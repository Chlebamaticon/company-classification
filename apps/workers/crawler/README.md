# apps/workers/crawler

Web Crawl Worker. Owned by the Ingest + Crawl agent.

Consumes `crawl.requests` (envelope payload `CrawlRequest`). Fetches the
homepage, follows in-domain links matching about/products/services/capabilit/parts,
depth 1, max ~8 pages, 30s total budget, robots.txt respected. Summarizes the
combined text into `CompanyFeatures` via `shared.llm.chat_json`, persists a row
in `crawls`, and replies with a `CrawlResult` on the `reply_to` queue.
