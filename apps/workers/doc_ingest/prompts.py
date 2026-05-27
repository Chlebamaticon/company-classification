"""LLM prompts for the doc ingest worker."""

SYSTEM_PROMPT = (
    "Extract a concise capability profile from a supplier's document. "
    "Return strict JSON matching the provided schema. "
    "Use exact NAICS codes if present; otherwise leave the array empty. "
    "Do not invent products or services not implied by the text."
)

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "capabilities": {"type": "array", "items": {"type": "string"}},
        "products": {"type": "array", "items": {"type": "string"}},
        "services": {"type": "array", "items": {"type": "string"}},
        "naics_codes": {
            "type": "array",
            "items": {"type": "string", "pattern": r"^\d{6}$"},
        },
        "free_text": {"type": "string", "maxLength": 600},
    },
    "required": ["capabilities", "products", "services", "naics_codes", "free_text"],
    "additionalProperties": False,
}
