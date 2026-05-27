"""Doc Ingest Worker: consumes doc_ingest.requests, extracts PDF text, summarizes via LLM."""

from __future__ import annotations

import asyncio
import json
import logging
from uuid import UUID

import aio_pika

from salespatriot_shared.llm import chat_json
from salespatriot_shared.messages import (
    Envelope,
    IngestRequest,
    WorkerReply,
)
from salespatriot_shared.mq import amqp_url, QUEUE_DOC_INGEST

from doc_ingest.extract import extract_text
from doc_ingest.prompts import SYSTEM_PROMPT, RESPONSE_SCHEMA

logger = logging.getLogger(__name__)

RAW_TEXT_EXCERPT_LIMIT = 2048


async def persist_document(
    submission_id: UUID,
    filename: str,
    raw_text: str,
    summary: dict,
) -> None:
    from salespatriot_shared.db import get_engine
    from sqlalchemy import text as sql_text

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.execute(
            sql_text(
                "INSERT INTO documents (submission_id, filename, raw_text, summary) "
                "VALUES (:sid, :fname, :raw, :summary)"
            ),
            {
                "sid": str(submission_id),
                "fname": filename,
                "raw": raw_text,
                "summary": json.dumps(summary),
            },
        )


async def handle_ingest(envelope: Envelope[IngestRequest]) -> WorkerReply:
    try:
        raw_text = extract_text(envelope.payload.file_path)

        summary = await chat_json(
            system=SYSTEM_PROMPT,
            user=raw_text,
            schema=RESPONSE_SCHEMA,
        )

        await persist_document(
            submission_id=envelope.submission_id,
            filename=envelope.payload.filename,
            raw_text=raw_text,
            summary=summary,
        )

        return WorkerReply(
            submission_id=envelope.submission_id,
            ok=True,
            result={
                "raw_text_excerpt": raw_text[:RAW_TEXT_EXCERPT_LIMIT],
                "summary": summary,
            },
        )
    except Exception as exc:
        logger.exception("Doc ingest failed for %s", envelope.submission_id)
        return WorkerReply(
            submission_id=envelope.submission_id,
            ok=False,
            error=str(exc),
        )


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logger.info("Starting doc_ingest worker...")

    for attempt in range(30):
        try:
            connection = await aio_pika.connect_robust(amqp_url())
            break
        except Exception:
            if attempt == 29:
                raise
            logger.info("RabbitMQ not ready, retrying in 2s...")
            await asyncio.sleep(2)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        async def on_message(message: aio_pika.abc.AbstractIncomingMessage) -> None:
            async with message.process():
                body = json.loads(message.body.decode())
                envelope = Envelope[IngestRequest](**body)
                reply = await handle_ingest(envelope)

                if message.reply_to:
                    await channel.default_exchange.publish(
                        aio_pika.Message(
                            body=reply.model_dump_json().encode(),
                            correlation_id=message.correlation_id,
                        ),
                        routing_key=message.reply_to,
                    )

        queue = await channel.declare_queue(QUEUE_DOC_INGEST, durable=True)
        await queue.consume(on_message)

        logger.info("Listening on %s", QUEUE_DOC_INGEST)
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
