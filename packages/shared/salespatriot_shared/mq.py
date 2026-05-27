"""RabbitMQ helpers. Stub for the Classification Worker agent to flesh out.

Intended surface:

    from salespatriot_shared.mq import connect, RpcClient

    async with connect() as conn:
        ...
        async with RpcClient(conn) as rpc:
            reply = await rpc.call(routing_key, envelope, timeout=30)
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

EXCHANGE_NAME = "salespatriot"

QUEUE_CLASSIFY = "classify.requests"
QUEUE_DOC_INGEST = "doc_ingest.requests"
QUEUE_CRAWL = "crawl.requests"

ROUTING_CLASSIFY = "classify.requested"
ROUTING_DOC_INGEST = "doc_ingest.requested"
ROUTING_CRAWL = "crawl.requested"


def amqp_url() -> str:
    user = os.environ.get("RABBITMQ_USER", "salespatriot")
    password = os.environ.get("RABBITMQ_PASSWORD", "salespatriot")
    host = os.environ.get("RABBITMQ_HOST", "rabbitmq")
    port = os.environ.get("RABBITMQ_PORT", "5672")
    return f"amqp://{user}:{password}@{host}:{port}/"


@asynccontextmanager
async def connect() -> AsyncIterator[object]:
    """Open an aio_pika connection. Implemented by the Classification Worker agent."""
    raise NotImplementedError("classification worker agent to implement")
    yield  # pragma: no cover


class RpcClient:
    """RPC over RabbitMQ using correlation_id + reply_to.

    Implemented by the Classification Worker agent.
    """

    def __init__(self, connection: object) -> None:
        self._connection = connection

    async def __aenter__(self) -> "RpcClient":
        raise NotImplementedError("classification worker agent to implement")

    async def __aexit__(self, exc_type, exc, tb) -> None:
        raise NotImplementedError("classification worker agent to implement")

    async def call(
        self,
        routing_key: str,
        envelope: object,
        *,
        timeout: float = 30.0,
    ) -> object:
        raise NotImplementedError("classification worker agent to implement")
