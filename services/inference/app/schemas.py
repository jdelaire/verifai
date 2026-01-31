"""Pydantic request / response models for the inference service."""

from __future__ import annotations

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Inbound request
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    """Payload sent by the API gateway to kick off an analysis job."""

    job_id: str
    object_key: str
    image_url: str
    callback_url: str


# ---------------------------------------------------------------------------
# Sub-models used inside the analysis report
# ---------------------------------------------------------------------------

class ProvenanceResult(BaseModel):
    """C2PA / content-provenance inspection results."""

    c2pa_present: bool
    c2pa_valid: bool | None = None
    notes: list[str] = []


class MetadataResult(BaseModel):
    """Image metadata extracted via Pillow + exifread."""

    has_exif: bool
    camera_make_model: str | None = None
    software_tag: str | None = None
    width: int
    height: int
    format: str


# ---------------------------------------------------------------------------
# Full analysis report returned to the API gateway via callback
# ---------------------------------------------------------------------------

class AnalysisReport(BaseModel):
    """Complete analysis report POSTed back to the callback URL."""

    job_id: str
    status: str
    ai_likelihood: int | None = None
    confidence: str | None = None
    verdict_text: str | None = None
    evidence: list[str] = []
    provenance: ProvenanceResult
    metadata: MetadataResult
    limitations: list[str] = []
