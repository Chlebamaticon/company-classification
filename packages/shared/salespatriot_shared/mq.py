"""RabbitMQ helpers: connect, publish, consume, and RPC client."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Callable, Coroutine

import aio_pika
from aio_pika import DeliveryMode, ExchangeType, Message
from aio_pika.abc import AbstractIncomingMessage

from .messages import Envelope

log = logging.getLogger(__name__)

EXCHANGE_NAME = "salespatriot"

QUEUE_CLASSIFY = "classify.requests"
QUEUE_DOC_INGEST = "doc_ingest.requests"
QUEUE_CRAWL = "crawl.requests"

ROUTING_CLASSIFY = "classify.requested"
ROUTING_DOC_INGEST = "doc_ingest.requested"
ROUTING_CRAWL = "crawl.requested"

_QUEUES = {
    ROUTING_CLASSIFY: QUEUE_CLASSIFY,
    ROUTING_DOC_INGEST: QUEUE_DOC_INGEST,
    ROUTING_CRAWL: QUEUE_CRAWL,
}


def amqp_url() -> str:
    user = os.environ.get("RABBITMQ_USER", "salespatriot")
    password = os.environ.get("RABBITMQ_PASSWORD", "salespatriot")
    host = os.environ.get("RABBITMQ_HOST", "rabbitmq")
    port = os.environ.get("RABBITMQ_PORT", "5672")
    return f"amqp://{user}:{password}@{host}:{port}/"


@asynccontextmanager
async def connect() -> AsyncIterator[aio_pika.abc.AbstractRobustConnection]:
    conn = await aio_pika.connect_robust(amqp_url())
    try:
        yield conn
    finally:
        await conn.close()


async def ensure_topology(channel: aio_pika.abc.AbstractChannel) -> aio_pika.abc.AbstractExchange:
    exchange = await channel.declare_exchange(
        EXCHANGE_NAME, ExchangeType.DIRECT, durable=True,
    )
    for routing_key, queue_name in _QUEUES.items():
        queue = await channel.declare_queue(queue_name, durable=True)
        await queue.bind(exchange, routing_key=routing_key)
    return exchange


async def publish(
    channel: aio_pika.abc.AbstractChannel,
    routing_key: str,
    envelope: Envelope[Any],
) -> None:
    exchange = await ensure_topology(channel)
    body = envelope.model_dump_json().encode()
    msg = Message(body, delivery_mode=DeliveryMode.PERSISTENT, content_type="application/json")
    await exchange.publish(msg, routing_key=routing_key)
    log.info("published %s for submission %s", routing_key, envelope.submission_id)


async def consume(
    channel: aio_pika.abc.AbstractChannel,
    queue_name: str,
    callback: Callable[[AbstractIncomingMessage], Coroutine[Any, Any, None]],
    *,
    prefetch: int = 1,
) -> None:
    await ensure_topology(channel)
    await channel.set_qos(prefetch_count=prefetch)
    queue = await channel.declare_queue(queue_name, durable=True)
    await queue.consume(callback)
    log.info("consuming %s", queue_name)


class RpcClient:
    """RPC over RabbitMQ using correlation_id + reply_to."""

    def __init__(self, connection: aio_pika.abc.AbstractConnection) -> None:
        self._connection = connection
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._callback_queue: aio_pika.abc.AbstractQueue | None = None
        self._futures: dict[str, asyncio.Future[bytes]] = {}

    async def __aenter__(self) -> RpcClient:
        self._channel = await self._connection.channel()
        await ensure_topology(self._channel)
        self._callback_queue = await self._channel.declare_queue("", exclusive=True)
        await self._callback_queue.consume(self._on_reply)
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self._channel and not self._channel.is_closed:
            await self._channel.close()

    async def _on_reply(self, message: AbstractIncomingMessage) -> None:
        async with message.process():
            cid = message.correlation_id
            if cid and cid in self._futures:
                self._futures[cid].set_result(message.body)

    async def call(
        self,
        routing_key: str,
        envelope: Envelope[Any],
        *,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        assert self._channel is not None and self._callback_queue is not None
        correlation_id = str(uuid.uuid4())
        future: asyncio.Future[bytes] = asyncio.get_event_loop().create_future()
        self._futures[correlation_id] = future

        exchange = await self._channel.get_exchange(EXCHANGE_NAME)
        body = envelope.model_dump_json().encode()
        msg = Message(
            body,
            delivery_mode=DeliveryMode.PERSISTENT,
            content_type="application/json",
            correlation_id=correlation_id,
            reply_to=self._callback_queue.name,
        )
        await exchange.publish(msg, routing_key=routing_key)

        try:
            raw = await asyncio.wait_for(future, timeout=timeout)
            return json.loads(raw)
        finally:
            self._futures.pop(correlation_id, None)
