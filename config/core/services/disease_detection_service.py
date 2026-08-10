"""
KisanAI OS
Disease Detection Service
Version: 1.0.0

Coordinates the AI disease-detection flow without depending on any ML
framework:

    Image -> UploadService validation/storage (existing layer)
          -> DiseaseDetectionService
          -> DiseaseDetectionProvider (replaceable)
          -> structured prediction result

The provider is injected so tests and future real models can swap it in
freely. When no trained model is configured the provider returns a
controlled ``MODEL_NOT_CONFIGURED`` result - never a fake diagnosis.
"""

import os

from config.core.logger import logger
from config.core.providers import get_disease_detection_provider
from config.core.providers.base import (
    RESULT_CONFIDENCE,
    RESULT_CROP,
    RESULT_DISEASE_NAME,
    RESULT_MESSAGE,
    RESULT_MODEL,
    RESULT_STATUS,
    STATUS_MODEL_NOT_CONFIGURED,
)
from config.core.services.upload_service import UploadError, UploadService
from config.settings import settings


class DiseaseDetectionError(Exception):
    """Disease detection could not be completed (provider failure)."""


class DiseaseDetectionService:
    """Disease Detection Service"""

    def __init__(self, upload_service=None, provider=None):
        self.upload_service = upload_service or UploadService()
        self.provider = provider or get_disease_detection_provider()

    def detect(self, file, crop_name=None):
        """Validate + store the image, then run the model provider.

        ``file`` is a FastAPI ``UploadFile``. Reuses the existing secure
        upload layer, so every image is content-validated (magic bytes),
        size-limited and stored under a server-controlled directory with
        a safe random name before any inference runs.

        Returns a structured dict; raises ``UploadError`` (rejected
        image) or ``DiseaseDetectionError`` (provider failure).
        """
        stored = self.upload_service.save_image(file.filename, file)
        stored_name = stored["filename"]

        # Absolute path is assembled server-side - the client only ever
        # supplied the raw bytes, never a filesystem path.
        image_path = os.path.join(settings.UPLOAD_DIR, stored_name)

        logger.info(
            "Disease detection request: stored image %s (crop=%s)",
            stored_name,
            crop_name,
        )

        try:
            result = self.provider.detect(image_path, crop_name)
        except DiseaseDetectionError:
            raise
        except Exception as error:  # never leak provider internals
            logger.exception("Disease detection provider failed")
            raise DiseaseDetectionError(
                "Disease detection service unavailable"
            ) from error

        return self._normalize(result, crop_name)

    def _normalize(self, result, crop_name):
        """Guarantee a stable, complete result shape."""
        status = result.get(RESULT_STATUS, STATUS_MODEL_NOT_CONFIGURED)
        crop = result.get(RESULT_CROP) or crop_name

        return {
            "success": True,
            "status": status,
            "crop": crop,
            "disease_name": result.get(RESULT_DISEASE_NAME),
            "confidence": result.get(RESULT_CONFIDENCE),
            "model": result.get(RESULT_MODEL),
            "message": result.get(RESULT_MESSAGE, ""),
        }
