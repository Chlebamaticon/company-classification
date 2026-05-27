---
name: Ingest And Crawl Plan
overview: "Two RabbitMQ-driven workers: Doc Ingest parses uploaded PDFs and Crawl fetches relevant website pages. Both produce a normalized CompanyFeatures summary returned via RPC to the Classification Worker."
todos:
  - id: ingest_scaffold
    content: Scaffold apps/workers/doc_ingest with pyproject.toml, worker.py entrypoint, prompts.py, Dockerfile.
    status: pending
  - id: ingest_extract
    content: Implement PDF text extraction with pdfplumber, normalization, 50k char cap.
    status: pending
  - id: ingest_llm
    content: Wire shared.llm.chat_json with CompanyFeatures schema; build doc-ingest prompt.
    status: pending
  - id: ingest_persist
    content: Persist documents row and reply via RabbitMQ correlation_id/reply_to.
    status: pending
  - id: ingest_tests
    content: Unit test against LSDP Capabilites Statement.pdf asserting NAICS extraction.
    status: pending
  - id: crawl_scaffold
    content: Scaffold apps/workers/crawler with pyproject.toml, worker.py, prompts.py, Dockerfile.
    status: pending
  - id: crawl_url
    content: Implement URL normalization (scheme default, email-domain fallback) and robots.txt enforcement.
    status: pending
  - id: crawl_links
    content: Fetch homepage; extract, score, dedupe in-domain links via tldextract; pick top 7 + homepage.
    status: pending
  - id: crawl_fetch
    content: Parallel fetch (concurrency 4, 30s budget) + HTML cleaning (drop script/style/nav/footer).
    status: pending
  - id: crawl_llm_persist
    content: Summarize via shared.llm.chat_json, persist crawls row, reply with urls_visited + summary.
    status: pending
  - id: crawl_tests
    content: Unit tests with respx covering link scoring and robots.txt disallow.
    status: pending
  - id: workers_readme
    content: Write apps/workers/README.md with worker-smoke runbook using rabbitmqadmin.
    status: pending
isProject: false
---

# Agent 3 of 3: Doc Ingest Worker + Crawl Worker

## Scope and ownership

Owns:

- `apps/workers/doc_ingest/`
- `apps/workers/crawler/`

Does not implement: API, SPA, Classification Worker, `packages/shared`, DB schema, docker-compose root. Consumes those as fixed contracts from the Classification Worker agent.

## Consumed contracts (read-only)

From `packages/shared`:

- `shared.messages.IngestRequest`, `CrawlRequest`, `WorkerReply`, `CompanyFeatures`
- `shared.mq.connect()`, `consume(queue, handler)`, `reply(envelope)` using `aio_pika` (correlation_id + reply_to)
- `shared.db` for persisting `documents` and `crawls` rows
- `shared.llm.chat_json(system, user, schema)` — OpenAI JSON-mode wrapper

RabbitMQ queues consumed:

- `doc_ingest.requests`, payload `{ "file_path": "/data/uploads/<uuid>.pdf", "filename": str }`
- `crawl.requests`, payload `{ "website_url": str, "email_domain": str|null }`

Reply envelope (sent back via `reply_to` with the original `correlation_id`):

```json
{
  "submission_id": "uuid",
  "ok": true,
  "error": null,
  "result": {
    "raw_text_excerpt": "first ~2k chars",
    "urls_visited": ["..."],
    "summary": {
      "capabilities": [str],
      "products": [str],
      "services": [str],
      "naics_codes": [str],
      "free_text": str
    }
  }
}
```

`urls_visited` only present in crawl replies. Each worker is responsible for inserting the corresponding `documents` / `crawls` row before replying.

## Doc Ingest Worker

Path: `apps/workers/doc_ingest/`

Responsibilities:

- Consume `doc_ingest.requests` with prefetch=1.
- Open `payload.file_path` from the shared `uploads` volume. Reject anything not PDF (MVP).
- Extract text with `pdfplumber.open(path)` page by page, concat with `\n\n`, normalize whitespace, cap at ~50k chars.
- Call `shared.llm.chat_json` with the prompt below to produce a `CompanyFeatures` summary.
- Persist `documents` row: `{submission_id, filename, raw_text, summary}`.
- Reply `WorkerReply(ok=True, result={raw_text_excerpt, summary})`.
- On any error (file missing, parse failure, LLM error), reply `ok=False, error=str(exc)` and still log; do not crash the worker process.

LLM prompt (in `apps/workers/doc_ingest/prompts.py`):

- System: "Extract a concise capability profile from a supplier's document. Return strict JSON matching the provided schema. Use exact NAICS codes if present; otherwise leave the array empty. Do not invent products or services not implied by the text."
- User: the extracted PDF text.
- Response schema: `{capabilities:[str], products:[str], services:[str], naics_codes:[str ^\d{6}$], free_text:str}` with `free_text` <= 600 chars.

## Crawl Worker

Path: `apps/workers/crawler/`

Responsibilities:

- Consume `crawl.requests` with prefetch=1.
- Resolve `website_url`; if missing scheme, prepend `https://`. If empty and `email_domain` provided, try `https://{email_domain}`.
- Fetch homepage with `httpx.AsyncClient` (HTTP/2 off for simplicity), 10 s timeout, browser-like User-Agent `SalesPatriot-Classifier/0.1 (+contact)`.
- Respect `robots.txt` via `urllib.robotparser`; skip disallowed paths.
- Parse links with BeautifulSoup, keep same-registrable-domain only (use `tldextract`), normalize, dedupe.
- Score links by path/anchor regex `(?i)(about|capabilit|product|service|part|catalog|equipment|industries|markets)` and pick top ~7 plus the homepage (cap 8 pages).
- Fetch in parallel with `asyncio.gather` (concurrency 4), total wall budget 30 s; whatever returns by the deadline is what we keep.
- Strip with BeautifulSoup: drop `script`, `style`, `nav`, `footer`, `header`, `noscript`; collapse whitespace; concat with section breaks; cap at ~50k chars.
- Call `shared.llm.chat_json` with the prompt below.
- Persist `crawls` row: `{submission_id, urls_visited, raw_text, summary}`.
- Reply with `urls_visited`, `raw_text_excerpt`, `summary`.
- Failure modes: DNS error / non-2xx homepage / total timeout → reply `ok=False, error=...`. Partial success (some pages 200, some failed) is still `ok=True` with whatever was collected.

LLM prompt (in `apps/workers/crawler/prompts.py`):

- System: same intent as Doc Ingest but framed for website text; "If the site sells products list them under products; if it offers services or capabilities list them under services/capabilities. Look for NAICS codes anywhere on the page."
- User: concatenated cleaned page text labeled by URL.
- Same response schema as Doc Ingest.

## Local dev and testing

- Each worker has `uv` or `pip` based `pyproject.toml` and a `Dockerfile` (`python:3.12-slim`, install deps, copy code, run `python -m worker`).
- `apps/workers/doc_ingest/tests/test_extract.py`: PDF fixture (`LSDP Capabilites Statement.pdf` from repo root) → assert NAICS `["332710","332721","332722","332510"]` extracted; assert `services` includes a CNC machining mention.
- `apps/workers/crawler/tests/test_crawl.py`: use `respx` to stub `https://example.com` homepage with seeded HTML; assert link selection ranks `/products` above `/contact`; assert `robots.txt` disallow respected.
- `tests/test_contract.py`: roundtrip Pydantic models from `shared.messages` to ensure reply shape is valid.

## Standalone smoke test (without the Classifier)

Provide a `make worker-smoke` target documented in `apps/workers/README.md`:

1. `docker compose up postgres rabbitmq doc_ingest crawler`.
2. Hand-publish a `doc_ingest.requested` envelope using `rabbitmqadmin` with a sample file path; observe reply on a temp queue.
3. Hand-publish a `crawl.requested` envelope for `https://loosco.com/`; observe reply.

## Tasks (atomic)

1. Doc Ingest: package scaffold (`pyproject.toml`, `worker.py`, `prompts.py`, `Dockerfile`).
2. Doc Ingest: PDF text extraction with `pdfplumber`, normalization, char cap.
3. Doc Ingest: LLM call via `shared.llm.chat_json`, schema-validated.
4. Doc Ingest: DB persistence (`documents` row) + reply on RPC queue with correlation_id.
5. Doc Ingest: error handling + unit test against `LSDP Capabilites Statement.pdf`.
6. Crawl: package scaffold (`pyproject.toml`, `worker.py`, `prompts.py`, `Dockerfile`).
7. Crawl: URL resolution (scheme + email-domain fallback) and `robots.txt` parsing.
8. Crawl: homepage fetch + link extraction + scoring + same-domain filter.
9. Crawl: parallel page fetch under 30 s budget + HTML cleaning.
10. Crawl: LLM summarization, DB persistence (`crawls` row), reply.
11. Crawl: unit tests with `respx` covering link ranking and robots.txt.
12. Worker README with the `worker-smoke` runbook.

## Done criteria

- Both worker processes start under `docker compose up doc_ingest crawler` and connect to RabbitMQ + Postgres.
- Hand-published requests produce schema-valid replies and matching DB rows.
- Doc Ingest extracts NAICS codes correctly from LSDP fixture.
- Crawl returns at least one in-domain page summary for `https://loosco.com/`.

## Out of scope

- OCR / scanned PDFs.
- JavaScript-rendered crawling (no Playwright/Selenium).
- Sitemap.xml traversal, depth > 1.
- Caching, rate limiting beyond per-host concurrency=4.

