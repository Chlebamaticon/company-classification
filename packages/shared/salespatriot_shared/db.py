"""Async Postgres helpers: engine singleton, emit_event, and raw-connection pool."""

from __future__ import annotations

import json
import logging
import os
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

log = logging.getLogger(__name__)

_engine: AsyncEngine | None = None


def database_url() -> str:
    user = os.environ.get("POSTGRES_USER", "salespatriot")
    password = os.environ.get("POSTGRES_PASSWORD", "salespatriot")
    host = os.environ.get("POSTGRES_HOST", "postgres")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ.get("POSTGRES_DB", "salespatriot")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(database_url(), pool_size=5, max_overflow=5)
    return _engine


async def dispose_engine() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None


async def emit_event(
    engine: AsyncEngine,
    submission_id: UUID,
    kind: str,
    payload: dict[str, Any],
) -> None:
    """Insert a row into submission_events. The DB trigger fires NOTIFY for SSE."""
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO submission_events (submission_id, kind, payload) "
                "VALUES (:sid, :kind, :payload)"
            ),
            {"sid": str(submission_id), "kind": kind, "payload": json.dumps(payload)},
        )
    log.info("emitted %s for %s", kind, submission_id)
