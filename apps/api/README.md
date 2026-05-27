# apps/api

FastAPI service. Owned by the Classification Worker agent.

Implements:

- `POST /submissions` (multipart) -> `{submission_id, status:"queued"}`
- `GET /submissions/{id}` -> current state
- `GET /submissions/{id}/events` (SSE) -> stream of `progress` / `result` / `error`

Backed by Postgres (`submissions`, `submission_events`) and RabbitMQ (publishes
`classify.requested` envelopes to the classifier).

See `infra/postgres/init.sql` for the schema and
`packages/shared/salespatriot_shared/messages.py` for the message contracts.
