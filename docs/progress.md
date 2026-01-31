# VerifAI MVP — Progress Tracker

## M0 — Repo Bootstrap & Local Dev Shell ✅
- [x] Initialize monorepo structure (root package.json, workspaces)
- [x] Set up Vite + Vue + TailwindCSS frontend scaffold
- [x] Set up Cloudflare Worker scaffold (wrangler)
- [x] Set up FastAPI inference service scaffold
- [x] Write D1 migration SQL
- [x] Add .gitignore
- [x] Confirm all three components can start locally
  - Frontend builds successfully (vite build)
  - Worker typechecks clean (tsc --noEmit)
  - FastAPI app loads, 26/26 Python tests pass
  - Shared types package created

## M1 — Upload Flow (Client -> R2) ✅
- [x] Worker route `POST /api/upload/token`
- [x] Worker route `PUT /api/upload/:jobId` (proxy upload to R2)
- [x] Worker route `POST /api/upload/finalize` (hash, dedup, enqueue)
- [x] Worker route `GET /api/report/:jobId`
- [x] Worker route `POST /api/internal/report` (inference callback)
- [x] Queue consumer (forwards to inference service)
- [x] Cron handler (cleanup expired jobs/reports)
- [x] Frontend drag-and-drop UploadZone component
- [x] Wire frontend upload flow (token -> PUT -> finalize -> navigate)
- [x] Per-IP rate limiting (10/day, 1/min, D1-backed)
- [x] File size + content type validation (client + server)
- [x] Worker typechecks clean, frontend builds

## M2 — Inference Service (Metadata + Provenance) ✅
- [x] `POST /analyze` endpoint in FastAPI (auth, download, analyze, callback)
- [x] EXIF metadata extraction (Pillow + exifread)
- [x] C2PA / Content Credentials check (stub — returns not-present)
- [x] Report callback to Worker (`POST /api/internal/report`)
- [x] Original image deletion from R2 (handled by Worker on callback)
- [x] Base64 data URL support for image transfer from Worker

## M3 — ML Detector Integration ✅
- [x] Integrate CPU-friendly AI image detector (umm-maybe/AI-image-detector, ViT-based)
- [x] Lazy model loading with graceful fallback (returns None if unavailable)
- [x] Image resizing for large images before inference
- [x] Scoring and confidence tier logic (implemented + tested in M0)
- [x] Evidence bullet generation (implemented + tested in M0)
- [x] Limitations list generation (implemented + tested in M0)
- [x] Added transformers + torch to requirements.txt

## M4 — Report Page & Polling
- [ ] Worker route `GET /api/report/:jobId`
- [ ] Frontend processing view with step indicators
- [ ] Polling logic with backoff
- [ ] Shareable report page `/report/:jobId`
- [ ] Render all report sections

## M5 — Retention, Caching & Abuse Controls
- [ ] Scheduled cron for expired job cleanup
- [ ] File-hash deduplication
- [ ] Cloudflare Turnstile (optional)
- [ ] Max image dimension enforcement
- [ ] Content-type validation

## M6 — Polish, Testing & Deploy
- [ ] Unit tests (Python scoring/confidence)
- [ ] Unit tests (Python evidence/limitations)
- [ ] JSON contract validation tests
- [ ] Integration test
- [ ] Deploy frontend to Cloudflare Pages
- [ ] Deploy Worker + D1 + R2 + Queue
- [ ] Deploy inference service to Render
- [ ] Smoke test in production
- [ ] README
