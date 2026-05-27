FROM python:3.12-slim

WORKDIR /app

COPY packages/shared /app/packages/shared
RUN pip install --no-cache-dir /app/packages/shared

COPY apps/workers/classifier /app/classifier
RUN pip install --no-cache-dir /app/classifier

CMD ["python", "-m", "classifier.worker"]
