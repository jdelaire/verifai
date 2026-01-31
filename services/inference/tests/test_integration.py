"""Integration test: exercises the full /analyze pipeline end-to-end.

The ML detector and the outbound HTTP callback are mocked so the test
can run without downloading model weights or a live callback server,
but every other layer (metadata extraction, provenance check, scoring,
report assembly) runs against real image bytes.
"""

from __future__ import annotations

import base64
import io
import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image

from app.main import app

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_jpeg_bytes(width: int = 640, height: int = 480) -> bytes:
    """Generate a minimal valid JPEG image in-memory."""
    img = Image.new("RGB", (width, height), color=(120, 180, 60))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _make_data_url(image_bytes: bytes, media_type: str = "image/jpeg") -> str:
    encoded = base64.b64encode(image_bytes).decode()
    return f"data:{media_type};base64,{encoded}"


def _mock_httpx_client(captured: dict):
    """Build a mock httpx.AsyncClient that captures the callback POST.

    Only patches the ``httpx.AsyncClient`` reference inside ``app.main``
    so the test's own ``AsyncClient`` (ASGI transport) is unaffected.
    """
    mock_client = AsyncMock()

    async def _capture_post(url, *, json=None, headers=None, **kwargs):
        captured["url"] = str(url)
        captured["body"] = json
        captured["headers"] = dict(headers) if headers else {}
        return httpx.Response(200, json={"status": "ok"})

    mock_client.post = _capture_post

    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    mock_cls = MagicMock(return_value=mock_cm)
    return mock_cls


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def jpeg_bytes():
    return _make_jpeg_bytes()


@pytest.fixture()
def analyze_payload(jpeg_bytes):
    return {
        "job_id": "integration-1",
        "object_key": "uploads/integration-1",
        "image_url": _make_data_url(jpeg_bytes),
        "callback_url": "https://worker.example.com/api/internal/report",
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAnalyzeEndpoint:
    """Integration tests for POST /analyze."""

    @pytest.mark.asyncio
    async def test_full_pipeline_with_score(self, analyze_payload):
        """Pipeline returns a valid report when the detector returns a score."""
        captured: dict = {}

        with (
            patch("app.detector.detect", return_value=72),
            patch("app.main.httpx.AsyncClient", _mock_httpx_client(captured)),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(
                    "/analyze",
                    json=analyze_payload,
                    headers={"Authorization": "Bearer test-secret"},
                )

        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

        # Verify the callback was called with a well-formed report
        body = captured["body"]
        assert body["job_id"] == "integration-1"
        assert body["status"] == "done"
        assert body["ai_likelihood"] == 72
        assert body["confidence"] in ("high", "medium", "low")
        assert "This image shows some indicators" in body["verdict_text"]
        assert isinstance(body["evidence"], list)
        assert len(body["evidence"]) >= 3
        assert isinstance(body["limitations"], list)
        assert len(body["limitations"]) >= 2

        # Metadata should reflect our synthetic JPEG
        meta = body["metadata"]
        assert meta["width"] == 640
        assert meta["height"] == 480
        assert meta["format"] == "JPEG"
        assert meta["has_exif"] is False

        # Provenance stub
        prov = body["provenance"]
        assert prov["c2pa_present"] is False

    @pytest.mark.asyncio
    async def test_full_pipeline_detector_unavailable(self, analyze_payload):
        """Pipeline handles None score gracefully (model unavailable)."""
        captured: dict = {}

        with (
            patch("app.detector.detect", return_value=None),
            patch("app.main.httpx.AsyncClient", _mock_httpx_client(captured)),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(
                    "/analyze",
                    json=analyze_payload,
                    headers={"Authorization": "Bearer test-secret"},
                )

        assert resp.status_code == 200
        body = captured["body"]
        assert body["ai_likelihood"] is None
        assert body["confidence"] == "low"
        assert "Unable to determine" in body["verdict_text"]

    @pytest.mark.asyncio
    async def test_rejects_missing_auth(self, analyze_payload):
        """Requests without a Bearer token get 401."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/analyze", json=analyze_payload)

        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_rejects_bad_auth(self, analyze_payload):
        """Requests with a wrong token get 403."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/analyze",
                json=analyze_payload,
                headers={"Authorization": "Bearer wrong-token"},
            )

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_report_json_round_trips(self, analyze_payload):
        """Report sent to callback is valid JSON that deserializes cleanly."""
        captured: dict = {}

        with (
            patch("app.detector.detect", return_value=50),
            patch("app.main.httpx.AsyncClient", _mock_httpx_client(captured)),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                await client.post(
                    "/analyze",
                    json=analyze_payload,
                    headers={"Authorization": "Bearer test-secret"},
                )

        # The callback body should survive a JSON round-trip without data loss
        from app.schemas import AnalysisReport

        report = AnalysisReport(**captured["body"])
        assert report.job_id == "integration-1"
        assert report.ai_likelihood == 50
        # Re-serialize and compare
        reserialized = json.loads(report.model_dump_json())
        assert reserialized["job_id"] == captured["body"]["job_id"]
        assert reserialized["ai_likelihood"] == captured["body"]["ai_likelihood"]
        assert reserialized["evidence"] == captured["body"]["evidence"]

    @pytest.mark.asyncio
    async def test_high_score_report(self, jpeg_bytes):
        """High AI score produces the expected verdict and confidence."""
        captured: dict = {}
        payload = {
            "job_id": "integration-high",
            "object_key": "uploads/integration-high",
            "image_url": _make_data_url(jpeg_bytes),
            "callback_url": "https://worker.example.com/api/internal/report",
        }

        with (
            patch("app.detector.detect", return_value=95),
            patch("app.main.httpx.AsyncClient", _mock_httpx_client(captured)),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(
                    "/analyze",
                    json=payload,
                    headers={"Authorization": "Bearer test-secret"},
                )

        assert resp.status_code == 200
        body = captured["body"]
        assert body["ai_likelihood"] == 95
        assert body["confidence"] == "high"
        assert "likely AI-generated" in body["verdict_text"]

    @pytest.mark.asyncio
    async def test_low_score_report(self, jpeg_bytes):
        """Low AI score produces an 'authentic' verdict."""
        captured: dict = {}
        payload = {
            "job_id": "integration-low",
            "object_key": "uploads/integration-low",
            "image_url": _make_data_url(jpeg_bytes),
            "callback_url": "https://worker.example.com/api/internal/report",
        }

        with (
            patch("app.detector.detect", return_value=5),
            patch("app.main.httpx.AsyncClient", _mock_httpx_client(captured)),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(
                    "/analyze",
                    json=payload,
                    headers={"Authorization": "Bearer test-secret"},
                )

        assert resp.status_code == 200
        body = captured["body"]
        assert body["ai_likelihood"] == 5
        assert "likely authentic" in body["verdict_text"]
