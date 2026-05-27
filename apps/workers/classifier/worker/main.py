"""Classification Worker: consume classify.requests, fan-out RPC, call LLM."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from pathlib import Path
from uuid import UUID

from aio_pika.abc import AbstractIncomingMessage

from salespatriot_shared.db import emit_event, get_engine
from salespatriot_shared.fsc import FSCCatalog
from salespatriot_shared.llm import chat_json
from salespatriot_shared.messages import (
    ClassifyRequest,
    CompanyFeatures,
    CrawlRequest,
    Envelope,
    IngestRequest,
    WorkerReply,
)
from salespatriot_shared.mq import (
    QUEUE_CLASSIFY,
    ROUTING_CRAWL,
    ROUTING_DOC_INGEST,
    RpcClient,
    connect,
    consume,
)

from .prompts import RESPONSE_SCHEMA, SYSTEM_PROMPT, build_user_payload

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("classifier")

FSC_CATALOG_PATH = os.environ.get("FSC_CATALOG_PATH", "/app/data/fsc_catalog.json")
MAX_FSC_CODES = 20

catalog: FSCCatalog


async def _rpc_ingest(rpc: RpcClient, envelope: Envelope[ClassifyRequest]) -> WorkerReply | None:
    sid = envelope.submission_id
    engine = get_engine()
    await emit_event(engine, sid, "progress", {"stage": "ingest", "status": "started"})
    try:
        ingest_env = Envelope[IngestRequest](
            submission_id=sid,
            trace_id=envelope.trace_id,
            payload=IngestRequest(
                file_path=f"/data/uploads/{sid}.pdf",
                filename=f"{sid}.pdf",
            ),
        )
        raw = await rpc.call(ROUTING_DOC_INGEST, ingest_env, timeout=120.0)
        reply = WorkerReply.model_validate(raw)
        if reply.ok:
            await emit_event(engine, sid, "progress", {"stage": "ingest", "status": "done"})
            await _persist_document(sid, reply)
        else:
            await emit_event(engine, sid, "progress", {"stage": "ingest", "status": "failed", "detail": reply.error})
        return reply
    except Exception as exc:
        log.exception("ingest RPC failed for %s", sid)
        await emit_event(engine, sid, "progress", {"stage": "ingest", "status": "failed", "detail": str(exc)})
        return None


async def _rpc_crawl(rpc: RpcClient, envelope: Envelope[ClassifyRequest]) -> WorkerReply | None:
    sid = envelope.submission_id
    engine = get_engine()
    await emit_event(engine, sid, "progress", {"stage": "crawl", "status": "started"})
    try:
        crawl_env = Envelope[CrawlRequest](
            submission_id=sid,
            trace_id=envelope.trace_id,
            payload=CrawlRequest(
                website_url=envelope.payload.website_url,
                email_domain=envelope.payload.email_domain,
            ),
        )
        raw = await rpc.call(ROUTING_CRAWL, crawl_env, timeout=120.0)
        reply = WorkerReply.model_validate(raw)
        if reply.ok:
            await emit_event(engine, sid, "progress", {"stage": "crawl", "status": "done"})
            await _persist_crawl(sid, reply)
        else:
            await emit_event(engine, sid, "progress", {"stage": "crawl", "status": "failed", "detail": reply.error})
        return reply
    except Exception as exc:
        log.exception("crawl RPC failed for %s", sid)
        await emit_event(engine, sid, "progress", {"stage": "crawl", "status": "failed", "detail": str(exc)})
        return None


async def _persist_document(sid: UUID, reply: WorkerReply) -> None:
    from sqlalchemy import text as sa_text
    engine = get_engine()
    result = reply.result or {}
    async with engine.begin() as conn:
        await conn.execute(
            sa_text(
                "INSERT INTO documents (submission_id, filename, raw_text, summary) "
                "VALUES (:sid, :fn, :rt, :sm)"
            ),
            {
                "sid": str(sid),
                "fn": f"{sid}.pdf",
                "rt": result.get("raw_text_excerpt", ""),
                "sm": json.dumps(result.get("summary", {})),
            },
        )


async def _persist_crawl(sid: UUID, reply: WorkerReply) -> None:
    from sqlalchemy import text as sa_text
    engine = get_engine()
    result = reply.result or {}
    async with engine.begin() as conn:
        await conn.execute(
            sa_text(
                "INSERT INTO crawls (submission_id, urls_visited, raw_text, summary) "
                "VALUES (:sid, :uv, :rt, :sm)"
            ),
            {
                "sid": str(sid),
                "uv": json.dumps(result.get("urls_visited", [])),
                "rt": result.get("raw_text_excerpt", ""),
                "sm": json.dumps(result.get("summary", {})),
            },
        )


def _merge_features(ingest_reply: WorkerReply | None, crawl_reply: WorkerReply | None) -> dict:
    merged = CompanyFeatures()
    for reply in (ingest_reply, crawl_reply):
        if not reply or not reply.ok or not reply.result:
            continue
        summary = reply.result.get("summary", {})
        features = CompanyFeatures.model_validate(summary)
        merged.capabilities.extend(features.capabilities)
        merged.products.extend(features.products)
        merged.services.extend(features.services)
        merged.naics_codes.extend(features.naics_codes)
        if features.free_text:
            merged.free_text = (merged.free_text + "\n" + features.free_text).strip()

    merged.capabilities = list(dict.fromkeys(merged.capabilities))
    merged.products = list(dict.fromkeys(merged.products))
    merged.services = list(dict.fromkeys(merged.services))
    merged.naics_codes = list(dict.fromkeys(merged.naics_codes))
    return merged.model_dump()


async def _classify(
    envelope: Envelope[ClassifyRequest],
    ingest_reply: WorkerReply | None,
    crawl_reply: WorkerReply | None,
) -> None:
    sid = envelope.submission_id
    engine = get_engine()
    await emit_event(engine, sid, "progress", {"stage": "classify", "status": "started"})

    features = _merge_features(ingest_reply, crawl_reply)
    fsc_list = [{"code": e.code, "title": e.title} for e in catalog.list_all()]

    user_payload = build_user_payload(
        company_name=envelope.payload.company_name,
        website_url=envelope.payload.website_url,
        email_domain=envelope.payload.email_domain,
        features=features,
        fsc_catalog=fsc_list,
    )

    llm_result = await chat_json(system=SYSTEM_PROMPT, user=user_payload, schema=RESPONSE_SCHEMA)

    codes = []
    for item in llm_result.get("codes", []):
        code = item.get("code", "")
        if not re.match(r"^\d{4}$", code):
            continue
        if code not in catalog:
            continue
        codes.append(item)

    codes.sort(key=lambda c: c.get("confidence", 0), reverse=True)
    codes = codes[:MAX_FSC_CODES]

    from sqlalchemy import text as sa_text
    async with engine.begin() as conn:
        await conn.execute(
            sa_text(
                "INSERT INTO classifications (submission_id, fsc_codes, model) "
                "VALUES (:sid, :codes, :model)"
            ),
            {"sid": str(sid), "codes": json.dumps(codes), "model": "gpt-4o-mini"},
        )
        await conn.execute(
            sa_text("UPDATE submissions SET status = 'done' WHERE id = :sid"),
            {"sid": str(sid)},
        )

    await emit_event(engine, sid, "progress", {"stage": "classify", "status": "done"})
    await emit_event(engine, sid, "result", {"fsc_codes": codes})
    log.info("classified %s -> %d codes", sid, len(codes))


async def _on_message(rpc: RpcClient, message: AbstractIncomingMessage) -> None:
    async with message.process():
        body = json.loads(message.body)
        envelope = Envelope[ClassifyRequest].model_validate(body)
        envelope = Envelope[ClassifyRequest](
            submission_id=envelope.submission_id,
            trace_id=envelope.trace_id,
            payload=ClassifyRequest.model_validate(body["payload"]),
        )
        sid = envelope.submission_id
        log.info("received classify request for %s", sid)

        try:
            tasks: list[asyncio.Task] = []
            task_labels: list[str] = []

            if envelope.payload.website_url:
                tasks.append(_rpc_crawl(rpc, envelope))
                task_labels.append("crawl")
            if envelope.payload.has_document:
                tasks.append(_rpc_ingest(rpc, envelope))
                task_labels.append("ingest")

            results = await asyncio.gather(*tasks, return_exceptions=True)

            crawl_reply: WorkerReply | None = None
            ingest_reply: WorkerReply | None = None
            for label, result in zip(task_labels, results):
                if isinstance(result, BaseException):
                    continue
                if label == "crawl":
                    crawl_reply = result
                elif label == "ingest":
                    ingest_reply = result

            await _classify(envelope, ingest_reply, crawl_reply)

        except Exception as exc:
            log.exception("classification failed for %s", sid)
            engine = get_engine()
            await emit_event(engine, sid, "error", {"message": str(exc)})
            from sqlalchemy import text as sa_text
            async with engine.begin() as conn:
                await conn.execute(
                    sa_text("UPDATE submissions SET status = 'error' WHERE id = :sid"),
                    {"sid": str(sid)},
                )


async def run() -> None:
    global catalog
    catalog = FSCCatalog.load(FSC_CATALOG_PATH)
    log.info("loaded FSC catalog: %d codes", len(catalog))

    async with connect() as conn:
        channel = await conn.channel()
        async with RpcClient(conn) as rpc:

            async def handler(msg: AbstractIncomingMessage) -> None:
                await _on_message(rpc, msg)

            await consume(channel, QUEUE_CLASSIFY, handler)
            log.info("classifier worker running, waiting for messages...")
            await asyncio.Future()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
