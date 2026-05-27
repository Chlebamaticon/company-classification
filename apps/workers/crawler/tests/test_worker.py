"""Tests for the crawl worker handler logic."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import httpx
import pytest
import respx

from salespatriot_shared.messages import (
    CrawlRequest,
    Envelope,
)


@pytest.fixture
def sample_envelope():
    return Envelope[CrawlRequest](
        submission_id=uuid4(),
        trace_id=uuid4(),
        payload=CrawlRequest(
            website_url="https://example.com",
            email_domain="example.com",
        ),
    )


@pytest.fixture
def sample_features():
    return {
        "capabilities": ["welding", "fabrication"],
        "products": ["steel beams"],
        "services": ["custom manufacturing"],
        "naics_codes": ["332710"],
        "free_text": "Industrial manufacturing company.",
    }


class TestHandleCrawl:
    @pytest.mark.asyncio
    @respx.mock
    async def test_successful_crawl_returns_ok(self, sample_envelope, sample_features):
        from crawler.worker import handle_crawl

        respx.get("https://example.com/robots.txt").mock(
            return_value=httpx.Response(404)
        )
        respx.get("https://example.com").mock(
            return_value=httpx.Response(
                200,
                text='<html><body><a href="/about">About</a><p>Content</p></body></html>',
            )
        )
        respx.get("https://example.com/about").mock(
            return_value=httpx.Response(
                200, text="<html><body><p>About page content</p></body></html>"
            )
        )

        with (
            patch("crawler.worker.chat_json", new_callable=AsyncMock) as mock_llm,
            patch("crawler.worker.persist_crawl", new_callable=AsyncMock),
        ):
            mock_llm.return_value = sample_features
            reply = await handle_crawl(sample_envelope)

        assert reply.ok is True
        assert reply.result is not None
        assert "urls_visited" in reply.result
        assert "summary" in reply.result
        assert len(reply.result["urls_visited"]) >= 1

    @pytest.mark.asyncio
    async def test_no_url_no_domain_returns_error(self):
        from crawler.worker import handle_crawl

        envelope = Envelope[CrawlRequest](
            submission_id=uuid4(),
            trace_id=uuid4(),
            payload=CrawlRequest(website_url=None, email_domain=None),
        )
        reply = await handle_crawl(envelope)
        assert reply.ok is False
        assert reply.error is not None

    @pytest.mark.asyncio
    @respx.mock
    async def test_dns_failure_returns_error(self, sample_envelope):
        from crawler.worker import handle_crawl

        respx.get("https://example.com/robots.txt").mock(
            side_effect=httpx.ConnectError("DNS resolution failed")
        )
        respx.get("https://example.com").mock(
            side_effect=httpx.ConnectError("DNS resolution failed")
        )

        reply = await handle_crawl(sample_envelope)
        assert reply.ok is False

    @pytest.mark.asyncio
    @respx.mock
    async def test_partial_success_still_ok(self, sample_envelope, sample_features):
        from crawler.worker import handle_crawl

        respx.get("https://example.com/robots.txt").mock(
            return_value=httpx.Response(404)
        )
        respx.get("https://example.com").mock(
            return_value=httpx.Response(
                200,
                text='<html><body><a href="/ok">OK</a><a href="/fail">Fail</a><p>Home</p></body></html>',
            )
        )
        respx.get("https://example.com/ok").mock(
            return_value=httpx.Response(
                200, text="<html><body><p>Working page</p></body></html>"
            )
        )
        respx.get("https://example.com/fail").mock(
            return_value=httpx.Response(500)
        )

        with (
            patch("crawler.worker.chat_json", new_callable=AsyncMock) as mock_llm,
            patch("crawler.worker.persist_crawl", new_callable=AsyncMock),
        ):
            mock_llm.return_value = sample_features
            reply = await handle_crawl(sample_envelope)

        assert reply.ok is True

    @pytest.mark.asyncio
    @respx.mock
    async def test_uses_email_domain_fallback(self, sample_features):
        from crawler.worker import handle_crawl

        envelope = Envelope[CrawlRequest](
            submission_id=uuid4(),
            trace_id=uuid4(),
            payload=CrawlRequest(website_url="", email_domain="fallback.com"),
        )

        respx.get("https://fallback.com/robots.txt").mock(
            return_value=httpx.Response(404)
        )
        respx.get("https://fallback.com").mock(
            return_value=httpx.Response(
                200, text="<html><body><p>Fallback content</p></body></html>"
            )
        )

        with (
            patch("crawler.worker.chat_json", new_callable=AsyncMock) as mock_llm,
            patch("crawler.worker.persist_crawl", new_callable=AsyncMock),
        ):
            mock_llm.return_value = sample_features
            reply = await handle_crawl(envelope)

        assert reply.ok is True
        assert "https://fallback.com" in reply.result["urls_visited"]
