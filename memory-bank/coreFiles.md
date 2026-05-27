# Core Files

## packages/shared/salespatriot_shared/messages.py
**Description**: Pydantic contracts shared across API, Classification Worker, Doc Ingest, Crawl.
**Classes**:
- ProgressPayload, ResultPayload, FscCodeAssignment, CompanyFeatures: SSE / result payloads.
- IngestRequest, CrawlRequest, ClassifyRequest, IngestResult, CrawlResult: per-worker payloads.
- Envelope[PayloadT]: generic wrapper with submission_id, trace_id, payload.
- WorkerReply: standard reply across all RPC workers.
**Important Notes**:
- All models forbid extra fields. FscCodeAssignment.code is `^\d{4}$`.

## packages/shared/salespatriot_shared/fsc.py
**Description**: FSC catalog loader.
**Classes**:
- FSCEntry (dataclass): code + title.
- FSCCatalog: load(path), lookup(code), list_all(), __contains__.
**Important Notes**:
- Validates against the JSON produced by `scripts/parse_fsc_pdf.py`.

## packages/shared/salespatriot_shared/mq.py
**Description**: RabbitMQ helper stub. Constants for exchange/queue/routing names live here.
**Notable Methods**: connect(), RpcClient.call() — both NotImplemented; Classification Worker agent fills these in.

## packages/shared/salespatriot_shared/db.py
**Description**: Postgres async helper stub. Implementation pending.

## packages/shared/salespatriot_shared/llm.py
**Description**: LLM JSON-mode wrapper stub. Implementation pending.

## scripts/parse_fsc_pdf.py
**Description**: One-shot CLI that parses `AV_FSCClassAssignment._151007.pdf` into `data/fsc_catalog.json`.
**Notable Methods**:
- parse(text): line-anchored extraction; handles direct, code+ric-only (wrapped), and two-line wrap cases.
- normalize_title(): strips whitespace and footnote markers.
**Important Notes**: RIC/ACTY regex must allow digit-leading RICs (7FX/75, 2FY/75, 6FE/75). Produced 576 entries against the current PDF.

## infra/postgres/init.sql
**Description**: Schema + per-submission NOTIFY trigger for SSE.
**Important Notes**: Trigger emits on channel `submission_events:<submission_id>` so each SSE consumer LISTENs to only its own stream.
