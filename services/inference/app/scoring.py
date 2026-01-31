"""Scoring, confidence assessment, and report assembly."""

from __future__ import annotations

from app.schemas import AnalysisReport, MetadataResult, ProvenanceResult

# ---------------------------------------------------------------------------
# Mandatory limitation disclaimers that appear on every report.
# ---------------------------------------------------------------------------
_MANDATORY_LIMITATIONS: list[str] = [
    "AI-detection models can produce false positives and false negatives; "
    "this result should not be treated as definitive proof.",
    "Heavy post-processing (resizing, re-encoding, screenshots) degrades "
    "detection accuracy.",
]

# Formats / patterns that strongly suggest the image is a screenshot rather
# than a camera capture or a direct AI render.
_SCREENSHOT_SOFTWARE_HINTS = frozenset({
    "screenshot",
    "snipping tool",
    "snagit",
    "greenshot",
    "lightshot",
    "shareX",
})


# ---------------------------------------------------------------------------
# Helper predicates
# ---------------------------------------------------------------------------

def _is_screenshot_like(metadata: MetadataResult) -> bool:
    """Heuristic: does the metadata suggest this is a screenshot?"""
    if metadata.software_tag:
        lower = metadata.software_tag.lower()
        if any(hint in lower for hint in _SCREENSHOT_SOFTWARE_HINTS):
            return True
    # PNG with no EXIF is a weak signal but common for screenshots.
    if metadata.format == "PNG" and not metadata.has_exif:
        return True
    return False


def _is_good_quality(metadata: MetadataResult) -> bool:
    """Heuristic: is the image large enough and in a 'real' format?"""
    return (
        metadata.width >= 256
        and metadata.height >= 256
        and metadata.format in {"JPEG", "TIFF", "PNG", "WEBP"}
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_confidence(
    ai_likelihood: int | None,
    metadata: MetadataResult,
    provenance: ProvenanceResult,
) -> str:
    """Determine the confidence level of the analysis.

    Returns one of ``"high"``, ``"medium"``, or ``"low"``.

    Rules
    -----
    **Low** when any of these hold:
      - ``ai_likelihood`` is ``None`` (model unavailable)
      - either image dimension is below 256 px
      - the image looks like a screenshot
      - no EXIF *and* no C2PA *and* ``30 <= ai_likelihood <= 70``

    **High** when any of these hold:
      - C2PA is present, valid, and one of the notes mentions AI generation
      - ``ai_likelihood >= 90`` and the image is good quality
      - ``ai_likelihood <= 10`` and the image has EXIF and is good quality

    **Medium** otherwise.
    """

    # --- Low conditions -------------------------------------------------------
    if ai_likelihood is None:
        return "low"

    if metadata.width < 256 or metadata.height < 256:
        return "low"

    if _is_screenshot_like(metadata):
        return "low"

    if (
        not metadata.has_exif
        and not provenance.c2pa_present
        and 30 <= ai_likelihood <= 70
    ):
        return "low"

    # --- High conditions ------------------------------------------------------
    good = _is_good_quality(metadata)

    if (
        provenance.c2pa_present
        and provenance.c2pa_valid
        and any("ai" in n.lower() for n in provenance.notes)
    ):
        return "high"

    if ai_likelihood >= 90 and good:
        return "high"

    if ai_likelihood <= 10 and metadata.has_exif and good:
        return "high"

    # --- Default --------------------------------------------------------------
    return "medium"


def verdict_text(ai_likelihood: int | None) -> str:
    """Human-readable verdict string derived from the AI likelihood score."""

    if ai_likelihood is None:
        return (
            "Unable to determine AI likelihood. The detection model did not "
            "produce a score for this image."
        )
    if ai_likelihood >= 80:
        return "This image is likely AI-generated."
    if ai_likelihood >= 60:
        return "This image shows some indicators of AI generation."
    if ai_likelihood >= 40:
        return "The analysis is inconclusive for this image."
    if ai_likelihood >= 20:
        return "This image shows few indicators of AI generation."
    return "This image is likely authentic."


def _build_evidence(
    ai_likelihood: int | None,
    metadata: MetadataResult,
    provenance: ProvenanceResult,
) -> list[str]:
    """Assemble human-readable evidence bullets."""

    evidence: list[str] = []

    # AI score
    if ai_likelihood is not None:
        evidence.append(f"AI detection model returned a score of {ai_likelihood}/100.")
    else:
        evidence.append("AI detection model did not return a score.")

    # Camera / EXIF
    if metadata.has_exif:
        if metadata.camera_make_model:
            evidence.append(
                f"EXIF data indicates the image was captured by {metadata.camera_make_model}."
            )
        else:
            evidence.append("EXIF data is present but does not include camera make/model.")
    else:
        evidence.append("No EXIF metadata found in the image.")

    # Software
    if metadata.software_tag:
        evidence.append(f"Software tag detected: {metadata.software_tag}.")

    # Provenance
    if provenance.c2pa_present:
        validity = "valid" if provenance.c2pa_valid else "invalid or unverifiable"
        evidence.append(f"C2PA content credentials found ({validity}).")
    else:
        evidence.append("No C2PA content credentials found.")

    # Dimensions / format
    evidence.append(
        f"Image is {metadata.width}x{metadata.height} pixels in {metadata.format} format."
    )

    # Screenshot heuristic
    if _is_screenshot_like(metadata):
        evidence.append(
            "Image appears to be a screenshot, which reduces detection reliability."
        )

    return evidence


def _build_limitations(
    ai_likelihood: int | None,
    metadata: MetadataResult,
) -> list[str]:
    """Assemble limitation disclaimers -- always includes the mandatory ones."""

    limitations = list(_MANDATORY_LIMITATIONS)

    if ai_likelihood is None:
        limitations.append(
            "The AI-detection model was unavailable; the report is based "
            "solely on metadata and provenance signals."
        )

    if metadata.width < 256 or metadata.height < 256:
        limitations.append(
            "The image is very small, which significantly reduces detection accuracy."
        )

    if _is_screenshot_like(metadata):
        limitations.append(
            "The image appears to be a screenshot; detection models perform "
            "poorly on screen-captured content."
        )

    return limitations


def build_report(
    job_id: str,
    ai_likelihood: int | None,
    metadata: MetadataResult,
    provenance: ProvenanceResult,
) -> AnalysisReport:
    """Assemble the complete analysis report.

    Parameters
    ----------
    job_id:
        Unique identifier for this analysis job.
    ai_likelihood:
        AI likelihood score 0-100, or ``None`` if the model was unavailable.
    metadata:
        Extracted image metadata.
    provenance:
        C2PA provenance inspection results.

    Returns
    -------
    AnalysisReport
    """

    confidence = compute_confidence(ai_likelihood, metadata, provenance)
    verdict = verdict_text(ai_likelihood)
    evidence = _build_evidence(ai_likelihood, metadata, provenance)
    limitations = _build_limitations(ai_likelihood, metadata)

    return AnalysisReport(
        job_id=job_id,
        status="done",
        ai_likelihood=ai_likelihood,
        confidence=confidence,
        verdict_text=verdict,
        evidence=evidence,
        provenance=provenance,
        metadata=metadata,
        limitations=limitations,
    )
