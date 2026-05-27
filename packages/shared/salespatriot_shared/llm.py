"""LLM wrapper: structured JSON output via OpenAI API."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from openai import AsyncOpenAI

log = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def model_name() -> str:
    return os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI()
    return _client


async def chat_json(
    *,
    system: str,
    user: str | dict[str, Any],
    schema: dict[str, Any],
    model: str | None = None,
) -> dict[str, Any]:
    """Call the LLM with JSON-schema response_format and return the parsed dict."""
    client = _get_client()
    user_content = user if isinstance(user, str) else json.dumps(user)

    response = await client.chat.completions.create(
        model=model or model_name(),
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "response", "strict": True, "schema": schema},
        },
        temperature=0.2,
    )

    raw = response.choices[0].message.content
    assert raw is not None, "LLM returned empty content"
    result = json.loads(raw)
    log.info("LLM responded with %d chars", len(raw))
    return result
