"""
KisanAI OS - AI Crop Growth Stage Detection milestone tests.

Covers the full detection surface: authenticated detection request,
401 unauthenticated, authorization (any authenticated user), valid /
invalid / corrupt / oversized images, safe image path handling, the
model-not-configured behavior, the no-fake-prediction guarantee, the
structured response shape, no local filesystem path leakage, and crop
context.

Uploads are isolated to a temporary directory (never the real media
directory) via the UPLOAD_DIR setting.
"""

import os
import re

import pytest

from config.settings import settings
from tests.conftest import unique_mobile

JPEG_MAGIC = b"\xff\xd8\xff\xe0"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
MAX_UPLOAD_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

STORED_NAME_PATTERN = re.compile(r"^[0-9a-f]{32}\.(jpg|png)$")


@pytest.fixture(autouse=True)
def _isolated_upload_dir(monkeypatch, tmp_path):
    upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(upload_dir))
    return upload_dir


def _jpeg_bytes():
    return JPEG_MAGIC + b"\x00" * 256


def _png_bytes():
    return PNG_MAGIC + b"\x00" * 256


def _detect(client, headers, filename, content, crop_name=None):
    files = {"file": (filename, content, "image/png")}
    data = {}
    if crop_name:
        data["crop_name"] = crop_name
    return client.post(
        "/api/growth-stage/detect",
        files=files,
        data=data,
        headers=headers,
    )


# ==========================================================
# Authentication / authorization
# ==========================================================

def test_detection_requires_auth(client):
    response = _detect(client, None, "plant.png", _png_bytes())
    assert response.status_code == 401


def test_detection_allows_any_authenticated_user(client, admin_headers, user_headers):
    """No special role is required - farmers are the intended users."""
    for headers in (admin_headers, user_headers):
        response = _detect(client, headers, "plant.png", _png_bytes())
        assert response.status_code == 200
        assert response.json()["success"] is True


# ==========================================================
# Happy path / valid images
# ==========================================================

def test_detection_valid_png(client, admin_headers, _isolated_upload_dir):
    response = _detect(client, admin_headers, "plant.png", _png_bytes())
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["status"] == "MODEL_NOT_CONFIGURED"

    files = os.listdir(_isolated_upload_dir)
    assert len(files) == 1
    assert STORED_NAME_PATTERN.match(files[0])


def test_detection_echoes_crop_context(client, admin_headers):
    response = _detect(
        client, admin_headers, "plant.png", _png_bytes(), crop_name="Wheat"
    )
    assert response.status_code == 200
    assert response.json()["crop"] == "Wheat"


def test_detection_no_crop_context_is_null(client, admin_headers):
    response = _detect(client, admin_headers, "plant.png", _png_bytes())
    assert response.json()["crop"] is None


# ==========================================================
# Model-not-configured behavior (no fake predictions)
# ==========================================================

def test_model_not_configured_status(client, admin_headers):
    body = _detect(client, admin_headers, "plant.png", _png_bytes()).json()
    assert body["status"] == "MODEL_NOT_CONFIGURED"
    assert body["message"] == (
        "Crop growth stage model is not configured"
    )


def test_no_fake_prediction(client, admin_headers):
    """'No model' must never look like 'no stage' or 'stage detected'."""
    body = _detect(client, admin_headers, "plant.png", _png_bytes()).json()
    assert body["status"] not in ("GROWTH_STAGE_DETECTED",)
    assert body["growth_stage"] is None
    assert body["confidence"] is None
    assert body["model"] is None


def test_structured_response_shape(client, admin_headers):
    body = _detect(client, admin_headers, "plant.png", _png_bytes()).json()
    assert set(body.keys()) == {
        "success",
        "status",
        "crop",
        "growth_stage",
        "confidence",
        "model",
        "message",
    }


def test_response_never_exposes_local_path(client, admin_headers):
    response = _detect(client, admin_headers, "plant.png", _png_bytes())
    assert "\\" not in response.text
    assert "/" not in response.text
    assert "media" not in response.text
    assert "C:" not in response.text
    assert "uploads" not in response.text


def test_model_path_set_but_no_loader_still_not_configured(client, admin_headers, monkeypatch):
    """Even if a model path is configured, without a loader we must not
    fabricate results."""
    monkeypatch.setattr(
        settings, "GROWTH_STAGE_MODEL_PATH", "models/whatever.pt"
    )
    body = _detect(client, admin_headers, "plant.png", _png_bytes()).json()
    assert body["status"] == "MODEL_NOT_CONFIGURED"
    assert body["growth_stage"] is None
    assert body["confidence"] is None


# ==========================================================
# Rejected images (via the existing upload layer)
# ==========================================================

def test_detection_invalid_image_400(client, admin_headers):
    response = _detect(client, admin_headers, "plant.png", b"not an image")
    assert response.status_code == 400
    assert "does not match" in response.json()["detail"]["message"]


def test_detection_oversized_image_400(client, admin_headers):
    oversized = PNG_MAGIC + b"\x00" * (MAX_UPLOAD_BYTES + 1)
    response = _detect(client, admin_headers, "big.png", oversized)
    assert response.status_code == 400
    assert "exceeds maximum size" in response.json()["detail"]["message"]