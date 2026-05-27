# apps/workers/classifier

Classification Worker. Owned by the Classification Worker agent.

Consumes `classify.requests`, fans out to `doc_ingest.requests` and
`crawl.requests` via RPC (`reply_to` + `correlation_id`), merges the returned
`CompanyFeatures`, calls the LLM with the FSC catalog as context, validates each
4-digit code against the catalog, persists to `classifications`, and emits the
final `result` event on `submission_events` for SSE delivery.

The FSC catalog is loaded from `/app/data/fsc_catalog.json` (mounted by
docker-compose from `data/fsc_catalog.json`).
