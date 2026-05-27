# Active Context

Phase: scaffolding complete. Three agents now build in parallel against the
contracts in `packages/shared`.

Done:
- Monorepo dirs, `docker-compose.yml`, `.env.example`, `.gitignore`, `Makefile`, `README.md`.
- `infra/postgres/init.sql` with tables + per-submission NOTIFY trigger.
- `packages/shared`: full Pydantic message contracts; stub `mq`, `db`, `llm`; complete `fsc` loader.
- `scripts/parse_fsc_pdf.py` -> `data/fsc_catalog.json` (576 entries, spot-checked).
- 8 shared-package tests passing.

Next:
- SPA agent: `apps/web/` Vite + React + Tailwind, form, SSE subscription, results view.
- Classification Worker agent: flesh out `shared.mq`/`db`/`llm`, build FastAPI + Classifier.
- Ingest + Crawl agent: implement `apps/workers/doc_ingest` and `apps/workers/crawler`.
