# apps/workers/doc_ingest

Doc Ingest Worker. Owned by the Ingest + Crawl agent.

Consumes `doc_ingest.requests` (envelope payload `IngestRequest`). Reads the
uploaded PDF from the shared `uploads` volume at `payload.file_path`, extracts
text via pdfplumber, summarizes into `CompanyFeatures` via `shared.llm.chat_json`,
persists a row in `documents`, and replies with an `IngestResult` on the
`reply_to` queue using the original `correlation_id`.
