FROM python:3.12-slim

WORKDIR /app

COPY packages/shared /app/packages/shared
RUN pip install --no-cache-dir /app/packages/shared

COPY apps/workers/doc_ingest /app/doc_ingest
RUN pip install --no-cache-dir /app/doc_ingest

CMD ["python", "-m", "doc_ingest.worker"]
