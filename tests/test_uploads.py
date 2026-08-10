"""
KisanAI OS - Image Upload milestone tests.

Covers the full secure-upload surface: authenticated admin upload of
valid JPEG/PNG, 401/403 authorization, unsupported types, fake/corrupt
images, empty and oversized files, path-traversal filenames, collision
safety, generated stored-filename safety, no local path leakage, and
upload-directory behavior.

All uploads go to an isolated temporary directory (never the real
media directory) via the UPLOAD_DIR setting.
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


def _upload(client, headers, filename, content, content_type=None):
    return client.post(
        "/api/uploads",
        files={"file": (filename, content, content_type)},
        headers=headers,
    )


# ==========================================================
# Happy path
# ==========================================================

def test_upload_valid_jpeg(client, admin_headers, _isolated_upload_dir):
    response = _upload(client, admin_headers, "photo.jpg", _jpeg_bytes())
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Image Uploaded Successfully"
    assert STORED_NAME_PATTERN.match(body["filename"])
    assert body["filename"].endswith(".jpg")

    stored_path = os.path.join(_isolated_upload_dir, body["filename"])
    assert os.path.isfile(stored_path)
    assert open(stored_path, "rb").read() == _jpeg_bytes()


def test_upload_valid_png(client, admin_headers, _isolated_upload_dir):
    response = _upload(client, admin_headers, "crop.png", _png_bytes())
    assert response.status_code == 200
    body = response.json()
    assert STORED_NAME_PATTERN.match(body["filename"])
    assert body["filename"].endswith(".png")

    stored_path = os.path.join(_isolated_upload_dir, body["filename"])
    assert os.path.isfile(stored_path)


def test_upload_jpeg_extension_alias(client, admin_headers, _isolated_upload_dir):
    response = _upload(client, admin_headers, "photo.jpeg", _jpeg_bytes())
    assert response.status_code == 200
    assert response.json()["filename"].endswith(".jpg")


# ==========================================================
# Authentication / authorization
# ==========================================================

def test_upload_requires_auth(client):
    response = _upload(client, None, "photo.png", _png_bytes())
    assert response.status_code == 401


def test_upload_non_admin_403(client, user_headers):
    response = _upload(client, user_headers, "photo.png", _png_bytes())
    assert response.status_code == 403


# ==========================================================
# Rejections
# ==========================================================

def test_upload_unsupported_extension_400(client, admin_headers):
    response = _upload(client, admin_headers, "script.py", b"print(1)")
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]["message"]


def test_upload_svg_rejected_400(client, admin_headers):
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
    response = _upload(client, admin_headers, "vector.svg", svg)
    assert response.status_code == 400


def test_upload_no_extension_400(client, admin_headers):
    response = _upload(client, admin_headers, "photo", b"data")
    assert response.status_code == 400


def test_upload_fake_image_with_png_extension_400(client, admin_headers):
    response = _upload(client, admin_headers, "fake.png", b"this is not an image")
    assert response.status_code == 400
    assert "does not match" in response.json()["detail"]["message"]


def test_upload_corrupt_image_mismatch_400(client, admin_headers):
    """PNG bytes labelled as .jpg: extension/content mismatch."""
    response = _upload(client, admin_headers, "corrupt.jpg", _png_bytes())
    assert response.status_code == 400
    assert "does not match" in response.json()["detail"]["message"]


def test_upload_empty_file_400(client, admin_headers):
    response = _upload(client, admin_headers, "empty.png", b"")
    assert response.status_code == 400
    assert response.json()["detail"]["message"] == "File is empty"


def test_upload_oversized_file_400(client, admin_headers):
    oversized = PNG_MAGIC + b"\x00" * (MAX_UPLOAD_BYTES + 1)
    response = _upload(client, admin_headers, "big.png", oversized)
    assert response.status_code == 400
    assert "exceeds maximum size" in response.json()["detail"]["message"]


# ==========================================================
# Filename / path safety
# ==========================================================

def test_upload_path_traversal_filename_rejected(client, admin_headers):
    response = _upload(client, admin_headers, "../../evil.png", _png_bytes())
    assert response.status_code == 400
    assert response.json()["detail"]["message"] == "Invalid filename"


def test_upload_backslash_traversal_rejected(client, admin_headers):
    response = _upload(client, admin_headers, "..\\..\\evil.png", _png_bytes())
    assert response.status_code == 400


def test_upload_dotdot_filename_rejected(client, admin_headers):
    response = _upload(client, admin_headers, "..", _png_bytes())
    assert response.status_code == 400


# ==========================================================
# Collision / stored-name safety
# ==========================================================

def test_duplicate_client_filename_collision_safe(client, admin_headers):
    first = _upload(client, admin_headers, "same.png", _png_bytes())
    second = _upload(client, admin_headers, "same.png", _png_bytes())

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["filename"] != second.json()["filename"]


def test_stored_filename_is_random_and_never_leaks(client, admin_headers):
    response = _upload(
        client, admin_headers, "secret-crop-field-42.png", _png_bytes()
    )
    stored = response.json()["filename"]

    assert STORED_NAME_PATTERN.match(stored)
    assert "secret-crop-field-42" not in stored
    assert "\\" not in stored
    assert "/" not in stored
    assert ".." not in stored


def test_response_never_exposes_local_path(client, admin_headers):
    response = _upload(client, admin_headers, "photo.png", _png_bytes())
    body_text = response.text
    assert "media" not in body_text
    assert "C:" not in body_text
    assert "\\" not in body_text
    assert "/" not in body_text
    assert "tmp" not in body_text


def test_upload_dir_created_and_only_valid_files_stored(
    client, admin_headers, _isolated_upload_dir
):
    _upload(client, admin_headers, "ok.png", _png_bytes())
    _upload(client, admin_headers, "bad.png", b"garbage")

    files = [f for f in os.listdir(_isolated_upload_dir)]
    assert len(files) == 1
    assert STORED_NAME_PATTERN.match(files[0])
