"""Tests that the report JSON contract matches the expected schema."""

from __future__ import annotations

from app.schemas import AnalysisReport, MetadataResult, ProvenanceResult
from app.scoring import build_report


def _meta(**kwargs) -> MetadataResult:
    defaults = dict(
        has_exif=True,
        camera_make_model="Canon EOS R5",
        software_tag=None,
        width=1024,
        height=768,
        format="JPEG",
    )
    defaults.update(kwargs)
    return MetadataResult(**defaults)


def _prov(**kwargs) -> ProvenanceResult:
    defaults = dict(c2pa_present=False, c2pa_valid=None, notes=[])
    defaults.update(kwargs)
    return ProvenanceResult(**defaults)


class TestReportContract:
    """Validate the AnalysisReport JSON shape matches the API contract."""

    def test_report_has_all_required_fields(self) -> None:
        report = build_report("job-1", 85, _meta(), _prov())
        data = report.model_dump()

        required_keys = {
            "job_id",
            "status",
            "ai_likelihood",
            "confidence",
            "verdict_text",
            "evidence",
            "provenance",
            "metadata",
            "limitations",
        }
        assert required_keys.issubset(data.keys())

    def test_status_is_valid_enum(self) -> None:
        report = build_report("job-1", 85, _meta(), _prov())
        assert report.status in ("pending", "processing", "done", "failed")

    def test_confidence_is_valid_enum(self) -> None:
        report = build_report("job-1", 85, _meta(), _prov())
        assert report.confidence in ("high", "medium", "low")

    def test_ai_likelihood_is_bounded(self) -> None:
        for score in [0, 50, 100]:
            report = build_report("job-1", score, _meta(), _prov())
            assert 0 <= report.ai_likelihood <= 100

    def test_ai_likelihood_null_when_unavailable(self) -> None:
        report = build_report("job-1", None, _meta(), _prov())
        assert report.ai_likelihood is None
        assert report.confidence == "low"

    def test_evidence_is_list_of_strings(self) -> None:
        report = build_report("job-1", 85, _meta(), _prov())
        assert isinstance(report.evidence, list)
        assert all(isinstance(e, str) for e in report.evidence)
        assert len(report.evidence) >= 3

    def test_provenance_shape(self) -> None:
        report = build_report("job-1", 85, _meta(), _prov())
        p = report.provenance
        assert isinstance(p.c2pa_present, bool)
        assert p.c2pa_valid is None or isinstance(p.c2pa_valid, bool)
        assert isinstance(p.notes, list)

    def test_metadata_shape(self) -> None:
        report = build_report("job-1", 85, _meta(), _prov())
        m = report.metadata
        assert isinstance(m.has_exif, bool)
        assert isinstance(m.width, int)
        assert isinstance(m.height, int)
        assert isinstance(m.format, str)

    def test_limitations_always_has_mandatory_items(self) -> None:
        report = build_report("job-1", 85, _meta(), _prov())
        assert len(report.limitations) >= 2
        # Check the mandatory disclaimers are present
        all_text = " ".join(report.limitations).lower()
        assert "false positives" in all_text or "probabilistic" in all_text or "definitive" in all_text
        assert "post-processing" in all_text or "recompressed" in all_text or "edited" in all_text

    def test_report_serializes_to_valid_json(self) -> None:
        report = build_report("job-1", 85, _meta(), _prov())
        import json

        data = json.loads(report.model_dump_json())
        assert isinstance(data, dict)
        assert data["job_id"] == "job-1"
        assert data["status"] == "done"

    def test_report_with_provenance(self) -> None:
        prov = _prov(c2pa_present=True, c2pa_valid=True, notes=["AI generated content"])
        report = build_report("job-1", 95, _meta(), prov)
        assert report.confidence == "high"
        assert report.provenance.c2pa_present is True

    def test_failed_status_report(self) -> None:
        """Verify we can construct a report-like object for failed jobs."""
        report = AnalysisReport(
            job_id="job-fail",
            status="failed",
            ai_likelihood=None,
            confidence=None,
            verdict_text=None,
            evidence=[],
            provenance=ProvenanceResult(c2pa_present=False, c2pa_valid=None, notes=[]),
            metadata=MetadataResult(
                has_exif=False,
                camera_make_model=None,
                software_tag=None,
                width=0,
                height=0,
                format="",
            ),
            limitations=[],
        )
        data = report.model_dump()
        assert data["status"] == "failed"
        assert data["ai_likelihood"] is None
