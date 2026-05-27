"""Contract tests: message envelopes must round-trip cleanly."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from salespatriot_shared.messages import (
    ClassifyRequest,
    CompanyFeatures,
    CrawlRequest,
    CrawlResult,
    Envelope,
    FscCodeAssignment,
    IngestRequest,
    IngestResult,
    ResultPayload,
    WorkerReply,
)


def test_fsc_code_must_be_four_digits():
    with pytest.raises(ValidationError):
        FscCodeAssignment(code="34", title="x", rationale="x", confidence=0.5)
    with pytest.raises(ValidationError):
        FscCodeAssignment(code="abcd", title="x", rationale="x", confidence=0.5)
    ok = FscCodeAssignment(code="3408", title="Machining", rationale="match", confidence=0.9)
    assert ok.code == "3408"


def test_confidence_bounded():
    with pytest.raises(ValidationError):
        FscCodeAssignment(code="3408", title="x", rationale="x", confidence=1.5)


def test_envelope_round_trip_for_classify():
    env = Envelope[ClassifyRequest](
        submission_id=uuid4(),
        trace_id=uuid4(),
        payload=ClassifyRequest(
            company_name="ACME",
            website_url="https://acme.example",
            email_domain="acme.example",
            has_document=True,
        ),
    )
    blob = env.model_dump_json()
    reloaded = Envelope[ClassifyRequest].model_validate_json(blob)
    assert reloaded.payload.company_name == "ACME"


def test_envelope_round_trip_for_ingest_and_crawl():
    ingest = Envelope[IngestRequest](
        submission_id=uuid4(),
        trace_id=uuid4(),
        payload=IngestRequest(file_path="/data/uploads/x.pdf", filename="x.pdf"),
    )
    crawl = Envelope[CrawlRequest](
        submission_id=uuid4(),
        trace_id=uuid4(),
        payload=CrawlRequest(website_url="https://x.example", email_domain=None),
    )
    for env in (ingest, crawl):
        cls = type(env)
        assert cls.model_validate_json(env.model_dump_json()) == env


def test_worker_reply_result_shapes():
    features = CompanyFeatures(
        capabilities=["CNC Machining"],
        products=["Bushings"],
        services=["Fabrication"],
        naics_codes=["332710"],
        free_text="LSDP example",
    )
    ingest_result = IngestResult(raw_text_excerpt="...", summary=features)
    crawl_result = CrawlResult(urls_visited=["https://x"], raw_text_excerpt="...", summary=features)

    reply_ingest = WorkerReply(submission_id=uuid4(), ok=True, result=ingest_result.model_dump())
    reply_crawl = WorkerReply(submission_id=uuid4(), ok=True, result=crawl_result.model_dump())
    assert reply_ingest.result is not None and "summary" in reply_ingest.result
    assert reply_crawl.result is not None and "urls_visited" in reply_crawl.result


def test_result_payload_validates_fsc_codes():
    payload = ResultPayload(
        fsc_codes=[
            FscCodeAssignment(
                code="3408",
                title="Machining Centers and Way-Type Machine",
                rationale="CNC machining capability stated in capability statement.",
                confidence=0.92,
            )
        ]
    )
    assert payload.fsc_codes[0].code == "3408"
