"""
KisanAI OS
Disease Detection Provider Base

Replaceable model-provider contract for the AI Disease Detection layer.

The business/API layer never depends on a specific ML framework: it talks
only to the ``DiseaseDetectionProvider`` interface. Swapping in a real
trained model later means implementing this interface and wiring it through
``get_disease_detection_provider()`` - no API changes required.

This module also hosts the replaceable pest-detection contract
(``PestDetectionProvider`` + ``UnavailablePestProvider``) so both
image-based AI layers share the same base module and status vocabulary.
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


# ==========================================================
# Pest Detection (Phase 1.6)
# ==========================================================

# Stable pest-detection status exposed by the API.
STATUS_PEST_DETECTED = "PEST_DETECTED"

# Stable result keys.
RESULT_PEST_NAME = "pest_name"


class PestDetectionProvider(ABC):
    """Interface every pest-detection model provider must implement."""

    @abstractmethod
    def detect(self, image_path: str, crop_name: str | None = None) -> dict:
        """Analyse a validated, server-stored image.

        ``image_path`` is an absolute filesystem path constructed
        server-side from ``settings.UPLOAD_DIR`` - never client input.

        Returns a dict matching the stable result keys above.
        """


class UnavailablePestProvider(PestDetectionProvider):
    """Default provider used when no trained pest model is configured.

    Never fabricates a pest identification: returns a controlled
    ``MODEL_NOT_CONFIGURED`` status with no pest name and no confidence,
    so callers can clearly distinguish "no model" from "pest detected".
    """

    model_id = "unavailable"

    def detect(self, image_path: str, crop_name: str | None = None) -> dict:
        logger.info(
            "Pest detection skipped: model not configured "
            "(image=%s, crop=%s)",
            image_path,
            crop_name,
        )
        return {
            RESULT_STATUS: STATUS_MODEL_NOT_CONFIGURED,
            RESULT_CROP: crop_name,
            RESULT_PEST_NAME: None,
            RESULT_CONFIDENCE: None,
            RESULT_MODEL: None,
            RESULT_MESSAGE: "Pest detection model is not configured",
        }


# ==========================================================
# Weed Detection (Phase 1.8)
# ==========================================================

# Stable weed-detection status exposed by the API.
STATUS_WEED_DETECTED = "WEED_DETECTED"

# Stable result keys.
RESULT_WEED_NAME = "weed_name"


class WeedDetectionProvider(ABC):
    """Interface every weed-detection model provider must implement."""

    @abstractmethod
    def detect(self, image_path: str, crop_name: str | None = None) -> dict:
        """Analyse a validated, server-stored image.

        ``image_path`` is an absolute filesystem path constructed
        server-side from ``settings.UPLOAD_DIR`` - never client input.

        Returns a dict matching the stable result keys above.
        """


class UnavailableWeedProvider(WeedDetectionProvider):
    """Default provider used when no trained weed model is configured.

    Never fabricates a weed identification: returns a controlled
    ``MODEL_NOT_CONFIGURED`` status with no weed name and no confidence,
    so callers can clearly distinguish "no model" from "weed detected".
    """

    model_id = "unavailable"

    def detect(self, image_path: str, crop_name: str | None = None) -> dict:
        logger.info(
            "Weed detection skipped: model not configured "
            "(image=%s, crop=%s)",
            image_path,
            crop_name,
        )
        return {
            RESULT_STATUS: STATUS_MODEL_NOT_CONFIGURED,
            RESULT_CROP: crop_name,
            RESULT_WEED_NAME: None,
            RESULT_CONFIDENCE: None,
            RESULT_MODEL: None,
            RESULT_MESSAGE: "Weed detection model is not configured",
        }


# ==========================================================
# Nutrient Deficiency Detection (Phase 1.9)
# ==========================================================

# Stable nutrient-deficiency status exposed by the API.
STATUS_NUTRIENT_DEFICIENCY_DETECTED = "NUTRIENT_DEFICIENCY_DETECTED"

# Stable result keys.
RESULT_DEFICIENCY_NAME = "deficiency_name"


class NutrientDeficiencyProvider(ABC):
    """Interface every nutrient-deficiency model provider must implement."""

    @abstractmethod
    def detect(self, image_path: str, crop_name: str | None = None) -> dict:
        """Analyse a validated, server-stored image.

        ``image_path`` is an absolute filesystem path constructed
        server-side from ``settings.UPLOAD_DIR`` - never client input.

        Returns a dict matching the stable result keys above.
        """


class UnavailableNutrientDeficiencyProvider(NutrientDeficiencyProvider):
    """Default provider used when no trained nutrient-deficiency model is
    configured.

    Never fabricates a nutrient-deficiency identification: returns a
    controlled ``MODEL_NOT_CONFIGURED`` status with no deficiency name and
    no confidence, so callers can clearly distinguish "no model" from
    "nutrient deficiency detected".
    """

    model_id = "unavailable"

    def detect(self, image_path: str, crop_name: str | None = None) -> dict:
        logger.info(
            "Nutrient deficiency detection skipped: model not configured "
            "(image=%s, crop=%s)",
            image_path,
            crop_name,
        )
        return {
            RESULT_STATUS: STATUS_MODEL_NOT_CONFIGURED,
            RESULT_CROP: crop_name,
            RESULT_DEFICIENCY_NAME: None,
            RESULT_CONFIDENCE: None,
            RESULT_MODEL: None,
            RESULT_MESSAGE: (
                "Nutrient deficiency model is not configured"
            ),
        }


# ==========================================================
# Crop Water Stress Detection (Phase 1.11)
# ==========================================================

# Stable crop-water-stress status exposed by the API.
STATUS_WATER_STRESS_DETECTED = "WATER_STRESS_DETECTED"

# Stable result keys.
RESULT_STRESS_LEVEL = "stress_level"


class WaterStressProvider(ABC):
    """Interface every crop-water-stress model provider must implement."""

    @abstractmethod
    def detect(self, image_path: str, crop_name: str | None = None) -> dict:
        """Analyse a validated, server-stored image.

        ``image_path`` is an absolute filesystem path constructed
        server-side from ``settings.UPLOAD_DIR`` - never client input.

        Returns a dict matching the stable result keys above.
        """


class UnavailableWaterStressProvider(WaterStressProvider):
    """Default provider used when no trained crop-water-stress model is
    configured.

    Never fabricates a water stress level: returns a controlled
    ``MODEL_NOT_CONFIGURED`` status with no stress level and no
    confidence, so callers can clearly distinguish "no model" from
    "no stress" and from a real stress identification.
    """

    model_id = "unavailable"

    def detect(self, image_path: str, crop_name: str | None = None) -> dict:
        logger.info(
            "Crop water stress detection skipped: model not configured "
            "(image=%s, crop=%s)",
            image_path,
            crop_name,
        )
        return {
            RESULT_STATUS: STATUS_MODEL_NOT_CONFIGURED,
            RESULT_CROP: crop_name,
            RESULT_STRESS_LEVEL: None,
            RESULT_CONFIDENCE: None,
            RESULT_MODEL: None,
            RESULT_MESSAGE: "Crop water stress model is not configured",
        }


# ==========================================================
# Crop Growth Stage Detection (Phase 1.10)
# ==========================================================

# Stable crop-growth-stage status exposed by the API.
STATUS_GROWTH_STAGE_DETECTED = "GROWTH_STAGE_DETECTED"

# Stable result keys.
RESULT_GROWTH_STAGE = "growth_stage"


class GrowthStageProvider(ABC):
    """Interface every crop-growth-stage model provider must implement."""

    @abstractmethod
    def detect(self, image_path: str, crop_name: str | None = None) -> dict:
        """Analyse a validated, server-stored image.

        ``image_path`` is an absolute filesystem path constructed
        server-side from ``settings.UPLOAD_DIR`` - never client input.

        Returns a dict matching the stable result keys above.
        """


class UnavailableGrowthStageProvider(GrowthStageProvider):
    """Default provider used when no trained crop-growth-stage model is
    configured.

    Never fabricates a growth stage: returns a controlled
    ``MODEL_NOT_CONFIGURED`` status with no growth stage and no
    confidence, so callers can clearly distinguish "no model" from
    "growth stage detected".
    """

    model_id = "unavailable"

    def detect(self, image_path: str, crop_name: str | None = None) -> dict:
        logger.info(
            "Crop growth stage detection skipped: model not configured "
            "(image=%s, crop=%s)",
            image_path,
            crop_name,
        )
        return {
            RESULT_STATUS: STATUS_MODEL_NOT_CONFIGURED,
            RESULT_CROP: crop_name,
            RESULT_GROWTH_STAGE: None,
            RESULT_CONFIDENCE: None,
            RESULT_MODEL: None,
            RESULT_MESSAGE: "Crop growth stage model is not configured",
        }
