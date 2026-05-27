"""Crawl Worker: consumes crawl.requests, fetches website pages, summarizes via LLM."""

from __future__ import annotations

import asyncio
import json
import logging
from uuid import UUID

import aio_pika
import httpx

from salespatriot_shared.llm import chat_json
from salespatriot_shared.messages import (
    CrawlRequest,
    Envelope,
    WorkerReply,
)
from salespatriot_shared.mq import amqp_url, QUEUE_CRAWL

from crawler.fetch import clean_html, fetch_pages
from crawler.links import extract_links, select_top_links
from crawler.prompts import SYSTEM_PROMPT, RESPONSE_SCHEMA
from crawler.url import is_allowed_by_robots, resolve_start_url, USER_AGENT

logger = logging.getLogger(__name__)

RAW_TEXT_EXCERPT_LIMIT = 2048


async def persist_crawl(
    submission_id: UUID,
    urls_visited: list[str],
    raw_text: str,
    summary: dict,
) -> None:
    from salespatriot_shared.db import get_engine
    from sqlalchemy import text as sql_text

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.execute(
            sql_text(
                "INSERT INTO crawls (submission_id, urls_visited, raw_text, summary) "
                "VALUES (:sid, :urls, :raw, :summary)"
            ),
            {
                "sid": str(submission_id),
                "urls": json.dumps(urls_visited),
                "raw": raw_text,
                "summary": json.dumps(summary),
            },
        )


async def handle_crawl(envelope: Envelope[CrawlRequest]) -> WorkerReply:
    try:
        start_url = resolve_start_url(
            envelope.payload.website_url,
            envelope.payload.email_domain,
        )
    except ValueError as exc:
        return WorkerReply(
            submission_id=envelope.submission_id,
            ok=False,
            error=str(exc),
        )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                homepage_resp = await client.get(
                    start_url, headers={"User-Agent": USER_AGENT}
                )
                if homepage_resp.status_code != 200:
                    return WorkerReply(
                        submission_id=envelope.submission_id,
                        ok=False,
                        error=f"Homepage returned {homepage_resp.status_code}",
                    )
                homepage_html = homepage_resp.text
            except (httpx.HTTPError, Exception) as exc:
                return WorkerReply(
                    submission_id=envelope.submission_id,
                    ok=False,
                    error=f"Failed to fetch homepage: {exc}",
                )

        links = extract_links(homepage_html, start_url)
        selected_urls = select_top_links(links, start_url)

        allowed_urls: list[str] = []
        for url in selected_urls:
            if await is_allowed_by_robots(url):
                allowed_urls.append(url)

        page_texts = await fetch_pages(allowed_urls)

        if not page_texts:
            homepage_clean = clean_html(homepage_html)
            if homepage_clean:
                page_texts[start_url] = homepage_clean

        if not page_texts:
            return WorkerReply(
                submission_id=envelope.submission_id,
                ok=False,
                error="No page content could be retrieved",
            )

        combined_text = "\n\n---\n\n".join(
            f"[{url}]\n{text}" for url, text in page_texts.items()
        )

        summary = await chat_json(
            system=SYSTEM_PROMPT,
            user=combined_text,
            schema=RESPONSE_SCHEMA,
        )

        urls_visited = list(page_texts.keys())

        await persist_crawl(
            submission_id=envelope.submission_id,
            urls_visited=urls_visited,
            raw_text=combined_text,
            summary=summary,
        )

        return WorkerReply(
            submission_id=envelope.submission_id,
            ok=True,
            result={
                "urls_visited": urls_visited,
                "raw_text_excerpt": combined_text[:RAW_TEXT_EXCERPT_LIMIT],
                "summary": summary,
            },
        )
    except Exception as exc:
        logger.exception("Crawl failed for %s", envelope.submission_id)
        return WorkerReply(
            submission_id=envelope.submission_id,
            ok=False,
            error=str(exc),
        )


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logger.info("Starting crawler worker...")

    connection = await aio_pika.connect_robust(amqp_url())
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        async def on_message(message: aio_pika.abc.AbstractIncomingMessage) -> None:
            async with message.process():
                body = json.loads(message.body.decode())
                envelope = Envelope[CrawlRequest](**body)
                reply = await handle_crawl(envelope)

                if message.reply_to:
                    await channel.default_exchange.publish(
                        aio_pika.Message(
                            body=reply.model_dump_json().encode(),
                            correlation_id=message.correlation_id,
                        ),
                        routing_key=message.reply_to,
                    )

        queue = await channel.declare_queue(QUEUE_CRAWL, durable=True)
        await queue.consume(on_message)

        logger.info("Listening on %s", QUEUE_CRAWL)
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
