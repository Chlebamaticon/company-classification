"""Parallel page fetching with budget and HTML cleaning."""

from __future__ import annotations

import asyncio
import re
import time

import httpx
from bs4 import BeautifulSoup

from crawler.url import USER_AGENT

MAX_TEXT_CHARS = 50_000
DEFAULT_TIMEOUT = 10.0
DEFAULT_BUDGET = 30.0
DEFAULT_CONCURRENCY = 4

STRIP_TAGS = {"script", "style", "nav", "footer", "header", "noscript"}


def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all(STRIP_TAGS):
        tag.decompose()

    text = soup.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:MAX_TEXT_CHARS]


async def _fetch_one(
    client: httpx.AsyncClient, url: str, semaphore: asyncio.Semaphore
) -> tuple[str, str | None]:
    async with semaphore:
        try:
            resp = await client.get(url, headers={"User-Agent": USER_AGENT})
            if resp.status_code == 200:
                return url, resp.text
        except (httpx.HTTPError, Exception):
            pass
    return url, None


async def fetch_pages(
    urls: list[str],
    *,
    max_concurrent: int = DEFAULT_CONCURRENCY,
    budget_seconds: float = DEFAULT_BUDGET,
) -> dict[str, str]:
    semaphore = asyncio.Semaphore(max_concurrent)
    results: dict[str, str] = {}

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        tasks = [_fetch_one(client, url, semaphore) for url in urls]

        try:
            done = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=budget_seconds,
            )
        except asyncio.TimeoutError:
            done = []

        for item in done:
            if isinstance(item, tuple):
                url, html = item
                if html is not None:
                    results[url] = clean_html(html)

    return results
