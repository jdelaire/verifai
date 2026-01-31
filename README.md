# VerifAI

AI-generated image detection as a service. Upload an image and receive a report estimating the likelihood it was created by an AI model, with supporting evidence, metadata analysis, and provenance checks.

## Architecture

```
┌──────────┐     ┌──────────────────┐     ┌───────────────────┐
│ Vue SPA  │────>│ Cloudflare Worker│────>│ FastAPI Inference  │
│ (Vite)   │<────│ D1 + R2 + Queue  │<────│ (ViT detector)    │
└──────────┘     └──────────────────┘     └───────────────────┘
```

- **Frontend** (`apps/web`) — Vue 3 + Vite + TailwindCSS v4. Drag-and-drop upload, polling, and report rendering.
- **API Worker** (`apps/worker`) — Cloudflare Worker with D1 (SQLite) for job/report storage, R2 for temporary image storage, and Queues for async inference dispatch.
- **Inference Service** (`services/inference`) — Python FastAPI service. Extracts EXIF metadata, checks C2PA provenance, and runs a ViT-based AI image detector (`umm-maybe/AI-image-detector`).
- **Shared Types** (`packages/shared`) — TypeScript type definitions shared between frontend and worker.

## Prerequisites

- Node.js >= 18
- Python 3.11
- npm (ships with Node)

## Local Development

### 1. Install dependencies

```bash
# From repo root — installs all workspace packages
npm install

# Python inference service
cd services/inference
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

The Worker needs these `[vars]` in `wrangler.toml` (already set with defaults):

| Variable | Description |
|---|---|
| `REPORT_TTL_HOURS` | Hours before reports expire (default: 24) |

The Worker also needs these secrets (set via `wrangler secret put`):

| Secret | Description |
|---|---|
| `SHARED_SECRET` | Auth token for Worker <-> Inference communication |
| `INFERENCE_URL` | URL of the inference service (e.g. `http://localhost:8000`) |

The inference service reads these environment variables:

| Variable | Description |
|---|---|
| `SHARED_SECRET` | Must match the Worker's secret |
| `CALLBACK_AUTH_SECRET` | Token the inference service sends back in report callbacks |

### 3. Run the D1 migration

```bash
npm run db:migrate:local -w apps/worker
```

### 4. Start all services

In three separate terminals:

```bash
# Terminal 1 — Frontend (http://localhost:5173)
npm run dev:web

# Terminal 2 — Worker (http://localhost:8787)
npm run dev:worker

# Terminal 3 — Inference (http://localhost:8000)
cd services/inference
source .venv/bin/activate
uvicorn app.main:app --reload
```

## API Routes

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/upload/token` | Request a job ID and upload URL |
| `PUT` | `/api/upload/:jobId` | Upload image bytes (proxied to R2) |
| `POST` | `/api/upload/finalize` | Validate upload, hash, dedup, enqueue |
| `GET` | `/api/report/:jobId` | Poll for report status/results |
| `POST` | `/api/internal/report` | Inference callback (internal only) |

## Testing

```bash
# Python tests (38 tests — scoring, evidence, contract validation)
cd services/inference
source .venv/bin/activate
pytest

# Worker typecheck
npm run typecheck -w apps/worker

# Frontend typecheck + build
npm run build:web
```

## Deployment

- **Frontend**: Cloudflare Pages — `npm run build:web`, deploy `apps/web/dist`
- **Worker**: `npm run deploy -w apps/worker` (requires `wrangler login`)
- **Inference**: Deploy to Render or Fly.io with `services/inference` as root, Python 3.11 runtime

## Key Design Decisions

- **Proxy upload**: Cloudflare Workers can't generate pre-signed R2 URLs, so the Worker proxies uploads via `PUT /api/upload/:jobId`.
- **Base64 image transfer**: The queue consumer reads from R2, base64-encodes the image, and sends it as a data URL to the inference service.
- **Lazy model loading**: The ViT detector loads on first request to keep FastAPI startup fast. Returns `null` scores gracefully if the model is unavailable.
- **Rate limiting**: IP-based, backed by D1. 10 requests/day, 1 request/minute burst limit.
- **File dedup**: SHA-256 hash on finalize. If a matching non-expired report exists, it's returned immediately.
- **Auto-cleanup**: Hourly cron deletes expired jobs, reports, and stale rate-limit rows.

## License

Private — all rights reserved.
