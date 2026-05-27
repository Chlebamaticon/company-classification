"""LLM wrapper. Stub for the Classification Worker agent to flesh out.

Intended surface:

    from salespatriot_shared.llm import chat_json
    data = await chat_json(system="...", user={...}, schema={...})
"""

from __future__ import annotations

import os
from typing import Any


def model_name() -> str:
    return os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


async def chat_json(
    *,
    system: str,
    user: str | dict[str, Any],
    schema: dict[str, Any],
    model: str | None = None,
) -> dict[str, Any]:
    """Call the LLM in JSON mode and return the parsed object.

    Implemented by the Classification Worker agent.
    """
    raise NotImplementedError("classification worker agent to implement")
