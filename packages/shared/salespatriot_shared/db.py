"""Async Postgres helpers. Stub for the Classification Worker agent to flesh out.

Intended surface:

    from salespatriot_shared.db import get_engine, emit_event

    engine = get_engine()
    await emit_event(engine, submission_id, "progress", {"stage": "crawl", "status": "started"})
"""

from __future__ import annotations

import os
from typing import Any
from uuid import UUID


def database_url() -> str:
    user = os.environ.get("POSTGRES_USER", "salespatriot")
    password = os.environ.get("POSTGRES_PASSWORD", "salespatriot")
    host = os.environ.get("POSTGRES_HOST", "postgres")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ.get("POSTGRES_DB", "salespatriot")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


def get_engine() -> Any:
    """Return a process-wide async engine. Implemented by Classification Worker agent."""
    raise NotImplementedError("classification worker agent to implement")


async def emit_event(
    engine: Any,
    submission_id: UUID,
    kind: str,
    payload: dict[str, Any],
) -> None:
    """Insert a row into submission_events. Trigger fires NOTIFY for SSE."""
    raise NotImplementedError("classification worker agent to implement")
