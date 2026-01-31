# VerifAI MVP Implementation Plan

## 1. Milestones

### M0 — Repo Bootstrap & Local Dev Shell
- Initialize monorepo structure
- Set up Vite + Vue + TailwindCSS frontend scaffold
- Set up Cloudflare Worker scaffold (wrangler)
- Set up FastAPI inference service scaffold
- Configure D1 local database and R2 local emulation via `wrangler dev`
- Write D1 migration SQL
- Confirm all three components start locally

### M1 — Upload Flow (Client -> R2)
- Implement Worker route `POST /api/upload/token` that creates a job row in D1 and returns a signed R2 upload URL
- Implement Worker route `POST /api/upload/finalize` that validates the upload exists in R2, computes file hash, updates the job row, and enqueues a message to Cloudflare Queue
- Implement frontend drag-and-drop upload component
- Wire frontend to call token -> upload to R2 -> finalize
- Implement per-IP rate limiting middleware in the Worker
- Add file size validation (5 MB max) on both client and Worker

### M2 — Inference Service (Metadata + Provenance)
- Implement `POST /analyze` endpoint in FastAPI
- Download image from R2 using a pre-signed GET URL (passed by Worker)
- Extract EXIF metadata via `Pillow` / `exifread`
- Extract basic file info (dimensions, format, file size)
- Implement C2PA / Content Credentials check using `c2pa-python` library
- Return partial report JSON (metadata + provenance sections populated, ML section as placeholder)
- Write report to D1 via Worker callback endpoint `POST /api/internal/report`
- Delete original image from R2 after report is written

### M3 — ML Detector Integration
- Integrate a single CPU-friendly open-source AI image detector
- **Default choice: SigLIP-based AIDE or `umm-maybe/AI-image-detector` (HuggingFace, ViT-based, ~350 MB, runs on CPU)**
- If model is too heavy for the chosen free host, fall back to the placeholder (ai_likelihood=null, confidence=low) and document the gap
- Implement scoring and confidence tier logic
- Implement evidence bullet generation
- Implement limitations list generation
- Wire ML results into the report JSON

### M4 — Report Page & Polling
- Implement Worker route `GET /api/report/:jobId` returning the report JSON contract
- Implement frontend processing view with step indicators
- Implement polling logic (poll every 2s, back off to 5s after 30s, timeout at 5 min)
- Implement shareable report page at `/report/:jobId`
- Render all report sections: score, confidence, verdict, evidence, provenance, metadata, limitations, expiry

### M5 — Retention, Caching & Abuse Controls
- Implement scheduled Worker (cron trigger) that deletes expired jobs and reports from D1 (runs every hour)
- Implement file-hash deduplication: if `file_hash` already exists in a non-expired job, return existing report
- Add Cloudflare Turnstile to upload form (optional, behind env flag)
- Enforce max image dimensions (4096px); downscale before sending to inference if exceeded
- Validate content-type (accept only image/jpeg, image/png, image/webp, image/tiff)

### M6 — Polish, Testing & Deploy
- Unit tests for scoring/confidence tier logic (Python)
- Unit tests for evidence and limitations generation (Python)
- JSON contract validation tests (TypeScript + Python)
- Integration test: upload -> finalize -> analyze -> report
- Deploy frontend to Cloudflare Pages
- Deploy Worker + D1 + R2 + Queue via wrangler
- Deploy inference service to Render (free tier) or Fly.io
- Smoke test in production
- Write minimal README

---

## 2. Repo Structure

```
verifai/
├── apps/
│   ├── web/                        # Vue frontend (Vite)
│   │   ├── public/
│   │   ├── src/
│   │   │   ├── assets/
│   │   │   ├── components/
│   │   │   │   ├── UploadZone.vue
│   │   │   │   ├── ProcessingView.vue
│   │   │   │   ├── ReportCard.vue
│   │   │   │   ├── ScoreGauge.vue
│   │   │   │   ├── EvidenceList.vue
│   │   │   │   ├── ProvenanceSection.vue
│   │   │   │   ├── MetadataSection.vue
│   │   │   │   └── LimitationsBox.vue
│   │   │   ├── pages/
│   │   │   │   ├── HomePage.vue
│   │   │   │   └── ReportPage.vue
│   │   │   ├── lib/
│   │   │   │   ├── api.ts           # API client functions
│   │   │   │   └── polling.ts       # Report polling logic
│   │   │   ├── App.vue
│   │   │   ├── router.ts
│   │   │   └── main.ts
│   │   ├── index.html
│   │   ├── tailwind.config.js
│   │   ├── vite.config.ts
│   │   ├── tsconfig.json
│   │   └── package.json
│   │
│   └── worker/                     # Cloudflare Worker
│       ├── src/
│       │   ├── index.ts            # Router entry point
│       │   ├── routes/
│       │   │   ├── upload.ts       # /api/upload/token, /api/upload/finalize
│       │   │   ├── report.ts       # /api/report/:jobId
│       │   │   └── internal.ts     # /api/internal/report (inference callback)
│       │   ├── middleware/
│       │   │   └── rateLimit.ts
│       │   ├── queue.ts            # Queue consumer handler
│       │   ├── cron.ts             # Scheduled handler (retention cleanup)
│       │   ├── db.ts               # D1 query helpers
│       │   └── r2.ts               # R2 helpers (signed URLs, delete)
│       ├── migrations/
│       │   └── 0001_init.sql
│       ├── wrangler.toml
│       ├── tsconfig.json
│       └── package.json
│
├── services/
│   └── inference/                  # Python FastAPI inference service
│       ├── app/
│       │   ├── main.py             # FastAPI app + /analyze endpoint
│       │   ├── metadata.py         # EXIF extraction
│       │   ├── provenance.py       # C2PA check
│       │   ├── detector.py         # ML detector wrapper
│       │   ├── scoring.py          # Score, confidence, evidence, limitations
│       │   ├── schemas.py          # Pydantic models
│       │   └── config.py           # Environment / settings
│       ├── tests/
│       │   ├── test_scoring.py
│       │   ├── test_metadata.py
│       │   └── test_contract.py
│       ├── Dockerfile
│       ├── requirements.txt
│       └── pyproject.toml
│
├── packages/
│   └── shared/                     # Shared TypeScript types (optional)
│       ├── src/
│       │   └── types.ts            # Report JSON contract types
│       ├── tsconfig.json
│       └── package.json
│
├── docs/
│   └── plan.md                     # This file
├── .gitignore
├── README.md
└── package.json                    # Workspace root (npm workspaces)
```

---

## 3. API Route Definitions (Worker)

### `POST /api/upload/token`

Request:
```json
{
  "content_type": "image/jpeg",
  "file_size": 2048000
}
```

Validation:
- `content_type` must be one of: `image/jpeg`, `image/png`, `image/webp`, `image/tiff`
- `file_size` must be <= 5242880 (5 MB)

Response `200`:
```json
{
  "job_id": "a1b2c3d4-...",
  "upload_url": "https://r2-bucket.../uploads/a1b2c3d4-...?X-Amz-Signature=...",
  "expires_in": 300
}
```

Response `429`:
```json
{ "error": "Rate limit exceeded. Try again later." }
```

---

### `POST /api/upload/finalize`

Request:
```json
{
  "job_id": "a1b2c3d4-..."
}
```

Validation:
- Job must exist in D1 with status `pending`
- Object must exist in R2 at the expected key
- Compute SHA-256 hash of the object
- If a non-expired job with the same `file_hash` already exists and has status `done`, return that report immediately

Response `200` (new analysis):
```json
{
  "job_id": "a1b2c3d4-...",
  "status": "processing"
}
```

Response `200` (cache hit):
```json
{
  "job_id": "existing-job-id",
  "status": "done",
  "cached": true
}
```

Side effects:
- Updates job status to `processing`
- Sets `file_hash` on the job row
- Enqueues message to Cloudflare Queue
- On cache hit: deletes the duplicate upload from R2

---

### `GET /api/report/:jobId`

Response `200`:
```json
{
  "job_id": "a1b2c3d4-...",
  "status": "done",
  "ai_likelihood": 87,
  "confidence": "high",
  "verdict_text": "This image is likely AI-generated.",
  "evidence": [
    "Classifier indicates patterns consistent with synthetic generation",
    "No camera metadata found",
    "Content credentials not present"
  ],
  "provenance": {
    "c2pa_present": false,
    "c2pa_valid": null,
    "notes": []
  },
  "metadata": {
    "has_exif": false,
    "camera_make_model": null,
    "software_tag": null,
    "width": 1024,
    "height": 1024,
    "format": "png"
  },
  "limitations": [
    "This is a probabilistic estimate, not a definitive proof.",
    "Heavily edited, recompressed, or screenshot images reduce reliability."
  ],
  "expires_at": "2025-06-02T14:30:00Z"
}
```

Response `200` (still processing):
```json
{
  "job_id": "a1b2c3d4-...",
  "status": "processing",
  "ai_likelihood": null,
  "confidence": null,
  "verdict_text": null,
  "evidence": [],
  "provenance": { "c2pa_present": false, "c2pa_valid": null, "notes": [] },
  "metadata": { "has_exif": false, "camera_make_model": null, "software_tag": null, "width": 0, "height": 0, "format": "" },
  "limitations": [],
  "expires_at": "2025-06-02T14:30:00Z"
}
```

Response `404`:
```json
{ "error": "Report not found or expired." }
```

---

### `POST /api/internal/report`

Called by the inference service to write results back. Authenticated via a shared secret in the `Authorization` header.

Request:
```json
{
  "job_id": "a1b2c3d4-...",
  "status": "done",
  "ai_likelihood": 87,
  "confidence": "high",
  "verdict_text": "This image is likely AI-generated.",
  "evidence": ["..."],
  "provenance": { "c2pa_present": false, "c2pa_valid": null, "notes": [] },
  "metadata": { "has_exif": false, "camera_make_model": null, "software_tag": null, "width": 1024, "height": 1024, "format": "png" },
  "limitations": ["..."]
}
```

Response `200`:
```json
{ "ok": true }
```

---

## 4. Queue Message Schema

Queue name: `verifai-analysis`

Message body:
```json
{
  "job_id": "a1b2c3d4-...",
  "object_key": "uploads/a1b2c3d4-...",
  "callback_url": "https://verifai-worker.example.workers.dev/api/internal/report",
  "r2_presigned_get_url": "https://r2-bucket.../uploads/a1b2c3d4-...?X-Amz-Signature=..."
}
```

The queue consumer in the Worker receives this message and makes an HTTP POST to the inference service:

```
POST https://inference-service.example.com/analyze
Authorization: Bearer <SHARED_SECRET>
{
  "job_id": "a1b2c3d4-...",
  "object_key": "uploads/a1b2c3d4-...",
  "image_url": "<r2_presigned_get_url>",
  "callback_url": "https://verifai-worker.example.workers.dev/api/internal/report"
}
```

---

## 5. D1 SQL Schema

```sql
-- migrations/0001_init.sql

CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'done', 'failed')),
  object_key TEXT NOT NULL,
  file_hash TEXT,
  error_message TEXT,
  expires_at TEXT NOT NULL,
  ip_address TEXT
);

CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_expires_at ON jobs(expires_at);
CREATE INDEX idx_jobs_file_hash ON jobs(file_hash);

CREATE TABLE IF NOT EXISTS reports (
  job_id TEXT PRIMARY KEY REFERENCES jobs(id),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  ai_likelihood INTEGER,
  confidence TEXT CHECK (confidence IN ('high', 'medium', 'low')),
  verdict_text TEXT,
  evidence_json TEXT NOT NULL DEFAULT '[]',
  metadata_json TEXT NOT NULL DEFAULT '{}',
  provenance_json TEXT NOT NULL DEFAULT '{}',
  limitations_json TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS rate_limits (
  ip_address TEXT NOT NULL,
  window_date TEXT NOT NULL,
  request_count INTEGER NOT NULL DEFAULT 0,
  last_request_at TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (ip_address, window_date)
);
```

---

## 6. Environment Variables

### Frontend (`apps/web/.env`)
```
VITE_API_BASE_URL=http://localhost:8787   # Worker URL (local dev)
VITE_TURNSTILE_SITE_KEY=                  # Optional, empty disables Turnstile
```

### Worker (`apps/worker/.env` / wrangler.toml secrets)
```
# wrangler.toml bindings (not env vars):
# - D1 database binding: DB
# - R2 bucket binding: BUCKET
# - Queue binding: ANALYSIS_QUEUE

# Secrets (set via `wrangler secret put`):
INFERENCE_SERVICE_URL=https://inference.example.com
INFERENCE_SHARED_SECRET=<random-64-char-hex>
TURNSTILE_SECRET_KEY=                      # Optional
REPORT_TTL_HOURS=24
```

### Inference Service (`services/inference/.env`)
```
SHARED_SECRET=<same-random-64-char-hex>
CALLBACK_AUTH_SECRET=<same-random-64-char-hex>
MODEL_NAME=umm-maybe/AI-image-detector
MODEL_CACHE_DIR=/app/model_cache
MAX_IMAGE_DIMENSION=4096
DOWNLOAD_TIMEOUT_SECONDS=30
INFERENCE_TIMEOUT_SECONDS=60
```

---

## 7. Storage Object Key Scheme

Pattern: `uploads/{job_id}`

- `job_id` is a UUID v4, so keys are unguessable
- Example: `uploads/a1b2c3d4-e5f6-7890-abcd-ef1234567890`
- No file extension stored in the key; content-type is set as R2 metadata
- After analysis completes, the object at this key is deleted

---

## 8. Retention & Deletion Strategy

| What | Retention | Mechanism |
|---|---|---|
| Original image in R2 | Deleted immediately after inference completes | Inference service calls Worker delete endpoint, or Worker deletes after receiving report callback |
| Job row in D1 | 24 hours from creation (configurable via `REPORT_TTL_HOURS`) | Scheduled Worker cron runs hourly: `DELETE FROM jobs WHERE expires_at < datetime('now')` |
| Report row in D1 | Cascade-deleted with job | Same cron. Foreign key ensures report is removed when job is removed |
| Rate limit rows | 7 days | Same cron: `DELETE FROM rate_limits WHERE window_date < date('now', '-7 days')` |

### Deletion flow after inference:
1. Inference service completes analysis
2. Inference service POSTs report to `/api/internal/report`
3. Worker writes report to D1, updates job status to `done`
4. Worker deletes object from R2: `await env.BUCKET.delete(object_key)`
5. If inference fails, Worker sets job status to `failed` and still deletes from R2

---

## 9. Rate Limiting Approach

**Where:** Implemented in the Worker as middleware on `POST /api/upload/token`.

**Strategy:** IP-based using D1 `rate_limits` table.

**Rules:**
- 10 requests per calendar day (UTC) per IP
- 1 request per 60 seconds per IP (burst protection)

**Implementation:**
1. Extract client IP from `CF-Connecting-IP` header
2. Query `rate_limits` table for current day + IP
3. If `request_count >= 10`, return `429` with header `Retry-After: <seconds-until-midnight-utc>`
4. If `last_request_at` is within 60 seconds, return `429` with header `Retry-After: <remaining-seconds>`
5. Otherwise, upsert the row incrementing `request_count` and updating `last_request_at`

**Response headers on success:**
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: <unix-timestamp-midnight-utc>
```

---

## 10. Local Development Workflow

### Prerequisites
- Node.js >= 20
- Python >= 3.11
- wrangler CLI (`npm install -g wrangler`)
- A Cloudflare account (free tier)

### Setup
```bash
# Clone and install
git clone https://github.com/jdelaire/verifai.git
cd verifai
npm install                          # Installs workspace deps

# Set up Python inference service
cd services/inference
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ../..

# Create local D1 database
cd apps/worker
wrangler d1 execute verifai-db --local --file=migrations/0001_init.sql
cd ../..
```

### Running all components

**Terminal 1 — Worker (includes D1 + R2 + Queue locally):**
```bash
cd apps/worker
wrangler dev
# Runs on http://localhost:8787
```

**Terminal 2 — Inference service:**
```bash
cd services/inference
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
# Runs on http://localhost:8000
```

**Terminal 3 — Frontend:**
```bash
cd apps/web
npm run dev
# Runs on http://localhost:5173, proxies /api to localhost:8787
```

### Notes
- `wrangler dev` emulates D1, R2, and Queues locally
- For local dev, the queue consumer calls `http://localhost:8000/analyze` directly
- The inference service uses `http://localhost:8787/api/internal/report` as callback URL locally
- Model weights are downloaded on first run and cached in `services/inference/model_cache/`

---

## 11. Deployment Workflow

### Frontend (Cloudflare Pages)
```bash
cd apps/web
npm run build
wrangler pages deploy dist --project-name=verifai
```

Or connect the GitHub repo to Cloudflare Pages with:
- Build command: `cd apps/web && npm run build`
- Build output: `apps/web/dist`
- Root directory: `/`

### Worker (Cloudflare Workers + D1 + R2 + Queue)
```bash
cd apps/worker

# First time: create resources
wrangler d1 create verifai-db
wrangler r2 bucket create verifai-uploads
wrangler queues create verifai-analysis

# Update wrangler.toml with the returned IDs

# Run migration
wrangler d1 execute verifai-db --file=migrations/0001_init.sql

# Set secrets
wrangler secret put INFERENCE_SERVICE_URL
wrangler secret put INFERENCE_SHARED_SECRET

# Deploy
wrangler deploy
```

### Inference Service (Render free tier)
- Create a new Web Service on Render
- Point to `services/inference` directory
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Add environment variables: `SHARED_SECRET`, `CALLBACK_AUTH_SECRET`, `MODEL_NAME`
- Free tier note: service spins down after 15 min idle. First request after spin-up takes ~30s. This is acceptable for MVP.

### wrangler.toml (key sections)
```toml
name = "verifai-worker"
main = "src/index.ts"
compatibility_date = "2024-12-01"

[[d1_databases]]
binding = "DB"
database_name = "verifai-db"
database_id = "<from-wrangler-d1-create>"

[[r2_buckets]]
binding = "BUCKET"
bucket_name = "verifai-uploads"

[[queues.producers]]
binding = "ANALYSIS_QUEUE"
queue = "verifai-analysis"

[[queues.consumers]]
queue = "verifai-analysis"
max_batch_size = 1
max_retries = 2

[triggers]
crons = ["0 * * * *"]   # Every hour for retention cleanup
```

---

## 12. Testing Plan

### Python (Inference Service)

**Unit tests — `services/inference/tests/`**

`test_scoring.py`:
- Test confidence tier = `low` when image dimensions < 256px
- Test confidence tier = `low` when EXIF stripped AND no C2PA AND heavy JPEG recompression detected
- Test confidence tier = `high` when C2PA present and indicates AI origin
- Test confidence tier = `high` when model score >= 90 and image quality is good (no degradation flags)
- Test confidence tier = `medium` for intermediate cases
- Test ai_likelihood clamped to 0-100
- Test evidence bullets generated for missing EXIF
- Test evidence bullets generated for missing C2PA
- Test evidence bullets generated for recompression detection
- Test limitations always include the two mandatory strings

`test_metadata.py`:
- Test EXIF extraction from a JPEG with full EXIF
- Test EXIF extraction from a PNG (no EXIF expected)
- Test EXIF extraction from a stripped JPEG
- Test dimension extraction for various formats
- Test format detection

`test_contract.py`:
- Validate that `/analyze` response matches the report JSON schema exactly
- Test with a placeholder model (ai_likelihood=null case)
- Test error case returns status=failed and valid JSON

**Run:** `cd services/inference && pytest tests/ -v`

### TypeScript (Worker)

**Unit tests — `apps/worker/tests/`** (using Vitest)

`test_routes.test.ts`:
- Test `/api/upload/token` returns signed URL and job_id
- Test `/api/upload/token` rejects invalid content types
- Test `/api/upload/token` rejects files over 5 MB
- Test `/api/upload/finalize` returns 404 for unknown job
- Test `/api/report/:jobId` returns full contract shape for done jobs
- Test `/api/report/:jobId` returns 404 for expired jobs
- Test rate limit returns 429 when exceeded

`test_contract.test.ts`:
- Validate report response against TypeScript types
- Validate all enum fields have correct values

**Run:** `cd apps/worker && npx vitest run`

### Integration Test (manual or scripted)
```bash
# 1. Request upload token
curl -X POST http://localhost:8787/api/upload/token \
  -H 'Content-Type: application/json' \
  -d '{"content_type":"image/jpeg","file_size":100000}'

# 2. Upload file to returned URL
curl -X PUT "<upload_url>" \
  -H 'Content-Type: image/jpeg' \
  --data-binary @test_image.jpg

# 3. Finalize
curl -X POST http://localhost:8787/api/upload/finalize \
  -H 'Content-Type: application/json' \
  -d '{"job_id":"<job_id>"}'

# 4. Poll for report
curl http://localhost:8787/api/report/<job_id>
# Repeat until status=done
```

---

## 13. Definition of Done Checklist

- [ ] User can drag-and-drop or click to upload a single image (JPEG, PNG, WebP, TIFF)
- [ ] Upload is rejected client-side and server-side if > 5 MB
- [ ] Upload is rejected if content type is not an accepted image format
- [ ] After upload, user sees a processing view with step indicators
- [ ] Processing view polls and transitions to report view when done
- [ ] Report page displays: AI likelihood score (0-100), confidence tier, verdict text
- [ ] Report page displays: 3-8 evidence bullets
- [ ] Report page displays: provenance section (C2PA present/valid/notes)
- [ ] Report page displays: metadata section (EXIF, camera, software, dimensions, format)
- [ ] Report page displays: limitations section (always visible, always includes 2 mandatory items)
- [ ] Report page displays: expiration time
- [ ] Report page has a shareable URL using the job UUID
- [ ] Sharing the URL shows the same report (public, read-only)
- [ ] If same file hash exists in a non-expired job, existing report is returned (cache hit)
- [ ] Original image is deleted from R2 within seconds of analysis completing
- [ ] Jobs and reports are deleted after 24 hours by the cron worker
- [ ] Rate limiting enforced: 10/day and 1/minute per IP
- [ ] Rate limit exceeded returns 429 with appropriate headers
- [ ] Inference service handles timeouts and corrupt images gracefully (returns status=failed)
- [ ] If ML model is unavailable, report still completes with metadata + provenance (ai_likelihood=null, confidence=low)
- [ ] API responses match the documented JSON contract exactly
- [ ] Unit tests pass for scoring, confidence tier logic, and JSON contract
- [ ] Frontend deployed to Cloudflare Pages
- [ ] Worker deployed to Cloudflare Workers with D1, R2, Queue bindings
- [ ] Inference service deployed to Render (or equivalent free tier host)
- [ ] End-to-end smoke test passes in production

---

## Appendix A: Confidence Tier Rules (Exact Thresholds)

```python
def compute_confidence(
    ai_likelihood: int | None,
    has_exif: bool,
    c2pa_present: bool,
    c2pa_valid: bool | None,
    c2pa_indicates_ai: bool,
    width: int,
    height: int,
    jpeg_quality_estimate: int | None,  # None if not JPEG
    is_screenshot_like: bool,           # True if aspect ratio matches common screen sizes
) -> str:
    # --- Force LOW ---
    if ai_likelihood is None:
        return "low"
    if width < 256 or height < 256:
        return "low"
    if is_screenshot_like:
        return "low"
    if jpeg_quality_estimate is not None and jpeg_quality_estimate < 50:
        return "low"
    if not has_exif and not c2pa_present:
        # No provenance signals at all — lower trust in any direction
        if 30 <= ai_likelihood <= 70:
            return "low"

    # --- Force HIGH ---
    if c2pa_present and c2pa_valid and c2pa_indicates_ai:
        return "high"
    if ai_likelihood >= 90 and not is_screenshot_like and (jpeg_quality_estimate is None or jpeg_quality_estimate >= 70):
        return "high"
    if ai_likelihood <= 10 and has_exif and (jpeg_quality_estimate is None or jpeg_quality_estimate >= 70):
        return "high"

    # --- Otherwise MEDIUM ---
    return "medium"
```

## Appendix B: Verdict Text Templates

```python
def verdict_text(ai_likelihood: int | None, confidence: str) -> str:
    if ai_likelihood is None:
        return "Unable to determine AI likelihood. Only metadata and provenance checks were performed."
    if ai_likelihood >= 80:
        return "This image is likely AI-generated."
    if ai_likelihood >= 60:
        return "This image shows some indicators of AI generation."
    if ai_likelihood >= 40:
        return "The analysis is inconclusive for this image."
    if ai_likelihood >= 20:
        return "This image shows few indicators of AI generation."
    return "This image is likely authentic."
```

## Appendix C: Mandatory Limitations

Every report must include at minimum:
1. `"This is a probabilistic estimate, not a definitive proof."`
2. `"Heavily edited, recompressed, or screenshot images reduce reliability."`

Additional limitations are appended based on conditions:
- If `ai_likelihood is None`: `"ML analysis was unavailable. Results are based on metadata and provenance only."`
- If `confidence == "low"`: `"Low confidence: the image characteristics limit detection accuracy."`
- If no EXIF and no C2PA: `"No provenance signals were found. This neither confirms nor denies AI generation."`

## Appendix D: Screenshot Detection Heuristic

```python
COMMON_SCREEN_RATIOS = {(16, 9), (9, 16), (16, 10), (10, 16), (4, 3), (3, 4)}

def is_screenshot_like(width: int, height: int) -> bool:
    from math import gcd
    g = gcd(width, height)
    ratio = (width // g, height // g)
    # Simplify large ratios
    while ratio[0] > 32 or ratio[1] > 32:
        ratio = (round(ratio[0] / 2), round(ratio[1] / 2))
    return ratio in COMMON_SCREEN_RATIOS
```

Note: This is a rough heuristic. It flags common screen aspect ratios. False positives are acceptable because it only affects the confidence tier (degrades to low), not the likelihood score itself.
