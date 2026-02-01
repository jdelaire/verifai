"""FastAPI application entry-point for the VerifAI inference service."""

from __future__ import annotations

import asyncio
import logging
import traceback

import httpx
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request

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
# Background pipeline
# ---------------------------------------------------------------------------

def _run_pipeline(job_id: str, image_url: str, callback_url: str) -> None:
    """Run the full analysis pipeline synchronously, then POST the result."""
    import base64

    from app import detector, metadata, provenance, scoring

    try:
        # 1. Decode the image
        if image_url.startswith("data:"):
            _, encoded = image_url.split(",", 1)
            image_bytes: bytes = base64.b64decode(encoded)
        else:
            # Synchronous download for background task
            import httpx as httpx_sync

            with httpx_sync.Client(timeout=settings.download_timeout_seconds) as client:
                img_resp = client.get(image_url)
                img_resp.raise_for_status()
                image_bytes = img_resp.content

        # 2. Extract metadata
        meta = metadata.extract_metadata(image_bytes)

        # 3. Check provenance
        prov = provenance.check_provenance(image_bytes)

        # 4. Run AI detector
        ai_likelihood = detector.detect(image_bytes)

        # 5. Build the report
        report = scoring.build_report(
            job_id=job_id,
            ai_likelihood=ai_likelihood,
            metadata=meta,
            provenance=prov,
        )

        # 6. POST the report back to the callback URL
        with httpx.Client(timeout=10.0) as client:
            client.post(
                callback_url,
                json=report.model_dump(),
                headers={
                    "Authorization": f"Bearer {settings.callback_auth_secret}",
                    "Content-Type": "application/json",
                },
            )

        logger.info("Analysis complete for job %s", job_id)

    except Exception:
        logger.exception("Analysis failed for job %s", job_id)

        try:
            with httpx.Client(timeout=10.0) as client:
                client.post(
                    callback_url,
                    json={
                        "job_id": job_id,
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
                "Failed to send failure callback for job %s", job_id,
            )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> dict[str, str]:
    """Lightweight health-check endpoint."""
    return {"status": "ok"}


@app.post("/analyze", dependencies=[Depends(_verify_shared_secret)])
async def analyze(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    """Accept an analysis job and run the pipeline in the background.

    Returns immediately so the calling Worker doesn't time out.
    """
    background_tasks.add_task(
        _run_pipeline,
        request.job_id,
        request.image_url,
        request.callback_url,
    )
    return {"status": "accepted", "job_id": request.job_id}
