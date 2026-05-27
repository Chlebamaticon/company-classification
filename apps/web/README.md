# apps/web

React SPA for SalesPatriot FSC classification.

## Stack

Vite + React 18 + TypeScript + Tailwind CSS. Tests via Vitest + React Testing Library.

## Dev

```bash
cd apps/web
npm install
npm run dev          # http://localhost:5173
```

Mock mode (no backend required):

```bash
VITE_USE_MOCK=true npm run dev
```

## Test

```bash
npm test             # single run
npm run test:watch   # watch mode
```

## Production (Docker)

```bash
docker build -t salespatriot-web .
docker run -p 80:80 salespatriot-web
```

Nginx proxies `/api/*` to the `api` service on port 8000 inside the compose network.

## API Contract

- `POST /api/submissions` — multipart form (company_name, website_url, email_domain?, file?)
- `GET /api/submissions/{id}` — current state
- `GET /api/submissions/{id}/events` — SSE stream (progress, result, error events)
