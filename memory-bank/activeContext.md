# Active Context

Phase: scaffolding complete. Three agents now build in parallel against the
contracts in `packages/shared`.

Done:
- Monorepo dirs, `docker-compose.yml`, `.env.example`, `.gitignore`, `Makefile`, `README.md`.
- `infra/postgres/init.sql` with tables + per-submission NOTIFY trigger.
- `packages/shared`: full Pydantic message contracts; stub `mq`, `db`, `llm`; complete `fsc` loader.
- `scripts/parse_fsc_pdf.py` -> `data/fsc_catalog.json` (576 entries, spot-checked).
- 8 shared-package tests passing.

Done (continued):
- SPA agent: `apps/web/` complete — form, SSE progress, results cards, mock mode, 18 tests, Dockerfile+nginx.

Done (Ingest + Crawl agent):
- `apps/workers/doc_ingest/`: extract.py, worker.py, prompts.py, Dockerfile, pyproject.toml. 15 tests passing.
- `apps/workers/crawler/`: url.py, links.py, fetch.py, worker.py, prompts.py, Dockerfile, pyproject.toml. 46 tests passing.
- `apps/workers/README.md`: worker-smoke runbook with rabbitmqadmin.

Next:
- Classification Worker agent: flesh out `shared.mq`/`db`/`llm`, build FastAPI + Classifier.
