"""Tests for the doc_ingest worker handler logic."""

import json
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

import pytest

from salespatriot_shared.messages import (
    CompanyFeatures,
    Envelope,
    IngestRequest,
    WorkerReply,
)


@pytest.fixture
def sample_envelope():
    return Envelope[IngestRequest](
        submission_id=uuid4(),
        trace_id=uuid4(),
        payload=IngestRequest(
            file_path="/data/uploads/test.pdf",
            filename="test.pdf",
        ),
    )


@pytest.fixture
def sample_features():
    return {
        "capabilities": ["CNC machining", "welding"],
        "products": ["steel brackets"],
        "services": ["precision cutting"],
        "naics_codes": ["332710"],
        "free_text": "A manufacturing company specializing in metal fabrication.",
    }


class TestHandleIngest:
    @pytest.mark.asyncio
    async def test_successful_extraction_and_reply(
        self, sample_envelope, sample_features, tmp_path
    ):
        from doc_ingest.worker import handle_ingest

        pdf_path = tmp_path / "test.pdf"
        from reportlab.pdfgen import canvas as pdf_canvas

        c = pdf_canvas.Canvas(str(pdf_path))
        c.drawString(72, 720, "CNC machining welding steel brackets")
        c.showPage()
        c.save()

        sample_envelope.payload.file_path = str(pdf_path)

        with (
            patch("doc_ingest.worker.chat_json", new_callable=AsyncMock) as mock_llm,
            patch("doc_ingest.worker.persist_document", new_callable=AsyncMock) as mock_db,
        ):
            mock_llm.return_value = sample_features

            reply = await handle_ingest(sample_envelope)

        assert reply.ok is True
        assert reply.error is None
        assert reply.result is not None
        assert "raw_text_excerpt" in reply.result
        assert "summary" in reply.result
        assert reply.result["summary"]["naics_codes"] == ["332710"]
        mock_db.assert_called_once()

    @pytest.mark.asyncio
    async def test_missing_file_returns_error(self, sample_envelope):
        from doc_ingest.worker import handle_ingest

        sample_envelope.payload.file_path = "/nonexistent/path.pdf"

        reply = await handle_ingest(sample_envelope)

        assert reply.ok is False
        assert reply.error is not None
        assert "not found" in reply.error.lower() or "No such file" in reply.error

    @pytest.mark.asyncio
    async def test_non_pdf_returns_error(self, sample_envelope, tmp_path):
        from doc_ingest.worker import handle_ingest

        txt_file = tmp_path / "test.txt"
        txt_file.write_text("not a pdf")
        sample_envelope.payload.file_path = str(txt_file)

        reply = await handle_ingest(sample_envelope)

        assert reply.ok is False
        assert "pdf" in reply.error.lower()

    @pytest.mark.asyncio
    async def test_llm_error_returns_error_reply(self, sample_envelope, tmp_path):
        from doc_ingest.worker import handle_ingest
        from reportlab.pdfgen import canvas as pdf_canvas

        pdf_path = tmp_path / "test.pdf"
        c = pdf_canvas.Canvas(str(pdf_path))
        c.drawString(72, 720, "Some content")
        c.showPage()
        c.save()
        sample_envelope.payload.file_path = str(pdf_path)

        with patch(
            "doc_ingest.worker.chat_json",
            new_callable=AsyncMock,
            side_effect=RuntimeError("LLM timeout"),
        ):
            reply = await handle_ingest(sample_envelope)

        assert reply.ok is False
        assert "LLM timeout" in reply.error

    @pytest.mark.asyncio
    async def test_raw_text_excerpt_limited_to_2k(
        self, sample_envelope, sample_features, tmp_path
    ):
        from doc_ingest.worker import handle_ingest
        from reportlab.pdfgen import canvas as pdf_canvas

        pdf_path = tmp_path / "test.pdf"
        c = pdf_canvas.Canvas(str(pdf_path))
        c.drawString(72, 720, "x" * 5000)
        c.showPage()
        c.save()
        sample_envelope.payload.file_path = str(pdf_path)

        with (
            patch("doc_ingest.worker.chat_json", new_callable=AsyncMock) as mock_llm,
            patch("doc_ingest.worker.persist_document", new_callable=AsyncMock),
        ):
            mock_llm.return_value = sample_features
            reply = await handle_ingest(sample_envelope)

        assert len(reply.result["raw_text_excerpt"]) <= 2048
