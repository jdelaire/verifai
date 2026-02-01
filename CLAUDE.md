# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VerifAI is an AI-generated image detection service. Users upload an image and receive a report estimating AI generation likelihood, with supporting metadata analysis, C2PA provenance checks, and optional ViT-based ML detection.

## Architecture

Three-service architecture connected via HTTP callbacks:

```
Vue SPA (Vite) → Cloudflare Worker (D1 + R2) → FastAPI Inference (Python)
```

- **`apps/web`** — Vue 3 + Vite + TailwindCSS v4 frontend. Drag-and-drop upload, polling, report rendering. Proxies `/api` to the Worker in dev.
- **`apps/worker`** — Cloudflare Worker. Manual pathname-based router (no framework). Uses D1 (SQLite) for jobs/reports/rate-limits, R2 for temporary image storage. Dispatches inference via `ctx.waitUntil()` (not Queues). Images are base64-encoded and sent as data URLs to the inference service.
- **`services/inference`** — Python FastAPI service. Extracts EXIF metadata (Pillow + exifread), checks C2PA provenance, optionally runs a ViT detector (`umm-maybe/AI-image-detector`). Posts results back to the Worker via callback URL.
- **`packages/shared`** — TypeScript type definitions (`Report`, `Provenance`, `ImageMetadata`, etc.) shared between frontend and worker via npm workspaces.

### Key data flow

1. Client requests upload token (`POST /api/upload/token`) → Worker creates job in D1
2. Client uploads image bytes (`PUT /api/upload/:jobId`) → Worker proxies to R2
3. Client finalizes (`POST /api/upload/finalize`) → Worker computes SHA-256 hash, checks for dedup, dispatches inference via `ctx.waitUntil()`
4. Worker reads image from R2, base64-encodes it, POSTs to inference service
5. Inference service analyzes and POSTs report back to `POST /api/internal/report`
6. Client polls `GET /api/report/:jobId` until status is `done`

### D1 schema (3 tables)

- `jobs` — tracks upload/analysis lifecycle (pending → processing → done/failed)
- `reports` — stores analysis results (JSON columns for evidence, metadata, provenance, limitations)
- `rate_limits` — IP-based rate limiting (per-day + burst)

## Common Commands

### Install dependencies

```bash
npm install                          # All workspace packages (from repo root)
cd services/inference && python3.11 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

### Run locally (3 terminals)

```bash
npm run dev:web          # Frontend — http://localhost:5173
npm run dev:worker       # Worker — http://localhost:8787
# Inference (from services/inference with venv active):
uvicorn app.main:app --reload --port 8001
```

### Database migration (local)

```bash
npm run db:migrate:local -w apps/worker
```

### Testing

```bash
# Python tests (from services/inference with venv active)
pytest                   # all tests
pytest tests/test_scoring.py           # single file
pytest tests/test_scoring.py::test_name -v  # single test

# TypeScript typechecking
npm run typecheck -w apps/worker       # Worker
npm run build:web                      # Frontend (typecheck + build)
```

### Deploy

```bash
npm run build:web                      # Build frontend → apps/web/dist
npm run deploy -w apps/worker          # Deploy Worker (requires wrangler login)
# Inference: deployed to Render via render.yaml (Docker)
```

## Worker Environment

Secrets for local dev go in `apps/worker/.dev.vars`:
- `INFERENCE_SERVICE_URL` — inference endpoint (default: `http://localhost:8001`)
- `INFERENCE_SHARED_SECRET` — shared auth secret
- `WORKER_URL` — base URL for callback (default: `http://localhost:8787`)

Wrangler bindings in `wrangler.toml`: `DB` (D1), `BUCKET` (R2). Cron runs hourly for expired job cleanup.

## Inference Service Environment

Config in `services/inference/.env`:
- `SHARED_SECRET` — must match Worker's `INFERENCE_SHARED_SECRET`
- `CALLBACK_AUTH_SECRET` — auth for callback endpoint

Two requirements files: `requirements.txt` (base, no ML) and `requirements-ml.txt` (adds PyTorch + transformers, ~1.5 GB). Without ML deps, reports still include metadata and provenance but `ai_likelihood` is `null`.

## Scoring Logic

The scoring system in `services/inference/app/scoring.py` uses a confidence tier model:
- **Low**: model unavailable, tiny images (<256px), screenshots, ambiguous scores (30-70) with no provenance
- **High**: valid C2PA indicating AI, model score >=90 with good quality, score <=10 with EXIF
- **Medium**: everything else

Verdict text maps from `ai_likelihood` ranges (>=80 likely AI, >=60 some indicators, >=40 inconclusive, >=20 few indicators, <20 likely authentic). Every report includes mandatory limitation disclaimers.
