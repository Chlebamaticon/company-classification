"""LLM prompt templates and JSON schema for FSC classification."""

from __future__ import annotations

SYSTEM_PROMPT = (
    "You are an expert at classifying defense and industrial suppliers using "
    "US Federal Supply Class (FSC) 4-digit codes. Pick only codes that appear "
    "in the provided catalog. Use NAICS codes, capabilities, products, and "
    "services as the strongest signals. Return strict JSON."
)

RESPONSE_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "codes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "4-digit FSC code"},
                    "title": {"type": "string"},
                    "rationale": {"type": "string"},
                    "confidence": {"type": "number"},
                },
                "required": ["code", "title", "rationale", "confidence"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["codes"],
    "additionalProperties": False,
}


def build_user_payload(
    *,
    company_name: str,
    website_url: str,
    email_domain: str | None,
    features: dict,
    fsc_catalog: list[dict],
) -> dict:
    return {
        "company": {
            "name": company_name,
            "website_url": website_url,
            "email_domain": email_domain or "",
        },
        "features": features,
        "fsc_catalog": fsc_catalog,
    }
