"""
KisanAI OS
AI Providers Package

Exposes settings-driven provider factories. Model file paths are always
server-controlled (settings), never derived from client input.
"""

import os

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
from config.core.providers.otp_provider import (
    ConsoleOtpProvider,
    MockOtpProvider,
    OtpProvider,
    OtpProviderError,
)
from config.settings import settings


def get_disease_detection_provider():
    """Return the configured disease-detection model provider.

    A real provider is used when a valid ``.onnx`` model file exists at
    ``DISEASE_MODEL_PATH`` (with a sibling labels file, or
    ``DISEASE_MODEL_LABELS``). Anything else - no path, a missing file,
    an unbuildable provider - degrades safely to the
    ``MODEL_NOT_CONFIGURED`` provider: a diagnosis is never fabricated.
    """
    model_path = (getattr(settings, "DISEASE_MODEL_PATH", "") or "").strip()

    if not model_path.strip():
        return UnavailableDiseaseProvider()

    if not os.path.isfile(model_path):
        logger.warning(
            "DISEASE_MODEL_PATH=%s does not exist; "
            "returning MODEL_NOT_CONFIGURED",
            model_path,
        )
        return UnavailableDiseaseProvider()

    labels_path = (
        getattr(settings, "DISEASE_MODEL_LABELS", "") or ""
    ).strip() or None

    try:
        from config.core.providers.disease_detection_provider import (
            OnnxDiseaseDetectionProvider,
        )

        return OnnxDiseaseDetectionProvider(
            model_path,
            labels_path=labels_path,
            input_size=getattr(settings, "DISEASE_MODEL_INPUT_SIZE", 224),
        )
    except Exception as error:
        logger.exception(
            "Failed to build disease detection provider: %s", error
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


def get_otp_provider():
    """Return the configured OTP delivery provider.

    Selection follows ``OTP_PROVIDER`` (default "mock" in development).
    Unknown provider names fail closed to the console provider with a
    warning rather than crashing or silently dropping codes.
    """
    provider_name = (getattr(settings, "OTP_PROVIDER", "") or "").lower()

    if provider_name == "mock":
        return MockOtpProvider()

    if provider_name == "console":
        return ConsoleOtpProvider()

    logger.warning(
        "OTP_PROVIDER=%s has no loader implementation; "
        "falling back to console provider",
        provider_name,
    )
    return ConsoleOtpProvider()


__all__ = [
    "UnavailableDiseaseProvider",
    "UnavailablePredictionProvider",
    "UnavailableRecommendationProvider",
    "RuleBasedRecommendationProvider",
    "OtpProvider",
    "OtpProviderError",
    "MockOtpProvider",
    "ConsoleOtpProvider",
    "get_otp_provider",
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
