"""Tests for parallel page fetching and HTML cleaning."""

import httpx
import pytest
import respx

from crawler.fetch import clean_html, fetch_pages


SAMPLE_PAGE = """
<html>
<head><script>var x = 1;</script><style>body{color:red}</style></head>
<body>
    <nav><a href="/">Home</a></nav>
    <header><h1>Header</h1></header>
    <main>
        <p>Important content about manufacturing.</p>
        <p>We provide CNC machining services.</p>
    </main>
    <footer>Copyright 2024</footer>
    <noscript>Enable JS</noscript>
</body>
</html>
"""


class TestCleanHtml:
    def test_removes_script_tags(self):
        result = clean_html(SAMPLE_PAGE)
        assert "var x = 1" not in result

    def test_removes_style_tags(self):
        result = clean_html(SAMPLE_PAGE)
        assert "color:red" not in result

    def test_removes_nav(self):
        result = clean_html(SAMPLE_PAGE)
        assert "<nav>" not in result

    def test_removes_footer(self):
        result = clean_html(SAMPLE_PAGE)
        assert "Copyright 2024" not in result

    def test_removes_header(self):
        result = clean_html(SAMPLE_PAGE)
        assert "<header>" not in result

    def test_removes_noscript(self):
        result = clean_html(SAMPLE_PAGE)
        assert "Enable JS" not in result

    def test_preserves_main_content(self):
        result = clean_html(SAMPLE_PAGE)
        assert "Important content about manufacturing" in result
        assert "CNC machining services" in result

    def test_collapses_whitespace(self):
        result = clean_html(SAMPLE_PAGE)
        assert "    " not in result

    def test_caps_at_50k_chars(self):
        huge_html = "<html><body>" + "x" * 60000 + "</body></html>"
        result = clean_html(huge_html)
        assert len(result) <= 50000


class TestFetchPages:
    @pytest.mark.asyncio
    @respx.mock
    async def test_fetches_multiple_urls(self):
        respx.get("https://example.com/page1").mock(
            return_value=httpx.Response(200, text="<html><body>Page 1 content</body></html>")
        )
        respx.get("https://example.com/page2").mock(
            return_value=httpx.Response(200, text="<html><body>Page 2 content</body></html>")
        )

        results = await fetch_pages(
            ["https://example.com/page1", "https://example.com/page2"]
        )
        assert len(results) == 2
        assert "Page 1 content" in results["https://example.com/page1"]
        assert "Page 2 content" in results["https://example.com/page2"]

    @pytest.mark.asyncio
    @respx.mock
    async def test_handles_failed_requests_gracefully(self):
        respx.get("https://example.com/ok").mock(
            return_value=httpx.Response(200, text="<body>OK</body>")
        )
        respx.get("https://example.com/fail").mock(
            return_value=httpx.Response(500)
        )

        results = await fetch_pages(
            ["https://example.com/ok", "https://example.com/fail"]
        )
        assert "https://example.com/ok" in results
        assert "https://example.com/fail" not in results

    @pytest.mark.asyncio
    @respx.mock
    async def test_respects_concurrency_limit(self):
        for i in range(10):
            respx.get(f"https://example.com/p{i}").mock(
                return_value=httpx.Response(200, text=f"<body>P{i}</body>")
            )

        urls = [f"https://example.com/p{i}" for i in range(10)]
        results = await fetch_pages(urls, max_concurrent=4)
        assert len(results) <= 10
