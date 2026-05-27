"""Link extraction, scoring, and same-domain filtering."""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

import tldextract
from bs4 import BeautifulSoup

SCORING_PATTERN = re.compile(
    r"(?i)(about|capabilit|product|service|part|catalog|equipment|industries|markets)"
)

MAX_LINKS = 7


def _registrable_domain(url: str) -> str:
    ext = tldextract.extract(url)
    return f"{ext.domain}.{ext.suffix}".lower()


def extract_links(html: str, base_url: str) -> list[dict[str, str]]:
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    base_domain = _registrable_domain(base_url)
    seen: set[str] = set()
    links: list[dict[str, str]] = []

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        absolute = urljoin(base_url + "/", href)

        parsed = urlparse(absolute)
        if parsed.scheme not in ("http", "https"):
            continue

        link_domain = _registrable_domain(absolute)
        if link_domain != base_domain:
            continue

        normalized = f"{parsed.scheme}://{parsed.netloc.lower()}{parsed.path.rstrip('/')}"
        if normalized in seen or normalized == base_url.rstrip("/"):
            continue

        seen.add(normalized)
        text = anchor.get_text(strip=True)
        links.append({"url": normalized, "text": text})

    return links


def score_link(url: str, anchor_text: str) -> int:
    score = 0
    path = urlparse(url).path
    if SCORING_PATTERN.search(path):
        score += 1
    if SCORING_PATTERN.search(anchor_text):
        score += 1
    return score


def select_top_links(links: list[dict[str, str]], homepage_url: str) -> list[str]:
    scored = [(score_link(l["url"], l["text"]), l["url"]) for l in links]
    scored.sort(key=lambda x: x[0], reverse=True)

    selected = [url for _, url in scored[:MAX_LINKS]]

    homepage = homepage_url.rstrip("/")
    if homepage not in selected:
        selected.insert(0, homepage)
    else:
        selected.remove(homepage)
        selected.insert(0, homepage)

    return selected[: MAX_LINKS + 1]
