# Active Context

Phase: Classification Worker agent complete. Remaining: SPA + Ingest/Crawl agents.

Done:
- Monorepo dirs, `docker-compose.yml`, `.env.example`, `.gitignore`, `Makefile`, `README.md`.
- `infra/postgres/init.sql` with tables + per-submission NOTIFY trigger.
- `packages/shared`: messages, fsc (complete); mq, db, llm (implemented).
- `scripts/parse_fsc_pdf.py` -> `data/fsc_catalog.json` (576 entries).
- 8 shared-package tests passing.
- `apps/api/`: FastAPI with `/health`, `POST /submissions`, `GET /submissions/{id}`, SSE `/submissions/{id}/events`.
- `apps/workers/classifier/`: consumes `classify.requests`, RPC fan-out, LLM classification, FSC validation.
- Dockerfiles for api + classifier.

Done (continued):
- SPA agent: `apps/web/` complete — form, SSE progress, results cards, mock mode, 18 tests, Dockerfile+nginx.

Done (Ingest + Crawl agent):
- `apps/workers/doc_ingest/`: extract.py, worker.py, prompts.py, Dockerfile, pyproject.toml. 15 tests passing.
- `apps/workers/crawler/`: url.py, links.py, fetch.py, worker.py, prompts.py, Dockerfile, pyproject.toml. 46 tests passing.
- `apps/workers/README.md`: worker-smoke runbook with rabbitmqadmin.

Next:
- Integration testing / e2e smoke test.
