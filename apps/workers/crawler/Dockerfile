FROM python:3.12-slim

WORKDIR /app

COPY packages/shared /app/packages/shared
RUN pip install --no-cache-dir /app/packages/shared

COPY apps/workers/crawler /app/crawler
RUN pip install --no-cache-dir /app/crawler

CMD ["python", "-m", "crawler.worker"]
