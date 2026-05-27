"""URL normalization and robots.txt enforcement."""

from __future__ import annotations

from urllib.parse import urlparse, urlunparse
from urllib.robotparser import RobotFileParser

import httpx

USER_AGENT = "SalesPatriot-Classifier/0.1 (+contact)"


def normalize_url(url: str) -> str:
    if not url:
        return url
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/") if parsed.path != "/" else ""
    normalized = urlunparse((parsed.scheme, netloc, path, "", parsed.query, ""))
    return normalized


def resolve_start_url(website_url: str | None, email_domain: str | None) -> str:
    if website_url and website_url.strip():
        return normalize_url(website_url.strip())

    if email_domain and email_domain.strip():
        domain = email_domain.strip()
        if "@" in domain:
            domain = domain.split("@", 1)[1]
        return normalize_url(domain)

    raise ValueError("No website_url or email_domain provided")


async def is_allowed_by_robots(url: str) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(robots_url, headers={"User-Agent": USER_AGENT})
            if resp.status_code != 200:
                return True

            rp = RobotFileParser()
            rp.parse(resp.text.splitlines())
            return rp.can_fetch(USER_AGENT, url)
    except (httpx.HTTPError, Exception):
        return True
