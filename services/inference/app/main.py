"""FastAPI application entry-point for the VerifAI inference service."""

from __future__ import annotations

import logging
import traceback

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request

from app.config import settings
from app.schemas import AnalyzeRequest

logger = logging.getLogger("verifai.inference")

app = FastAPI(
    title="VerifAI Inference Service",
    version="0.1.0",
    docs_url="/docs",
)


# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------

async def _verify_shared_secret(request: Request) -> None:
    """Ensure the inbound request carries a valid Bearer token."""

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = auth_header.removeprefix("Bearer ").strip()
    if token != settings.shared_secret:
        raise HTTPException(status_code=403, detail="Invalid shared secret")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> dict[str, str]:
    """Lightweight health-check endpoint."""
    return {"status": "ok"}


@app.post("/analyze", dependencies=[Depends(_verify_shared_secret)])
async def analyze(request: AnalyzeRequest) -> dict[str, str]:
    """Kick off an image analysis pipeline and POST results to callback_url.

    The heavy lifting is intentionally synchronous in this MVP; a production
    deployment would offload to a task queue (Celery, ARQ, etc.).
    """

    # Lazy imports so the module-level import graph stays lightweight and
    # the service boots quickly even if optional deps are missing.
    from app import detector, metadata, provenance, scoring

    try:
        # 1. Download the image ------------------------------------------------
        import base64

        if request.image_url.startswith("data:"):
            # Handle base64 data URLs (used when Worker can't create pre-signed R2 URLs)
            _, encoded = request.image_url.split(",", 1)
            image_bytes: bytes = base64.b64decode(encoded)
        else:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(settings.download_timeout_seconds),
            ) as client:
                img_resp = await client.get(request.image_url)
                img_resp.raise_for_status()
                image_bytes = img_resp.content

        # 2. Extract metadata --------------------------------------------------
        meta = metadata.extract_metadata(image_bytes)

        # 3. Check provenance --------------------------------------------------
        prov = provenance.check_provenance(image_bytes)

        # 4. Run AI detector ---------------------------------------------------
        ai_likelihood = detector.detect(image_bytes)

        # 5. Build the report --------------------------------------------------
        report = scoring.build_report(
            job_id=request.job_id,
            ai_likelihood=ai_likelihood,
            metadata=meta,
            provenance=prov,
        )

        # 6. POST the report back to the callback URL --------------------------
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            await client.post(
                request.callback_url,
                json=report.model_dump(),
                headers={
                    "Authorization": f"Bearer {settings.callback_auth_secret}",
                    "Content-Type": "application/json",
                },
            )

        return {"status": "ok", "job_id": request.job_id}

    except Exception:
        # On any failure, try to notify the caller via the callback URL so the
        # job does not hang in a "processing" state forever.
        logger.exception("Analysis failed for job %s", request.job_id)

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                await client.post(
                    request.callback_url,
                    json={
                        "job_id": request.job_id,
                        "status": "failed",
                        "error": traceback.format_exc(),
                    },
                    headers={
                        "Authorization": f"Bearer {settings.callback_auth_secret}",
                        "Content-Type": "application/json",
                    },
                )
        except Exception:
            logger.exception(
                "Failed to send failure callback for job %s", request.job_id,
            )

        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed for job {request.job_id}",
        )
