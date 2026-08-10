"""
KisanAI OS
Prediction Engine Service
Version: 1.0.0

Central prediction engine coordinating structured agricultural input
through replaceable model providers:

    Input Data
      -> validation (Pydantic schema at the API layer)
      -> PredictionEngine
      -> PredictionProvider (replaceable: local/ONNX/PyTorch/TF/future)
      -> structured prediction result

The provider is injected so tests and future real models swap it in
freely. When no validated model is configured the provider returns a
controlled ``MODEL_NOT_CONFIGURED`` result - never a fake prediction or
a fabricated confidence value.
"""

from config.core.logger import logger
from config.core.providers import get_prediction_provider
from config.core.providers.base import STATUS_MODEL_NOT_CONFIGURED
from config.core.providers.prediction_provider import (
    RESULT_CONFIDENCE,
    RESULT_MESSAGE,
    RESULT_METADATA,
    RESULT_MODEL,
    RESULT_RESULT,
    RESULT_STATUS,
)


class PredictionError(Exception):
    """Prediction could not be completed (provider failure)."""


class PredictionService:
    """Prediction Engine Service"""

    def __init__(self, provider=None):
        self.provider = provider or get_prediction_provider()

    def predict(self, prediction_type, context=None):
        """Run a prediction through the configured model provider.

        ``context`` is a validated dict built from API input (crop /
        soil / weather fields). Returns a structured dict; raises
        ``PredictionError`` on provider failure. Missing data is never
        fabricated - absent fields stay absent in ``context``.
        """
        context = context or {}

        logger.info(
            "Prediction request: type=%s",
            prediction_type,
        )

        try:
            result = self.provider.predict(prediction_type, context)
        except PredictionError:
            raise
        except Exception as error:  # never leak provider internals
            logger.exception("Prediction provider failed")
            raise PredictionError(
                "Prediction service unavailable"
            ) from error

        return self._normalize(result, prediction_type)

    def _normalize(self, result, prediction_type):
        """Guarantee a stable, complete result shape."""
        status = result.get(RESULT_STATUS, STATUS_MODEL_NOT_CONFIGURED)

        return {
            "success": True,
            "status": status,
            "prediction_type": prediction_type,
            "result": result.get(RESULT_RESULT),
            "confidence": result.get(RESULT_CONFIDENCE),
            "model": result.get(RESULT_MODEL),
            "metadata": result.get(RESULT_METADATA),
            "message": result.get(RESULT_MESSAGE, ""),
        }
