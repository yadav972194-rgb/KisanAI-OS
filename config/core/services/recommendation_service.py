"""
KisanAI OS
Recommendation Engine Service
Version: 1.0.0

Central recommendation engine combining only verified agricultural
context through replaceable providers:

    Verified Agricultural Context
      -> input validation (Pydantic at the API layer)
      -> RecommendationEngine
      -> Rules / Provider Layer (replaceable)
      -> structured recommendation result

Safety contract:
- missing required context returns INSUFFICIENT_DATA (never guessed)
- unavailable AI model returns MODEL_NOT_CONFIGURED (never confused
  with healthy/no-disease/recommendation-available)
- no fabricated data, no fabricated confidence, no dosage advice
"""

from config.core.logger import logger
from config.core.providers import get_recommendation_provider
from config.core.providers.base import STATUS_MODEL_NOT_CONFIGURED
from config.core.providers.recommendation_provider import (
    RESULT_CONFIDENCE,
    RESULT_MESSAGE,
    RESULT_MISSING,
    RESULT_MODEL,
    RESULT_PROVIDER,
    RESULT_REASON,
    RESULT_RECOMMENDATIONS,
    RESULT_RECOMMENDATION_TYPE,
    RESULT_STATUS,
    RESULT_WARNINGS,
    STATUS_INSUFFICIENT_DATA,
)

# Required verified context. Absence of any of these (or of the listed
# sub-fields) yields INSUFFICIENT_DATA - never a guessed recommendation.
REQUIRED_CONTEXT = ["crop", "soil", "weather"]
REQUIRED_SOIL_FIELDS = ("ph", "moisture", "nitrogen", "phosphorus", "potassium")
REQUIRED_WEATHER_FIELDS = ("temperature", "humidity", "condition", "wind_speed")


class RecommendationError(Exception):
    """Recommendation could not be completed (provider failure)."""


class RecommendationService:
    """Recommendation Engine Service"""

    def __init__(self, provider=None):
        self.provider = provider or get_recommendation_provider()

    def _missing_context(self, context):
        """Identify required verified inputs that are absent."""
        missing = []

        if not context.get("crop_name"):
            missing.append("crop")

        soil = context.get("soil")

        if not isinstance(soil, dict) or not soil:
            missing.append("soil")
        else:
            for field in REQUIRED_SOIL_FIELDS:
                if soil.get(field) is None:
                    missing.append(f"soil.{field}")

        weather = context.get("weather")

        if not isinstance(weather, dict) or not weather:
            missing.append("weather")
        else:
            for field in REQUIRED_WEATHER_FIELDS:
                if weather.get(field) is None:
                    missing.append(f"weather.{field}")

        return missing

    def _insufficient(self, missing):
        return {
            "success": True,
            "status": STATUS_INSUFFICIENT_DATA,
            "recommendation_type": "general",
            "recommendations": [],
            "warnings": [],
            "required_context": list(REQUIRED_CONTEXT),
            "missing": missing,
            "reason": "Required agricultural context is missing",
            "confidence": None,
            "model": None,
            "provider": None,
            "message": "Insufficient data to generate a recommendation",
        }

    def recommend(self, data):
        """Produce a structured recommendation from verified input.

        ``data`` is a validated dict (crop/soil/weather/disease) built
        exclusively from API input. Returns a structured dict; raises
        ``RecommendationError`` on provider failure.
        """
        missing = self._missing_context(data)

        if missing:
            logger.info(
                "Recommendation skipped: insufficient data (%s)",
                ", ".join(missing),
            )
            return self._insufficient(missing)

        logger.info("Recommendation request: crop=%s", data.get("crop_name"))

        try:
            result = self.provider.recommend(data)
        except RecommendationError:
            raise
        except Exception as error:  # never leak provider internals
            logger.exception("Recommendation provider failed")
            raise RecommendationError(
                "Recommendation service unavailable"
            ) from error

        return self._normalize(result)

    def _normalize(self, result):
        """Guarantee a stable, complete result shape."""
        status = result.get(RESULT_STATUS, STATUS_MODEL_NOT_CONFIGURED)

        return {
            "success": True,
            "status": status,
            "recommendation_type": result.get(
                RESULT_RECOMMENDATION_TYPE, "general"
            ),
            "recommendations": result.get(RESULT_RECOMMENDATIONS, []),
            "warnings": result.get(RESULT_WARNINGS, []),
            "required_context": list(REQUIRED_CONTEXT),
            "missing": result.get(RESULT_MISSING, []),
            "reason": result.get(RESULT_REASON),
            "confidence": result.get(RESULT_CONFIDENCE),
            "model": result.get(RESULT_MODEL),
            "provider": result.get(RESULT_PROVIDER),
            "message": result.get(RESULT_MESSAGE, ""),
        }
