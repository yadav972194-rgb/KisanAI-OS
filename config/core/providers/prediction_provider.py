"""
KisanAI OS
Prediction Provider Base

Replaceable model-provider contract for the AI Prediction Engine.

The engine/API layer never depends on a specific ML framework: it talks
only to the ``PredictionProvider`` interface. Future providers (local,
ONNX, PyTorch, TensorFlow, remote AI) implement this interface and are
wired through ``get_prediction_provider()`` - no API changes required.
"""

from abc import ABC, abstractmethod

from config.core.logger import logger
from config.core.providers.base import STATUS_MODEL_NOT_CONFIGURED

# Stable prediction result keys.
RESULT_STATUS = "status"
RESULT_RESULT = "result"
RESULT_CONFIDENCE = "confidence"
RESULT_MODEL = "model"
RESULT_METADATA = "metadata"
RESULT_MESSAGE = "message"


class PredictionProvider(ABC):
    """Interface every prediction model provider must implement."""

    @abstractmethod
    def predict(self, prediction_type: str, context: dict) -> dict:
        """Run a prediction for ``prediction_type`` against ``context``.

        ``context`` is a validated dict (crop/soil/weather fields) built
        exclusively from API input - never filesystem paths or secrets.

        Returns a dict matching the stable result keys above.
        """


class UnavailablePredictionProvider(PredictionProvider):
    """Default provider used when no validated model is configured.

    Never fabricates a prediction: returns a controlled
    ``MODEL_NOT_CONFIGURED`` status with ``result=None`` and
    ``confidence=None`` so "no model" is never confused with any real
    prediction (healthy crop, high/low yield, fertilizer advice, ...).
    """

    model_id = "unavailable"

    def predict(self, prediction_type: str, context: dict) -> dict:
        logger.info(
            "Prediction skipped: model not configured "
            "(type=%s)",
            prediction_type,
        )
        return {
            RESULT_STATUS: STATUS_MODEL_NOT_CONFIGURED,
            RESULT_RESULT: None,
            RESULT_CONFIDENCE: None,
            RESULT_MODEL: None,
            RESULT_METADATA: None,
            RESULT_MESSAGE: "Prediction model is not configured",
        }
