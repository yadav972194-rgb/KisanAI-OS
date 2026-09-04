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
    UnavailableGrowthStageProvider,
    UnavailableNutrientDeficiencyProvider,
    UnavailablePestProvider,
    UnavailableWaterStressProvider,
    UnavailableWeedProvider,
)
from config.core.providers.prediction_provider import (
    RESULT_CONFIDENCE,
    RESULT_METADATA,
    RESULT_MODEL,
    RESULT_RESULT,
    STATUS_PREDICTION_COMPLETE,
    OnnxPredictionProvider,
    UnavailablePredictionProvider,
)
from config.core.providers.recommendation_provider import (
    ONNX_PROVIDER_ID,
    ONNX_SOURCE,
    RULE_PROVIDER_ID,
    RULE_SOURCE,
    STATUS_INSUFFICIENT_DATA,
    STATUS_RECOMMENDATION_AVAILABLE,
    OnnxRecommendationProvider,
    RuleBasedRecommendationProvider,
    UnavailableRecommendationProvider,
)
from config.core.providers.otp_provider import (
    ConsoleOtpProvider,
    MockOtpProvider,
    OtpProvider,
    OtpProviderError,
    TwilioOtpProvider,
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


def get_pest_detection_provider():
    """Return the configured pest-detection model provider.

    A real provider is used when a valid ``.onnx`` model file exists at
    ``PEST_MODEL_PATH`` (with a sibling labels file, or
    ``PEST_MODEL_LABELS``). Anything else - no path, a missing file,
    an unbuildable provider - degrades safely to the
    ``MODEL_NOT_CONFIGURED`` provider: a pest identification is never
    fabricated.
    """
    model_path = (getattr(settings, "PEST_MODEL_PATH", "") or "").strip()

    if not model_path.strip():
        return UnavailablePestProvider()

    if not os.path.isfile(model_path):
        logger.warning(
            "PEST_MODEL_PATH=%s does not exist; "
            "returning MODEL_NOT_CONFIGURED",
            model_path,
        )
        return UnavailablePestProvider()

    labels_path = (
        getattr(settings, "PEST_MODEL_LABELS", "") or ""
    ).strip() or None

    try:
        from config.core.providers.pest_detection_provider import (
            OnnxPestDetectionProvider,
        )

        return OnnxPestDetectionProvider(
            model_path,
            labels_path=labels_path,
            input_size=getattr(settings, "PEST_MODEL_INPUT_SIZE", 224),
        )
    except Exception as error:
        logger.exception(
            "Failed to build pest detection provider: %s", error
        )
        return UnavailablePestProvider()


def get_weed_detection_provider():
    """Return the configured weed-detection model provider.

    A real provider is used when a valid ``.onnx`` model file exists at
    ``WEED_MODEL_PATH`` (with a sibling labels file, or
    ``WEED_MODEL_LABELS``). Anything else - no path, a missing file,
    an unbuildable provider - degrades safely to the
    ``MODEL_NOT_CONFIGURED`` provider: a weed identification is never
    fabricated.
    """
    model_path = (getattr(settings, "WEED_MODEL_PATH", "") or "").strip()

    if not model_path.strip():
        return UnavailableWeedProvider()

    if not os.path.isfile(model_path):
        logger.warning(
            "WEED_MODEL_PATH=%s does not exist; "
            "returning MODEL_NOT_CONFIGURED",
            model_path,
        )
        return UnavailableWeedProvider()

    labels_path = (
        getattr(settings, "WEED_MODEL_LABELS", "") or ""
    ).strip() or None

    try:
        from config.core.providers.weed_detection_provider import (
            OnnxWeedDetectionProvider,
        )

        return OnnxWeedDetectionProvider(
            model_path,
            labels_path=labels_path,
            input_size=getattr(settings, "WEED_MODEL_INPUT_SIZE", 224),
        )
    except Exception as error:
        logger.exception(
            "Failed to build weed detection provider: %s", error
        )
        return UnavailableWeedProvider()


def get_nutrient_deficiency_provider():
    """Return the configured nutrient-deficiency model provider.

    A real provider is used when a valid ``.onnx`` model file exists at
    ``NUTRIENT_DEFICIENCY_MODEL_PATH`` (with a sibling labels file, or
    ``NUTRIENT_DEFICIENCY_MODEL_LABELS``). Anything else - no path, a
    missing file, an unbuildable provider - degrades safely to the
    ``MODEL_NOT_CONFIGURED`` provider: a nutrient-deficiency
    identification is never fabricated.
    """
    model_path = (
        getattr(settings, "NUTRIENT_DEFICIENCY_MODEL_PATH", "") or ""
    ).strip()

    if not model_path.strip():
        return UnavailableNutrientDeficiencyProvider()

    if not os.path.isfile(model_path):
        logger.warning(
            "NUTRIENT_DEFICIENCY_MODEL_PATH=%s does not exist; "
            "returning MODEL_NOT_CONFIGURED",
            model_path,
        )
        return UnavailableNutrientDeficiencyProvider()

    labels_path = (
        getattr(settings, "NUTRIENT_DEFICIENCY_MODEL_LABELS", "") or ""
    ).strip() or None

    try:
        from config.core.providers.nutrient_deficiency_provider import (
            OnnxNutrientDeficiencyProvider,
        )

        return OnnxNutrientDeficiencyProvider(
            model_path,
            labels_path=labels_path,
            input_size=getattr(
                settings, "NUTRIENT_DEFICIENCY_MODEL_INPUT_SIZE", 224
            ),
        )
    except Exception as error:
        logger.exception(
            "Failed to build nutrient deficiency provider: %s", error
        )
        return UnavailableNutrientDeficiencyProvider()


def get_growth_stage_provider():
    """Return the configured crop-growth-stage model provider.

    A real provider is used when a valid ``.onnx`` model file exists at
    ``GROWTH_STAGE_MODEL_PATH`` (with a sibling labels file, or
    ``GROWTH_STAGE_MODEL_LABELS``). Anything else - no path, a missing
    file, an unbuildable provider - degrades safely to the
    ``MODEL_NOT_CONFIGURED`` provider: a growth stage is never
    fabricated.
    """
    model_path = (
        getattr(settings, "GROWTH_STAGE_MODEL_PATH", "") or ""
    ).strip()

    if not model_path.strip():
        return UnavailableGrowthStageProvider()

    if not os.path.isfile(model_path):
        logger.warning(
            "GROWTH_STAGE_MODEL_PATH=%s does not exist; "
            "returning MODEL_NOT_CONFIGURED",
            model_path,
        )
        return UnavailableGrowthStageProvider()

    labels_path = (
        getattr(settings, "GROWTH_STAGE_MODEL_LABELS", "") or ""
    ).strip() or None

    try:
        from config.core.providers.growth_stage_provider import (
            OnnxGrowthStageProvider,
        )

        return OnnxGrowthStageProvider(
            model_path,
            labels_path=labels_path,
            input_size=getattr(
                settings, "GROWTH_STAGE_MODEL_INPUT_SIZE", 224
            ),
        )
    except Exception as error:
        logger.exception(
            "Failed to build growth stage provider: %s", error
        )
        return UnavailableGrowthStageProvider()


def get_water_stress_provider():
    """Return the configured crop-water-stress model provider.

    A real provider is used when a valid ``.onnx`` model file exists at
    ``WATER_STRESS_MODEL_PATH`` (with a sibling labels file, or
    ``WATER_STRESS_MODEL_LABELS``). Anything else - no path, a missing
    file, an unbuildable provider - degrades safely to the
    ``MODEL_NOT_CONFIGURED`` provider: a water stress level is never
    fabricated.
    """
    model_path = (
        getattr(settings, "WATER_STRESS_MODEL_PATH", "") or ""
    ).strip()

    if not model_path.strip():
        return UnavailableWaterStressProvider()

    if not os.path.isfile(model_path):
        logger.warning(
            "WATER_STRESS_MODEL_PATH=%s does not exist; "
            "returning MODEL_NOT_CONFIGURED",
            model_path,
        )
        return UnavailableWaterStressProvider()

    labels_path = (
        getattr(settings, "WATER_STRESS_MODEL_LABELS", "") or ""
    ).strip() or None

    try:
        from config.core.providers.water_stress_provider import (
            OnnxWaterStressProvider,
        )

        return OnnxWaterStressProvider(
            model_path,
            labels_path=labels_path,
            input_size=getattr(
                settings, "WATER_STRESS_MODEL_INPUT_SIZE", 224
            ),
        )
    except Exception as error:
        logger.exception(
            "Failed to build water stress provider: %s", error
        )
        return UnavailableWaterStressProvider()


def get_prediction_provider():
    """Return the configured prediction model provider.

    A real provider is used when a valid model file exists at
    ``PREDICTION_MODEL_PATH`` (with a labels file for classification
    outputs, either ``PREDICTION_MODEL_LABELS`` or a sibling
    ``<model>.txt``). Anything else - no path, a missing file, an
    unbuildable provider - degrades safely to the ``MODEL_NOT_CONFIGURED``
    provider: a prediction is never fabricated.
    """
    model_path = getattr(settings, "PREDICTION_MODEL_PATH", "") or ""

    if not model_path.strip():
        return UnavailablePredictionProvider()

    if not os.path.isfile(model_path):
        logger.warning(
            "PREDICTION_MODEL_PATH=%s does not exist; "
            "returning MODEL_NOT_CONFIGURED",
            model_path,
        )
        return UnavailablePredictionProvider()

    labels_path = (
        getattr(settings, "PREDICTION_MODEL_LABELS", "") or ""
    ).strip() or None

    try:
        return OnnxPredictionProvider(
            model_path,
            labels_path=labels_path,
            input_size=getattr(settings, "PREDICTION_MODEL_INPUT_SIZE", 224),
        )
    except Exception as error:
        logger.exception(
            "Failed to build prediction provider: %s", error
        )
        return UnavailablePredictionProvider()


def get_recommendation_provider():
    """Return the configured recommendation provider.

    Default is the deterministic rule-based provider (no model needed).
    Any other configured provider requires a validated model file at
    ``RECOMMENDATION_MODEL_PATH`` (with a labels file for classification
    outputs, either ``RECOMMENDATION_MODEL_LABELS`` or a sibling
    ``<model>.txt``). When one is not present or cannot be loaded, the
    safe ``MODEL_NOT_CONFIGURED`` provider is returned - a fabricated
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

    if not os.path.isfile(model_path):
        logger.warning(
            "RECOMMENDATION_MODEL_PATH=%s does not exist; "
            "returning MODEL_NOT_CONFIGURED",
            model_path,
        )
        return UnavailableRecommendationProvider()

    labels_path = (
        getattr(settings, "RECOMMENDATION_MODEL_LABELS", "") or ""
    ).strip() or None

    try:
        return OnnxRecommendationProvider(
            model_path,
            labels_path=labels_path,
            input_size=getattr(settings, "RECOMMENDATION_MODEL_INPUT_SIZE", 224),
        )
    except Exception as error:
        logger.exception(
            "Failed to build recommendation provider: %s", error
        )
        return UnavailableRecommendationProvider()


def get_advisory_provider():
    """Return the configured advisory provider.

    Default is the deterministic rule-based provider (no model needed).
    Any other configured provider requires a validated model file at
    ``ADVISORY_MODEL_PATH`` (with a labels file for classification
    outputs, either ``ADVISORY_MODEL_LABELS`` or a sibling
    ``<model>.txt``). When one is not present or cannot be loaded, the
    safe ``MODEL_NOT_CONFIGURED`` provider is returned - a fabricated
    advisory is never produced.

    The provider classes live in ``config.core.services.advisory_service``
    (which imports this package at module scope), so they are imported
    lazily here to avoid a circular import at package load time.
    """
    provider_name = getattr(settings, "ADVISORY_PROVIDER", "") or ""

    if not provider_name or provider_name == "rules":
        from config.core.services.advisory_service import (
            RuleBasedAdvisoryProvider,
        )

        return RuleBasedAdvisoryProvider()

    model_path = getattr(settings, "ADVISORY_MODEL_PATH", "") or ""

    if not model_path.strip():
        logger.warning(
            "ADVISORY_PROVIDER=%s is set but "
            "ADVISORY_MODEL_PATH is empty; "
            "returning MODEL_NOT_CONFIGURED",
            provider_name,
        )
        from config.core.services.advisory_service import (
            UnavailableAdvisoryProvider,
        )

        return UnavailableAdvisoryProvider()

    if not os.path.isfile(model_path):
        logger.warning(
            "ADVISORY_MODEL_PATH=%s does not exist; "
            "returning MODEL_NOT_CONFIGURED",
            model_path,
        )
        from config.core.services.advisory_service import (
            UnavailableAdvisoryProvider,
        )

        return UnavailableAdvisoryProvider()

    labels_path = (
        getattr(settings, "ADVISORY_MODEL_LABELS", "") or ""
    ).strip() or None

    try:
        from config.core.services.advisory_service import (
            OnnxAdvisoryProvider,
        )

        return OnnxAdvisoryProvider(
            model_path,
            labels_path=labels_path,
            input_size=getattr(settings, "ADVISORY_MODEL_INPUT_SIZE", 224),
        )
    except Exception as error:
        logger.exception(
            "Failed to build advisory provider: %s", error
        )
        from config.core.services.advisory_service import (
            UnavailableAdvisoryProvider,
        )

        return UnavailableAdvisoryProvider()


def get_otp_provider():
    """Return the configured OTP delivery provider.

    Selection follows ``OTP_PROVIDER`` (default "mock" in development).
    Unknown provider names fail closed to the console provider with a
    warning rather than crashing or silently dropping codes.

    ``twilio`` activates the production gateway only when the required
    credentials are configured; missing/invalid credentials fall back to
    the console provider (safe, never crashes) and never leak the
    credential values.
    """
    provider_name = (getattr(settings, "OTP_PROVIDER", "") or "").lower()

    if provider_name == "mock":
        return MockOtpProvider()

    if provider_name == "console":
        return ConsoleOtpProvider()

    if provider_name == "twilio":
        return _build_twilio_provider()

    logger.warning(
        "OTP_PROVIDER=%s has no loader implementation; "
        "falling back to console provider",
        provider_name,
    )
    return ConsoleOtpProvider()


def _build_twilio_provider():
    """Build a Twilio OTP provider from settings, failing safely.

    Required: an Account SID + Auth Token, and a sender (Messaging
    Service SID or From number). When any is missing the console provider
    is returned with a warning - the app never crashes at startup and the
    credential values are never logged.
    """
    account_sid = (getattr(settings, "TWILIO_ACCOUNT_SID", "") or "").strip()
    auth_token = (getattr(settings, "TWILIO_AUTH_TOKEN", "") or "").strip()
    messaging_sid = (
        getattr(settings, "TWILIO_MESSAGING_SERVICE_SID", "") or ""
    ).strip()
    from_number = (getattr(settings, "TWILIO_FROM_NUMBER", "") or "").strip()

    if not (account_sid and auth_token):
        logger.warning(
            "OTP_PROVIDER=twilio but Twilio credentials are not configured; "
            "falling back to console provider"
        )
        return ConsoleOtpProvider()

    if not (messaging_sid or from_number):
        logger.warning(
            "OTP_PROVIDER=twilio but no Twilio sender is configured; "
            "falling back to console provider"
        )
        return ConsoleOtpProvider()

    return TwilioOtpProvider(
        account_sid=account_sid,
        auth_token=auth_token,
        messaging_service_sid=messaging_sid,
        from_number=from_number,
    )


__all__ = [
    "UnavailableDiseaseProvider",
    "UnavailablePestProvider",
    "UnavailableWeedProvider",
    "UnavailableNutrientDeficiencyProvider",
    "UnavailableGrowthStageProvider",
    "UnavailableWaterStressProvider",
    "OnnxPredictionProvider",
    "UnavailablePredictionProvider",
    "OnnxRecommendationProvider",
    "UnavailableRecommendationProvider",
    "RuleBasedRecommendationProvider",
    "OtpProvider",
    "OtpProviderError",
    "MockOtpProvider",
    "ConsoleOtpProvider",
    "TwilioOtpProvider",
    "get_otp_provider",
    "get_disease_detection_provider",
    "get_pest_detection_provider",
    "get_weed_detection_provider",
    "get_nutrient_deficiency_provider",
    "get_growth_stage_provider",
    "get_water_stress_provider",
    "get_prediction_provider",
    "get_recommendation_provider",
    "get_advisory_provider",
    "RESULT_STATUS",
    "RESULT_MESSAGE",
    "RESULT_CONFIDENCE",
    "RESULT_METADATA",
    "RESULT_MODEL",
    "RESULT_RESULT",
    "STATUS_MODEL_NOT_CONFIGURED",
    "STATUS_PREDICTION_COMPLETE",
    "STATUS_INSUFFICIENT_DATA",
    "STATUS_RECOMMENDATION_AVAILABLE",
    "RULE_PROVIDER_ID",
    "RULE_SOURCE",
    "ONNX_PROVIDER_ID",
    "ONNX_SOURCE",
]
