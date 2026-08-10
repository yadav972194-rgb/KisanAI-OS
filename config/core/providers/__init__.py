"""
KisanAI OS
AI Providers Package

Exposes settings-driven provider factories. Model file paths are always
server-controlled (settings), never derived from client input.
"""

from config.core.logger import logger
from config.core.providers.base import (
    RESULT_MESSAGE,
    RESULT_STATUS,
    STATUS_MODEL_NOT_CONFIGURED,
    UnavailableDiseaseProvider,
)
from config.core.providers.prediction_provider import (
    RESULT_CONFIDENCE,
    RESULT_METADATA,
    RESULT_MODEL,
    RESULT_RESULT,
    UnavailablePredictionProvider,
)
from config.core.providers.recommendation_provider import (
    RULE_PROVIDER_ID,
    RULE_SOURCE,
    STATUS_INSUFFICIENT_DATA,
    STATUS_RECOMMENDATION_AVAILABLE,
    RuleBasedRecommendationProvider,
    UnavailableRecommendationProvider,
)
from config.settings import settings


def get_disease_detection_provider():
    """Return the configured disease-detection model provider.

    No trained model exists in the repository and no ML dependency is
    installed, so a configured model path cannot be loaded yet. Rather
    than fabricating a diagnosis, every real-loading attempt is logged
    and the safe ``MODEL_NOT_CONFIGURED`` provider is returned.
    """
    model_path = getattr(settings, "DISEASE_MODEL_PATH", "") or ""

    if not model_path.strip():
        return UnavailableDiseaseProvider()

    # A model path was configured but there is no loader implementation
    # yet (no ML framework installed, no validated model file). Never
    # guess: report unavailable so the client is not misled.
    logger.warning(
        "DISEASE_MODEL_PATH is set (%s) but no model loader is "
        "available; returning MODEL_NOT_CONFIGURED",
        model_path,
    )
    return UnavailableDiseaseProvider()


def get_prediction_provider():
    """Return the configured prediction model provider.

    No validated agricultural model exists in the repository and no ML
    dependency is installed, so a configured model path cannot be
    loaded yet. Rather than fabricating a prediction, every real-loading
    attempt is logged and the safe ``MODEL_NOT_CONFIGURED`` provider is
    returned.
    """
    model_path = getattr(settings, "PREDICTION_MODEL_PATH", "") or ""

    if not model_path.strip():
        return UnavailablePredictionProvider()

    # A model path was configured but there is no loader implementation
    # yet. Never guess: report unavailable so the client is not misled.
    logger.warning(
        "PREDICTION_MODEL_PATH is set (%s) but no model loader is "
        "available; returning MODEL_NOT_CONFIGURED",
        model_path,
    )
    return UnavailablePredictionProvider()


def get_recommendation_provider():
    """Return the configured recommendation provider.

    Default is the deterministic rule-based provider (no model needed).
    Any other configured provider requires a validated model file; when
    one is not present or cannot be loaded, the safe
    ``MODEL_NOT_CONFIGURED`` provider is returned - a fabricated
    recommendation is never produced.
    """
    provider_name = getattr(settings, "RECOMMENDATION_PROVIDER", "") or ""

    if not provider_name or provider_name == "rules":
        return RuleBasedRecommendationProvider()

    model_path = getattr(settings, "RECOMMENDATION_MODEL_PATH", "") or ""

    if not model_path.strip():
        logger.warning(
            "RECOMMENDATION_PROVIDER=%s is set but "
            "RECOMMENDATION_MODEL_PATH is empty; "
            "returning MODEL_NOT_CONFIGURED",
            provider_name,
        )
        return UnavailableRecommendationProvider()

    logger.warning(
        "RECOMMENDATION_PROVIDER=%s is set (%s) but no model loader "
        "is available; returning MODEL_NOT_CONFIGURED",
        provider_name,
        model_path,
    )
    return UnavailableRecommendationProvider()


__all__ = [
    "UnavailableDiseaseProvider",
    "UnavailablePredictionProvider",
    "UnavailableRecommendationProvider",
    "RuleBasedRecommendationProvider",
    "get_disease_detection_provider",
    "get_prediction_provider",
    "get_recommendation_provider",
    "RESULT_STATUS",
    "RESULT_MESSAGE",
    "RESULT_CONFIDENCE",
    "RESULT_METADATA",
    "RESULT_MODEL",
    "RESULT_RESULT",
    "STATUS_MODEL_NOT_CONFIGURED",
    "STATUS_INSUFFICIENT_DATA",
    "STATUS_RECOMMENDATION_AVAILABLE",
    "RULE_PROVIDER_ID",
    "RULE_SOURCE",
]
