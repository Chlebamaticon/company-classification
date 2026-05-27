"""Tests for PDF text extraction and normalization."""

import pytest

from doc_ingest.extract import extract_text, normalize_text, MAX_CHARS


class TestNormalizeText:
    def test_collapses_multiple_spaces(self):
        assert normalize_text("hello   world") == "hello world"

    def test_collapses_multiple_newlines(self):
        result = normalize_text("hello\n\n\n\nworld")
        assert result == "hello\n\nworld"

    def test_strips_leading_trailing_whitespace(self):
        assert normalize_text("  hello  ") == "hello"

    def test_caps_at_max_chars(self):
        long_text = "a" * (MAX_CHARS + 1000)
        result = normalize_text(long_text)
        assert len(result) <= MAX_CHARS

    def test_empty_string(self):
        assert normalize_text("") == ""


class TestExtractText:
    def test_raises_on_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            extract_text(str(tmp_path / "nonexistent.pdf"))

    def test_raises_on_non_pdf(self, tmp_path):
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("hello")
        with pytest.raises(ValueError, match="not.*PDF"):
            extract_text(str(txt_file))

    def test_extracts_text_from_pdf(self, tmp_path):
        """Integration test: requires a real PDF fixture."""
        import pdfplumber
        from reportlab.pdfgen import canvas as pdf_canvas

        pdf_path = tmp_path / "test.pdf"
        c = pdf_canvas.Canvas(str(pdf_path))
        c.drawString(72, 720, "Hello World CNC Machining")
        c.showPage()
        c.save()

        result = extract_text(str(pdf_path))
        assert "Hello World" in result
        assert "CNC Machining" in result

    def test_multipage_extraction(self, tmp_path):
        from reportlab.pdfgen import canvas as pdf_canvas

        pdf_path = tmp_path / "multi.pdf"
        c = pdf_canvas.Canvas(str(pdf_path))
        c.drawString(72, 720, "Page One Content")
        c.showPage()
        c.drawString(72, 720, "Page Two Content")
        c.showPage()
        c.save()

        result = extract_text(str(pdf_path))
        assert "Page One Content" in result
        assert "Page Two Content" in result

    def test_output_is_normalized(self, tmp_path):
        from reportlab.pdfgen import canvas as pdf_canvas

        pdf_path = tmp_path / "norm.pdf"
        c = pdf_canvas.Canvas(str(pdf_path))
        c.drawString(72, 720, "   Spaces   everywhere   ")
        c.showPage()
        c.save()

        result = extract_text(str(pdf_path))
        assert "   " not in result
