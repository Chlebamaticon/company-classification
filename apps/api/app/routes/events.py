"""SSE endpoint: GET /submissions/{id}/events backed by Postgres LISTEN/NOTIFY."""

from __future__ import annotations

import asyncio
import json
import uuid

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from salespatriot_shared.db import database_url

router = APIRouter(tags=["events"])


def _raw_dsn() -> str:
    """Convert SQLAlchemy URL to plain asyncpg DSN."""
    url = database_url()
    return url.replace("postgresql+asyncpg://", "postgresql://")


async def _event_generator(request: Request, submission_id: uuid.UUID):
    import asyncpg  # local import — only SSE route needs raw asyncpg

    dsn = _raw_dsn()
    conn: asyncpg.Connection = await asyncpg.connect(dsn)
    channel = f"submission_events:{submission_id}"

    try:
        replay_rows = await conn.fetch(
            "SELECT id, kind, payload, created_at "
            "FROM submission_events WHERE submission_id = $1 ORDER BY id",
            submission_id,
        )
        for row in replay_rows:
            data = {
                "id": row["id"],
                "submission_id": str(submission_id),
                "kind": row["kind"],
                "payload": json.loads(row["payload"]) if isinstance(row["payload"], str) else row["payload"],
                "created_at": row["created_at"].isoformat(),
            }
            yield {"event": row["kind"], "data": json.dumps(data)}

        queue: asyncio.Queue[str] = asyncio.Queue()

        def _listener(conn, pid, channel, payload):  # noqa: ARG001
            queue.put_nowait(payload)

        await conn.add_listener(channel, _listener)

        while True:
            if await request.is_disconnected():
                break
            try:
                raw = await asyncio.wait_for(queue.get(), timeout=30.0)
                notification = json.loads(raw)
                yield {"event": notification.get("kind", "progress"), "data": raw}
            except asyncio.TimeoutError:
                yield {"event": "ping", "data": "{}"}
    finally:
        try:
            await conn.remove_listener(channel, _listener)
        except Exception:
            pass
        await conn.close()


@router.get("/submissions/{submission_id}/events")
async def submission_events(request: Request, submission_id: uuid.UUID):
    return EventSourceResponse(_event_generator(request, submission_id))
