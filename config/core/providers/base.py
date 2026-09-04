"""
KisanAI OS
Disease Detection Provider Base

Replaceable model-provider contract for the AI Disease Detection layer.

The business/API layer never depends on a specific ML framework: it talks
only to the ``DiseaseDetectionProvider`` interface. Swapping in a real
trained model later means implementing this interface and wiring it through
``get_disease_detection_provider()`` - no API changes required.
"""

from abc import ABC, abstractmethod

from config.core.logger import logger

# Stable prediction statuses exposed by the API.
STATUS_HEALTHY = "HEALTHY"
STATUS_DISEASE_DETECTED = "DISEASE_DETECTED"
STATUS_MODEL_NOT_CONFIGURED = "MODEL_NOT_CONFIGURED"

# Result keys -> None until a real provider is available. The keys below
# are the future-compatible shape: disease name, confidence (0-1), and the
# model/provider identifier. They must remain None when no model exists so
# "no model" is never confused with "healthy" or "disease detected".
RESULT_STATUS = "status"
RESULT_CROP = "crop"
RESULT_DISEASE_NAME = "disease_name"
RESULT_CONFIDENCE = "confidence"
RESULT_MODEL = "model"
RESULT_MESSAGE = "message"


class DiseaseDetectionProvider(ABC):
    """Interface every disease-detection model provider must implement."""

    @abstractmethod
    def detect(self, image_path: str, crop_name: str | None = None) -> dict:
        """Analyse a validated, server-stored image.

        ``image_path`` is an absolute filesystem path constructed
        server-side from ``settings.UPLOAD_DIR`` - never client input.

        Returns a dict matching the stable result keys above.
        """


class UnavailableDiseaseProvider(DiseaseDetectionProvider):
    """Default provider used when no trained model is configured.

    Never fabricates a diagnosis: returns a controlled
    ``MODEL_NOT_CONFIGURED`` status with no disease name and no
    confidence, so callers can clearly distinguish "no model" from
    "healthy" and from "disease detected".
    """

    model_id = "unavailable"

    def detect(self, image_path: str, crop_name: str | None = None) -> dict:
        logger.info(
            "Disease detection skipped: model not configured "
            "(image=%s, crop=%s)",
            image_path,
            crop_name,
        )
        return {
            RESULT_STATUS: STATUS_MODEL_NOT_CONFIGURED,
            RESULT_CROP: crop_name,
            RESULT_DISEASE_NAME: None,
            RESULT_CONFIDENCE: None,
            RESULT_MODEL: None,
            RESULT_MESSAGE: "Disease detection model is not configured",
        }
