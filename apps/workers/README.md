# Workers

Two RabbitMQ-driven workers that produce normalized `CompanyFeatures` summaries:

- **doc_ingest** — parses uploaded PDFs, extracts text, summarizes via LLM
- **crawler** — fetches relevant website pages, cleans HTML, summarizes via LLM

## Running locally

```bash
docker compose up postgres rabbitmq doc_ingest crawler
```

## Worker Smoke Test

Requires `rabbitmqadmin` (ships with the management plugin image, or install locally).

### 1. Start infrastructure + workers

```bash
docker compose up -d postgres rabbitmq doc_ingest crawler
```

### 2. Test doc_ingest

```bash
# Create a temp reply queue
rabbitmqadmin declare queue name=test.reply durable=false

# Publish a request (place a test PDF at /data/uploads/test.pdf in the uploads volume)
rabbitmqadmin publish \
  exchange=amq.default \
  routing_key=doc_ingest.requests \
  properties='{"reply_to":"test.reply","correlation_id":"smoke-1"}' \
  payload='{"submission_id":"00000000-0000-0000-0000-000000000001","trace_id":"00000000-0000-0000-0000-000000000002","payload":{"file_path":"/data/uploads/test.pdf","filename":"test.pdf"}}'

# Wait a few seconds, then read the reply
rabbitmqadmin get queue=test.reply count=1
```

### 3. Test crawler

```bash
rabbitmqadmin publish \
  exchange=amq.default \
  routing_key=crawl.requests \
  properties='{"reply_to":"test.reply","correlation_id":"smoke-2"}' \
  payload='{"submission_id":"00000000-0000-0000-0000-000000000001","trace_id":"00000000-0000-0000-0000-000000000003","payload":{"website_url":"https://loosco.com/","email_domain":null}}'

# Wait ~30s for crawl + LLM, then:
rabbitmqadmin get queue=test.reply count=1
```

### 4. Cleanup

```bash
rabbitmqadmin delete queue name=test.reply
docker compose down
```

## Running tests

```bash
# doc_ingest
cd apps/workers/doc_ingest
pip install -e ".[dev]" && pip install -e ../../../packages/shared
pytest tests/ -v

# crawler
cd apps/workers/crawler
pip install -e ".[dev]" && pip install -e ../../../packages/shared
pytest tests/ -v
```
