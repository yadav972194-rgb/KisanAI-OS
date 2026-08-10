"""
KisanAI OS
Upload Service

Secure image upload handling for the Image Upload milestone.

Validates actual file content via magic bytes (zero extra dependencies),
enforces a maximum size, generates collision-free stored filenames and
never trusts the client-supplied filename for storage.
"""

import os
import uuid

from config.core.logger import logger
from config.settings import settings

# Allowed formats -> detected magic-byte signature.
JPEG_MAGIC = b"\xff\xd8\xff"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

ALLOWED_EXTENSIONS = {
    "jpg": JPEG_MAGIC,
    "jpeg": JPEG_MAGIC,
    "png": PNG_MAGIC,
}

MAX_UPLOAD_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


class UploadError(Exception):
    """Image upload rejected (invalid content / size / filename)."""


class UploadService:
    """Upload Service"""

    def _reject(self, message):
        raise UploadError(message)

    def _validate_client_filename(self, filename):
        """Reject empty, hidden, path-traversal or extension-less names."""
        if not filename or filename.strip() in ("", ".", ".."):
            self._reject("Invalid filename")

        name = os.path.basename(filename.replace("\\", "/"))

        if name != filename:
            self._reject("Invalid filename")

        if ".." in name:
            self._reject("Invalid filename")

        return name

    def _extension_for(self, filename):
        """Lowercase extension from the client filename, if allowed."""
        parts = filename.rsplit(".", 1)

        if len(parts) != 2 or not parts[1]:
            self._reject("File must have a .jpg, .jpeg or .png extension")

        extension = parts[1].lower()

        if extension not in ALLOWED_EXTENSIONS:
            self._reject(
                "Unsupported file type. Allowed: JPG, JPEG, PNG"
            )

        return extension

    def _validate_content(self, data, extension):
        """Verify magic bytes and extension/content agreement."""
        if not data:
            self._reject("File is empty")

        expected_magic = ALLOWED_EXTENSIONS[extension]

        if not data.startswith(expected_magic):
            self._reject(
                "File content does not match its extension or is corrupt"
            )

        return True

    def _detected_extension(self, data):
        """Authoritative extension derived from file content."""
        if data.startswith(JPEG_MAGIC):
            return "jpg"
        if data.startswith(PNG_MAGIC):
            return "png"
        return None

    def save_image(self, filename, file):
        """Validate and store an uploaded image.

        ``file`` is a FastAPI ``UploadFile``. Returns a safe response
        dict; raises ``UploadError`` for rejected uploads.
        """
        safe_name = self._validate_client_filename(filename)
        client_extension = self._extension_for(safe_name)

        # Read via the underlying file object so this works from sync
        # (non-async) FastAPI routes; bounded so oversized files are cut
        # off before we allocate unbounded memory.
        data = file.file.read(MAX_UPLOAD_BYTES + 1)

        if len(data) > MAX_UPLOAD_BYTES:
            self._reject(
                f"File exceeds maximum size of "
                f"{settings.MAX_UPLOAD_SIZE_MB} MB"
            )

        self._validate_content(data, client_extension)

        stored_extension = self._detected_extension(data)

        if stored_extension is None:
            self._reject("Unsupported image content")

        # Never reuse the client filename: generate a random safe name.
        stored_name = f"{uuid.uuid4().hex}.{stored_extension}"

        upload_dir = settings.UPLOAD_DIR
        os.makedirs(upload_dir, exist_ok=True)

        destination = os.path.join(upload_dir, stored_name)

        # 'xb' refuses to overwrite an existing file (collision safety).
        with open(destination, "xb") as handle:
            handle.write(data)

        logger.info("Image uploaded: %s (%d bytes)", stored_name, len(data))

        return {
            "success": True,
            "message": "Image Uploaded Successfully",
            "filename": stored_name,
        }
