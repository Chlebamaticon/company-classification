FROM python:3.12-slim

WORKDIR /app

COPY packages/shared /app/packages/shared
RUN pip install --no-cache-dir /app/packages/shared

COPY apps/workers/classifier/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY apps/workers/classifier/worker /app/worker
COPY data/fsc_catalog.json /app/data/fsc_catalog.json

CMD ["python", "-m", "worker.main"]
