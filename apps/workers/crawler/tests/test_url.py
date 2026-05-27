"""Tests for URL normalization and robots.txt enforcement."""

import httpx
import pytest
import respx

from crawler.url import normalize_url, resolve_start_url, is_allowed_by_robots


class TestNormalizeUrl:
    def test_adds_https_if_no_scheme(self):
        assert normalize_url("example.com") == "https://example.com"

    def test_preserves_existing_https(self):
        assert normalize_url("https://example.com") == "https://example.com"

    def test_preserves_existing_http(self):
        assert normalize_url("http://example.com") == "http://example.com"

    def test_strips_trailing_slash(self):
        assert normalize_url("https://example.com/") == "https://example.com"

    def test_strips_fragment(self):
        assert normalize_url("https://example.com/page#section") == "https://example.com/page"

    def test_lowercases_domain(self):
        assert normalize_url("https://EXAMPLE.COM/Path") == "https://example.com/Path"


class TestResolveStartUrl:
    def test_uses_website_url_when_provided(self):
        result = resolve_start_url("https://example.com", None)
        assert result == "https://example.com"

    def test_falls_back_to_email_domain(self):
        result = resolve_start_url(None, "info@example.com")
        assert result == "https://example.com"

    def test_falls_back_to_raw_email_domain(self):
        result = resolve_start_url(None, "example.com")
        assert result == "https://example.com"

    def test_empty_url_uses_email_domain(self):
        result = resolve_start_url("", "test.org")
        assert result == "https://test.org"

    def test_raises_when_both_empty(self):
        with pytest.raises(ValueError):
            resolve_start_url(None, None)

    def test_raises_when_both_blank(self):
        with pytest.raises(ValueError):
            resolve_start_url("", "")


class TestRobotsTxt:
    @pytest.mark.asyncio
    @respx.mock
    async def test_allows_when_no_robots(self):
        respx.get("https://example.com/robots.txt").mock(
            return_value=httpx.Response(404)
        )
        result = await is_allowed_by_robots("https://example.com/about")
        assert result is True

    @pytest.mark.asyncio
    @respx.mock
    async def test_disallows_blocked_path(self):
        robots_content = "User-agent: *\nDisallow: /private/"
        respx.get("https://example.com/robots.txt").mock(
            return_value=httpx.Response(200, text=robots_content)
        )
        result = await is_allowed_by_robots("https://example.com/private/secret")
        assert result is False

    @pytest.mark.asyncio
    @respx.mock
    async def test_allows_non_blocked_path(self):
        robots_content = "User-agent: *\nDisallow: /private/"
        respx.get("https://example.com/robots.txt").mock(
            return_value=httpx.Response(200, text=robots_content)
        )
        result = await is_allowed_by_robots("https://example.com/about")
        assert result is True
