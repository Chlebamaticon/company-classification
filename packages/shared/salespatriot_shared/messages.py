"""Pydantic contracts shared across API, Classification Worker, Doc Ingest, Crawl.

All RabbitMQ messages use the generic Envelope wrapper. Workers reply on the
`reply_to` queue with a WorkerReply carrying the original `correlation_id`.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Generic, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

PayloadT = TypeVar("PayloadT", bound=BaseModel)


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SubmissionEventKind(str, Enum):
    PROGRESS = "progress"
    RESULT = "result"
    ERROR = "error"


class ProgressPayload(_Model):
    stage: Literal["ingest", "crawl", "classify"]
    status: Literal["started", "done", "failed"]
    detail: str | None = None


class FscCodeAssignment(_Model):
    """One 4-digit FSC code assigned to a company with rationale and confidence."""

    code: str = Field(pattern=r"^\d{4}$")
    title: str
    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)


class ResultPayload(_Model):
    fsc_codes: list[FscCodeAssignment]


class CompanyFeatures(_Model):
    """Normalized output of doc ingest / crawl summarization."""

    capabilities: list[str] = Field(default_factory=list)
    products: list[str] = Field(default_factory=list)
    services: list[str] = Field(default_factory=list)
    naics_codes: list[str] = Field(default_factory=list)
    free_text: str = ""


# --- RabbitMQ message payloads --------------------------------------------------


class IngestRequest(_Model):
    file_path: str
    filename: str


class CrawlRequest(_Model):
    website_url: str | None = None
    email_domain: str | None = None


class ClassifyRequest(_Model):
    company_name: str
    website_url: str
    email_domain: str | None = None
    has_document: bool = False


class IngestResult(_Model):
    raw_text_excerpt: str
    summary: CompanyFeatures


class CrawlResult(_Model):
    urls_visited: list[str]
    raw_text_excerpt: str
    summary: CompanyFeatures


class Envelope(_Model, Generic[PayloadT]):
    """Wrapper for every request published to a worker queue."""

    submission_id: UUID
    trace_id: UUID
    payload: PayloadT


class WorkerReply(_Model):
    """Returned by each worker on the `reply_to` queue with matching correlation_id."""

    submission_id: UUID
    ok: bool
    error: str | None = None
    result: dict[str, Any] | None = None
