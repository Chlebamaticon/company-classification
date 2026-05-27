# Tech Context

- Python 3.12, Pydantic v2, FastAPI, aio-pika, SQLAlchemy async + asyncpg, pdfplumber, BeautifulSoup, httpx.
- Node 20 + Vite + React 18 + TypeScript + Tailwind for the SPA.
- Postgres 16, RabbitMQ 3 (management), Nginx 1.x (web prod image).
- Orchestrated via `docker-compose.yml`. Single `uploads` volume shared between `api`, `doc_ingest`, and `classifier`.
- LLM: OpenAI by default, configurable via `OPENAI_MODEL` (default `gpt-4o-mini`).
