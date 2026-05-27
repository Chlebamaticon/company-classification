# SalesPatriot FSC Code Classifier

MVP that takes company info (name, website URL, email domain, optional document)
and outputs the 4-digit Federal Supply Classification (FSC) codes that best
describe what the company sells or provides.

See `SP_Task.pdf` for the original assignment.

## Architecture

```
React SPA  -->  FastAPI  -->  RabbitMQ  -->  Classification Worker
                  |                              |
                  |                              +--> Doc Ingest Worker
                  |                              +--> Crawl Worker
                  |
                  +--> Postgres  (LISTEN/NOTIFY drives SSE back to the SPA)
```

All three workers reply to the Classification Worker via RPC
(`correlation_id` + `reply_to`). The Classifier merges their summaries with
the parsed FSC catalog and asks an LLM for ranked 4-digit codes, then validates
each code against the catalog before returning the result.

## Monorepo layout

```
apps/
  api/                  # FastAPI service
  web/                  # React SPA (Vite)
  workers/
    classifier/         # Classification Worker
    doc_ingest/         # Doc Ingest Worker (PDFs)
    crawler/            # Web Crawl Worker
packages/
  shared/               # Pydantic message schemas, MQ + DB helpers, FSC loader, LLM wrapper
data/
  fsc_catalog.json      # Parsed once from AV_FSCClassAssignment._151007.pdf
scripts/
  parse_fsc_pdf.py      # Regenerates data/fsc_catalog.json
infra/
  postgres/init.sql     # Schema + NOTIFY trigger
docs/                   # Reference PDFs
```

## Quick start

```bash
cp .env.example .env
make parse-fsc          # generate data/fsc_catalog.json (one-time)
make up                 # docker compose up --build
```

Then open <http://localhost:5173>.

## Agent ownership

This repository is being built by three parallel agents:

| Area                                | Owner agent                    |
| ----------------------------------- | ------------------------------ |
| `apps/web/`                         | SPA agent                      |
| `apps/api/`, `apps/workers/classifier/`, `packages/shared/`, root scaffolding | Classification Worker agent |
| `apps/workers/doc_ingest/`, `apps/workers/crawler/` | Ingest + Crawl agent |

Each agent's plan lives in `.cursor/plans/` and they share the contracts defined
in `packages/shared/salespatriot_shared/messages.py`, `infra/postgres/init.sql`,
and the HTTP/SSE contract documented in `apps/api/README.md`.
