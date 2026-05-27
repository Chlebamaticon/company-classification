# System Patterns

- Monorepo with shared package `packages/shared` consumed by every backend service.
- Workers communicate via RabbitMQ RPC (`reply_to` + `correlation_id`).
- Postgres `submission_events` + `LISTEN/NOTIFY` drives SSE back to the SPA per submission (`submission_events:<uuid>`).
- LLM calls go through `shared.llm.chat_json` (JSON-mode + schema).
- FSC catalog is a static JSON file loaded once at worker startup; LLM output codes are validated against it before persistence.
- One classification per submission. No retries in MVP.
