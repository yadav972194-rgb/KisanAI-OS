"""
KisanAI OS - AI Disease Detection milestone tests.

Covers the full detection surface: authenticated diagnosis request,
401 unauthenticated, authorization (any authenticated user), valid /
invalid / corrupt / oversized images, safe image path handling, the
model-not-configured behavior, the no-fake-prediction guarantee, the
structured response shape, no local filesystem path leakage, crop
context, and provider replaceability (the abstraction works without a
real ML framework).

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
        "/api/disease-detection",
        files=files,
        data=data,
        headers=headers,
    )


# ==========================================================
# Authentication / authorization
# ==========================================================

def test_detection_requires_auth(client):
    response = _detect(client, None, "leaf.png", _png_bytes())
    assert response.status_code == 401


def test_detection_allows_any_authenticated_user(client, admin_headers, user_headers):
    """No special role is required - farmers are the intended users."""
    for headers in (admin_headers, user_headers):
        response = _detect(client, headers, "leaf.png", _png_bytes())
        assert response.status_code == 200
        assert response.json()["success"] is True


# ==========================================================
# Happy path / valid images
# ==========================================================

def test_detection_valid_png(client, admin_headers, _isolated_upload_dir):
    response = _detect(client, admin_headers, "leaf.png", _png_bytes())
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["status"] == "MODEL_NOT_CONFIGURED"

    files = os.listdir(_isolated_upload_dir)
    assert len(files) == 1
    assert STORED_NAME_PATTERN.match(files[0])


def test_detection_valid_jpeg(client, user_headers, _isolated_upload_dir):
    response = _detect(client, user_headers, "leaf.jpg", _jpeg_bytes())
    assert response.status_code == 200
    assert response.json()["status"] == "MODEL_NOT_CONFIGURED"
    assert len(os.listdir(_isolated_upload_dir)) == 1


def test_detection_echoes_crop_context(client, admin_headers):
    response = _detect(
        client, admin_headers, "leaf.png", _png_bytes(), crop_name="Wheat"
    )
    assert response.status_code == 200
    assert response.json()["crop"] == "Wheat"


def test_detection_no_crop_context_is_null(client, admin_headers):
    response = _detect(client, admin_headers, "leaf.png", _png_bytes())
    assert response.json()["crop"] is None


# ==========================================================
# Model-not-configured behavior (no fake predictions)
# ==========================================================

def test_model_not_configured_status(client, admin_headers):
    body = _detect(client, admin_headers, "leaf.png", _png_bytes()).json()
    assert body["status"] == "MODEL_NOT_CONFIGURED"
    assert body["message"] == "Disease detection model is not configured"


def test_no_fake_prediction(client, admin_headers):
    """'No model' must never look like 'healthy' or 'disease detected'."""
    body = _detect(client, admin_headers, "leaf.png", _png_bytes()).json()
    assert body["status"] not in ("HEALTHY", "DISEASE_DETECTED")
    assert body["disease_name"] is None
    assert body["confidence"] is None
    assert body["model"] is None


def test_structured_response_shape(client, admin_headers):
    body = _detect(client, admin_headers, "leaf.png", _png_bytes()).json()
    assert set(body.keys()) == {
        "success",
        "status",
        "crop",
        "disease_name",
        "confidence",
        "model",
        "message",
    }


def test_response_never_exposes_local_path(client, admin_headers):
    response = _detect(client, admin_headers, "leaf.png", _png_bytes())
    assert "\\" not in response.text
    assert "/" not in response.text
    assert "media" not in response.text
    assert "C:" not in response.text
    assert "uploads" not in response.text


def test_model_path_set_but_no_loader_still_not_configured(client, admin_headers, monkeypatch):
    """Even if a model path is configured, without a loader we must not
    fabricate results."""
    monkeypatch.setattr(settings, "DISEASE_MODEL_PATH", "models/whatever.pt")
    body = _detect(client, admin_headers, "leaf.png", _png_bytes()).json()
    assert body["status"] == "MODEL_NOT_CONFIGURED"
    assert body["disease_name"] is None
    assert body["confidence"] is None


# ==========================================================
# Rejected images (via the existing upload layer)
# ==========================================================

def test_detection_invalid_image_400(client, admin_headers):
    response = _detect(client, admin_headers, "leaf.png", b"not an image")
    assert response.status_code == 400
    assert "does not match" in response.json()["detail"]["message"]


def test_detection_corrupt_image_400(client, admin_headers):
    response = _detect(client, admin_headers, "leaf.jpg", _png_bytes())
    assert response.status_code == 400


def test_detection_unsupported_type_400(client, admin_headers):
    response = _detect(client, admin_headers, "note.txt", b"hello")
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]["message"]


def test_detection_empty_file_400(client, admin_headers):
    response = _detect(client, admin_headers, "leaf.png", b"")
    assert response.status_code == 400


def test_detection_oversized_image_400(client, admin_headers):
    oversized = PNG_MAGIC + b"\x00" * (MAX_UPLOAD_BYTES + 1)
    response = _detect(client, admin_headers, "big.png", oversized)
    assert response.status_code == 400
    assert "exceeds maximum size" in response.json()["detail"]["message"]


def test_detection_path_traversal_filename_400(client, admin_headers):
    response = _detect(client, admin_headers, "../../leaf.png", _png_bytes())
    assert response.status_code == 400
    assert response.json()["detail"]["message"] == "Invalid filename"


def test_detection_rejected_files_never_stored(client, admin_headers, _isolated_upload_dir):
    _detect(client, admin_headers, "bad.png", b"garbage")
    _detect(client, admin_headers, "big.png", PNG_MAGIC + b"\x00" * (MAX_UPLOAD_BYTES + 1))
    files = os.listdir(_isolated_upload_dir) if os.path.isdir(_isolated_upload_dir) else []
    assert files == []


# ==========================================================
# Provider replaceability (abstraction works without ML framework)
# ==========================================================

def test_service_returns_fake_provider_prediction(tmp_path, monkeypatch):
    """A real provider implementation can be plugged in later: the
    service simply forwards the provider's result."""
    from config.core.providers.base import (
        RESULT_CONFIDENCE,
        RESULT_CROP,
        RESULT_DISEASE_NAME,
        RESULT_MESSAGE,
        RESULT_MODEL,
        RESULT_STATUS,
        STATUS_DISEASE_DETECTED,
    )
    from config.core.services.disease_detection_service import (
        DiseaseDetectionService,
    )

    class FakeProvider:
        def detect(self, image_path, crop_name=None):
            assert os.path.isabs(image_path)
            assert os.path.basename(image_path).endswith(".png")
            return {
                RESULT_STATUS: STATUS_DISEASE_DETECTED,
                RESULT_CROP: crop_name,
                RESULT_DISEASE_NAME: "Leaf Blight",
                RESULT_CONFIDENCE: 0.93,
                RESULT_MODEL: "fake-model-1.0",
                RESULT_MESSAGE: "ok",
            }

    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))

    class FakeUploadFile:
        def __init__(self):
            self.filename = "leaf.png"
            self._file = type("SF", (), {"read": lambda self, n: _png_bytes()})()

        @property
        def file(self):
            return self._file

    result = DiseaseDetectionService(
        provider=FakeProvider()
    ).detect(FakeUploadFile(), "Wheat")

    assert result["status"] == "DISEASE_DETECTED"
    assert result["disease_name"] == "Leaf Blight"
    assert result["confidence"] == 0.93
    assert result["model"] == "fake-model-1.0"
    assert result["crop"] == "Wheat"


def test_factory_returns_unavailable_provider_when_unconfigured(monkeypatch):
    from config.core.providers import get_disease_detection_provider
    from config.core.providers.base import UnavailableDiseaseProvider

    monkeypatch.setattr(settings, "DISEASE_MODEL_PATH", "")
    provider = get_disease_detection_provider()
    assert isinstance(provider, UnavailableDiseaseProvider)


def test_provider_failure_raises_controlled_error(tmp_path, monkeypatch):
    from config.core.services.disease_detection_service import (
        DiseaseDetectionError,
        DiseaseDetectionService,
    )

    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))

    class BrokenProvider:
        def detect(self, image_path, crop_name=None):
            raise RuntimeError("framework exploded")

    class FakeUploadFile:
        def __init__(self):
            self.filename = "leaf.png"
            self._file = type("SF", (), {"read": lambda self, n: _png_bytes()})()

        @property
        def file(self):
            return self._file

    with pytest.raises(DiseaseDetectionError):
        DiseaseDetectionService(provider=BrokenProvider()).detect(
            FakeUploadFile()
        )
