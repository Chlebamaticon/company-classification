"""LLM prompts for the crawler worker."""

SYSTEM_PROMPT = (
    "Extract a concise capability profile from a company's website pages. "
    "If the site sells products list them under products; if it offers services "
    "or capabilities list them under services/capabilities. "
    "Look for NAICS codes anywhere on the page. "
    "Return strict JSON matching the provided schema. "
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
