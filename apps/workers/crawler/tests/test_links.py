"""Tests for link extraction, scoring, and same-domain filtering."""

import pytest

from crawler.links import extract_links, score_link, select_top_links


SAMPLE_HTML = """
<html>
<body>
    <a href="/about">About Us</a>
    <a href="/products">Our Products</a>
    <a href="/services">Services</a>
    <a href="/contact">Contact</a>
    <a href="/capabilities">Capabilities</a>
    <a href="/blog/post-1">Blog Post</a>
    <a href="https://external.com/link">External</a>
    <a href="/catalog">Parts Catalog</a>
    <a href="/industries">Industries Served</a>
    <a href="/careers">Careers</a>
    <a href="/privacy">Privacy Policy</a>
</body>
</html>
"""


class TestExtractLinks:
    def test_extracts_relative_links(self):
        links = extract_links(SAMPLE_HTML, "https://example.com")
        urls = [l["url"] for l in links]
        assert "https://example.com/about" in urls
        assert "https://example.com/products" in urls

    def test_filters_external_links(self):
        links = extract_links(SAMPLE_HTML, "https://example.com")
        urls = [l["url"] for l in links]
        assert "https://external.com/link" not in urls

    def test_deduplicates_links(self):
        html = """
        <a href="/about">About</a>
        <a href="/about">About Us</a>
        <a href="/about/">About Page</a>
        """
        links = extract_links(html, "https://example.com")
        urls = [l["url"] for l in links]
        assert urls.count("https://example.com/about") == 1

    def test_handles_empty_html(self):
        links = extract_links("", "https://example.com")
        assert links == []


class TestScoreLink:
    def test_about_scores_high(self):
        score = score_link("https://example.com/about", "About Us")
        assert score > 0

    def test_products_scores_high(self):
        score = score_link("https://example.com/products", "Products")
        assert score > 0

    def test_capabilities_scores_high(self):
        score = score_link("https://example.com/capabilities", "Capabilities")
        assert score > 0

    def test_contact_scores_zero(self):
        score = score_link("https://example.com/contact", "Contact")
        assert score == 0

    def test_privacy_scores_zero(self):
        score = score_link("https://example.com/privacy", "Privacy Policy")
        assert score == 0

    def test_products_ranks_above_contact(self):
        prod_score = score_link("https://example.com/products", "Products")
        contact_score = score_link("https://example.com/contact", "Contact")
        assert prod_score > contact_score


class TestSelectTopLinks:
    def test_returns_max_7_plus_homepage(self):
        links = [
            {"url": f"https://example.com/page{i}", "text": f"Page {i}"}
            for i in range(20)
        ]
        result = select_top_links(links, "https://example.com")
        assert len(result) <= 8

    def test_homepage_always_included(self):
        links = [
            {"url": "https://example.com/about", "text": "About"},
            {"url": "https://example.com/products", "text": "Products"},
        ]
        result = select_top_links(links, "https://example.com")
        assert "https://example.com" in result

    def test_high_scoring_links_selected(self):
        links = extract_links(SAMPLE_HTML, "https://example.com")
        result = select_top_links(links, "https://example.com")
        assert "https://example.com/products" in result
        assert "https://example.com/capabilities" in result

    def test_low_scoring_links_excluded_when_overflow(self):
        links = extract_links(SAMPLE_HTML, "https://example.com")
        result = select_top_links(links, "https://example.com")
        if len(links) > 7:
            assert "https://example.com/privacy" not in result
