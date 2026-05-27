---
name: Classification Worker Plan
overview: "Owns the backbone: FastAPI service, Classification Worker, shared MQ/DB package, Postgres schema, docker-compose orchestration, FSC catalog parsing, and the contracts the other two agents consume."
todos:
  - id: scaffold_root
    content: "Create monorepo scaffolding: docker-compose.yml, .env.example, root README.md, Makefile with up/parse-fsc/logs targets."
    status: pending
  - id: fsc_parser
    content: Write scripts/parse_fsc_pdf.py, run it against AV_FSCClassAssignment._151007.pdf, commit data/fsc_catalog.json.
    status: pending
  - id: shared_pkg
    content: "Build packages/shared: messages.py (Pydantic envelopes), mq.py (aio_pika connect/publish/RpcClient), db.py (async SQLAlchemy + emit_event), fsc.py (FSCCatalog), llm.py (chat_json wrapper)."
    status: pending
  - id: db_init
    content: Write init.sql with submissions, documents, crawls, classifications, submission_events tables and per-submission NOTIFY trigger.
    status: pending
  - id: api_skeleton
    content: FastAPI app with lifespan opening DB and MQ pools and a /health route.
    status: pending
  - id: api_submissions
    content: Implement POST /submissions (multipart, file save) and GET /submissions/{id}.
    status: pending
  - id: api_sse
    content: Implement GET /submissions/{id}/events SSE backed by Postgres LISTEN/NOTIFY with initial replay.
    status: pending
  - id: classifier_bootstrap
    content: "Classification Worker process: consume classify.requests, ack/nack semantics, connect DB + MQ."
    status: pending
  - id: classifier_rpc
    content: RPC fan-out to doc_ingest + crawl, persist replies to documents and crawls tables, emit progress events.
    status: pending
  - id: classifier_llm
    content: Merge features, build prompt with FSC catalog, call LLM chat_json, validate codes against catalog, persist classifications, emit result event.
    status: pending
  - id: docker_backend
    content: Add Dockerfiles for api and classifier; wire all services into docker-compose with uploads volume.
    status: pending
  - id: e2e_smoke
    content: "Manual e2e: docker compose up, curl POST /submissions, hand-publish stub replies to doc_ingest.requests and crawl.requests, observe SSE result event with valid FSC codes."
    status: pending
isProject: false
---



# Agent 2 of 3: Classification Worker + API + Scaffolding

## Scope and ownership

Owns:

- `docker-compose.yml`, `.env.example`, root `README.md`
- `apps/api/` — FastAPI service
- `apps/workers/classifier/` — Classification Worker
- `packages/shared/` — Pydantic message schemas, RabbitMQ helpers, DB models, FSC catalog loader
- `scripts/parse_fsc_pdf.py` and `data/fsc_catalog.json`
- Postgres init / migrations
- Placeholders in compose for `web`, `doc_ingest`, `crawler` services (image build paths only; other agents fill them in)

Does not implement: React SPA, Doc Ingest Worker, Crawl Worker logic.

## Produced contracts (other agents consume these verbatim)

### HTTP / SSE (for SPA)

- `POST /submissions` multipart: `company_name`, `website_url`, `email_domain?`, `file?` → 202 `{submission_id, status:"queued"}`
- `GET /submissions/{id}` → `{submission_id, status, fsc_codes|null}`
- `GET /submissions/{id}/events` SSE with event types `progress`, `result`, `error` (payloads as defined in SPA plan)

### RabbitMQ messages (for Doc Ingest + Crawl workers)

Exchange: `salespatriot` (direct). Queues and routing keys:

- `doc_ingest.requests` <- key `doc_ingest.requested`
- `crawl.requests` <- key `crawl.requested`
- `classify.requests` <- key `classify.requested`
- Replies via RPC pattern: `reply_to` is a per-classifier exclusive queue; `correlation_id` ties requests to replies.

Request envelope (all messages):

```json
{
  "submission_id": "uuid",
  "trace_id": "uuid",
  "payload": { ... task-specific ... }
}
```

- `doc_ingest.requested.payload`: `{ "file_path": "/data/uploads/<id>.pdf", "filename": "..." }`
- `crawl.requested.payload`: `{ "website_url": "https://...", "email_domain": "..."|null }`
- `classify.requested.payload`: `{ "company_name", "website_url", "email_domain"|null, "has_document": bool }`

Reply envelope: `{ "submission_id", "ok": bool, "error": str|null, "result": { ... } }`

- Doc Ingest reply `result`: `{ "raw_text_excerpt": str, "summary": { "capabilities": [str], "products": [str], "services": [str], "naics_codes": [str], "free_text": str } }`
- Crawl reply `result`: `{ "urls_visited": [str], "summary": { "capabilities": [str], "products": [str], "services": [str], "naics_codes": [str], "free_text": str } }`

### DB schema (Postgres, used by all backend services)

- `submissions(id uuid pk, company_name text, website_url text, email_domain text null, file_path text null, status text, created_at timestamptz)`
- `documents(id uuid pk, submission_id uuid fk, filename text, raw_text text, summary jsonb)`
- `crawls(id uuid pk, submission_id uuid fk, urls_visited jsonb, raw_text text, summary jsonb)`
- `classifications(id uuid pk, submission_id uuid fk, fsc_codes jsonb, model text, created_at timestamptz)`
- `submission_events(id bigserial pk, submission_id uuid fk, kind text, payload jsonb, created_at timestamptz)` plus a trigger `NOTIFY submission_events_<submission_id>` on insert

## docker-compose services

- `postgres:16` with init SQL applied on first boot
- `rabbitmq:3-management`
- `api` (FastAPI, uvicorn, depends on postgres + rabbitmq)
- `classifier` (Classification Worker, depends on rabbitmq + postgres)
- `doc_ingest` (image built from `apps/workers/doc_ingest/`)
- `crawler` (image built from `apps/workers/crawler/`)
- `web` (image built from `apps/web/`, nginx on 5173 -> 80)

Shared volume `uploads:/data/uploads` mounted in `api`, `doc_ingest`, `classifier`.

## packages/shared module

- `shared/mq.py` — `connect()`, `publish(envelope, routing_key)`, `RpcClient.call(routing_key, envelope, timeout)` using `aio_pika` and correlation_id futures
- `shared/messages.py` — Pydantic models for every envelope/payload above
- `shared/db.py` — async SQLAlchemy engine + repository helpers; `emit_event(submission_id, kind, payload)` inserts and notifies
- `shared/fsc.py` — loads `data/fsc_catalog.json`; exposes `FSCCatalog` with `lookup(code) -> title|None` and `list_all() -> [(code, title)]`
- `shared/llm.py` — thin OpenAI client wrapper: `chat_json(system, user, schema)` enforces a JSON schema via response_format

## FSC catalog parser

- `scripts/parse_fsc_pdf.py`: open `AV_FSCClassAssignment._151007.pdf` with `pdfplumber`, regex `^\s*(\d{4})\s+(.+?)\s+\S{3,4}/\S{2,3}\s*$` to capture `(code, description)` lines from Table 1, dedupe, sort, write to `data/fsc_catalog.json` as `[{"code":"3408","title":"Machining Centers and Way-Type Machine"}, ...]`.
- Run once at repo setup; output committed to the repo for fast worker startup.

## API service

- `apps/api/app/main.py` mounts routes and lifespan that opens shared DB pool + MQ connection.
- `apps/api/app/routes/submissions.py`:
  - `POST /submissions`: validate, save file to `/data/uploads/{id}.pdf` if present, insert row, publish `classify.requested`, return 202.
  - `GET /submissions/{id}`: read current state + latest classification.
- `apps/api/app/routes/events.py`:
  - SSE handler that opens a dedicated Postgres connection, runs `LISTEN submission_events_<id>`, yields each notification as an SSE event. Sends an initial replay of any events already in `submission_events` for that submission so reconnects are safe.

## Classification Worker

- Consumes `classify.requests`.
- On message:
  1. `emit_event(submission_id, "progress", {stage:"classify", status:"started"})`
  2. In parallel via `RpcClient.call`:
     - If `has_document`: `doc_ingest.requested`
     - Always: `crawl.requested`
     - Emit `progress` events for each `started`/`done`/`failed`
  3. Persist `documents` and `crawls` rows from replies; allow either to fail (continue with what is available, emit a `progress` `failed`).
  4. Merge both summaries into `CompanyFeatures` JSON.
  5. Build LLM prompt: system message describes task and JSON schema; user message contains `CompanyFeatures` + the full FSC catalog (it is ~700 codes, fits easily in context).
  6. Call `shared.llm.chat_json` with strict schema `{codes: [{code: "^\\d{4}$", title, rationale, confidence:0..1}]}`.
  7. Drop codes whose `code` is not in `FSCCatalog`; cap to top 20 by confidence.
  8. Insert `classifications` row, `emit_event(... "result", {fsc_codes})`, and update `submissions.status = "done"`.
- Errors emit `error` events; do not retry in MVP (single delivery, ack on completion or failure).

## LLM prompt outline (kept in `apps/workers/classifier/prompts.py`)

System: "You are an expert at classifying defense and industrial suppliers using US Federal Supply Class (FSC) 4-digit codes. Pick only codes that appear in the provided catalog. Use NAICS codes, capabilities, products, and services as the strongest signals. Return strict JSON."

User payload:

```json
{
  "company": { "name": "...", "website_url": "...", "email_domain": "..." },
  "features": {
    "capabilities": [...],
    "products": [...],
    "services": [...],
    "naics_codes": [...],
    "free_text": "..."
  },
  "fsc_catalog": [{"code":"3408","title":"Machining Centers..."}, ...]
}
```

Constraint: model output must be `{"codes":[{"code":"NNNN","title":"...","rationale":"...","confidence":0.0-1.0}]}`.

## Tasks (atomic)

1. Scaffold monorepo dirs and root `README.md`, `.env.example`, `docker-compose.yml`, `Makefile` with `make up`, `make parse-fsc`, `make logs`.
2. `scripts/parse_fsc_pdf.py` + run once → commit `data/fsc_catalog.json`.
3. `packages/shared`: messages, mq, db, fsc, llm modules; unit tests for `FSCCatalog.lookup` and `chat_json` schema validation against a stubbed client.
4. Postgres init.sql with tables + `submission_events` trigger that issues `NOTIFY` per submission id.
5. FastAPI app skeleton with lifespan and `/health`.
6. `POST /submissions` and `GET /submissions/{id}` routes + persistence + file save.
7. SSE `/submissions/{id}/events` route using `LISTEN/NOTIFY` and initial replay.
8. Classification Worker bootstrap: connect MQ + DB, consume `classify.requests`.
9. Implement RPC fan-out to doc_ingest + crawl, persist replies, emit progress events.
10. Implement feature merge + LLM call + catalog validation + persistence + final `result` event.
11. Add Dockerfiles for `api` and `classifier`; wire into compose; smoke test `make up` with workers stubbed.
12. End-to-end test with a hard-coded fake submission that bypasses the SPA (curl) and a stub worker reply, asserting an SSE `result` event arrives.

## Done criteria

- `make up` boots postgres, rabbitmq, api, classifier (workers and web can be stubbed/empty for this agent).
- `curl -X POST /submissions` with sample payload returns a `submission_id`; a stub reply on `doc_ingest.requests` and `crawl.requests` (manually published) drives the classifier to produce a `result` SSE event with at least one valid FSC code from the catalog.
- `data/fsc_catalog.json` contains the parsed catalog and is loaded at worker startup.

## Out of scope

- Authentication, multi-tenant, audit logs.
- Retries, dead-letter queues, idempotency beyond MQ ack/nack.
- OCR, vector DBs, embeddings.

