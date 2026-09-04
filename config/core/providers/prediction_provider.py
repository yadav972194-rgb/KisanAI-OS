"""
KisanAI OS
Prediction Provider Base

Replaceable model-provider contract for the AI Prediction Engine.

The engine/API layer never depends on a specific ML framework: it talks
only to the ``PredictionProvider`` interface. Future providers (local,
ONNX, PyTorch, TensorFlow, remote AI) implement this interface and are
wired through ``get_prediction_provider()`` - no API changes required.
"""

import os
from abc import ABC, abstractmethod

import numpy as np

from config.core.logger import logger
from config.core.providers.base import STATUS_MODEL_NOT_CONFIGURED

# Stable prediction result keys.
RESULT_STATUS = "status"
RESULT_RESULT = "result"
RESULT_CONFIDENCE = "confidence"
RESULT_MODEL = "model"
RESULT_METADATA = "metadata"
RESULT_MESSAGE = "message"

# Status returned by a real provider when a prediction is produced.
STATUS_PREDICTION_COMPLETE = "COMPLETE"


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


def _softmax(scores: np.ndarray) -> np.ndarray:
    """Stable softmax over the last axis (class scores)."""
    shifted = scores - np.max(scores, axis=-1, keepdims=True)
    exp = np.exp(shifted)
    return exp / np.sum(exp, axis=-1, keepdims=True)


def _default_labels_path(model_path):
    """Labels live next to the model: ``<model>.txt``."""
    return os.path.splitext(model_path)[0] + ".txt"


def _read_labels(labels_path):
    """Read one class name per line. None when unreadable."""
    if not labels_path or not os.path.isfile(labels_path):
        return None
    try:
        with open(labels_path, "r", encoding="utf-8") as handle:
            labels = [
                line.strip()
                for line in handle
                if line.strip()
            ]
        return labels or None
    except OSError:
        return None


class OnnxPredictionProvider(PredictionProvider):
    """Real local crop-yield / soil prediction model backed by ONNX.

    Unlike the image-based disease provider, prediction input is the
    validated structured context (crop / soil / weather). Numeric
    context fields are extracted in a fixed order into a feature vector
    and fed to the model; no image decoding is involved.

    Runtime requirements (all free / open source):
      - ``onnxruntime``: CPU inference runtime.
      - ``PREDICTION_MODEL_PATH``: a ``.onnx`` model exporting one input
        feature tensor and one output tensor.
      - a labels file (one class name per line, in the model's output
        order) - only required for classification-style outputs. Either
        ``<model>.txt`` next to the model or the
        ``PREDICTION_MODEL_LABELS`` setting.

    The provider never fabricates a prediction. If the model file is
    missing/corrupt, the runtime is unavailable, the labels file is
    missing (for classification outputs) or the output shape does not
    match the labels, it returns the controlled ``MODEL_NOT_CONFIGURED``
    result so the API and the app stay honest.
    """

    # Fixed feature ordering: soil fields then weather fields, matching
    # the PredictionRequest schema so a model trained on this order is
    # reproducible across deployments.
    FEATURE_FIELDS = (
        ("soil", "ph"),
        ("soil", "moisture"),
        ("soil", "nitrogen"),
        ("soil", "phosphorus"),
        ("soil", "potassium"),
        ("weather", "temperature"),
        ("weather", "humidity"),
        ("weather", "wind_speed"),
    )

    def __init__(self, model_path, labels_path=None, input_size=224):
        self.model_path = model_path
        self.labels_path = labels_path or _default_labels_path(model_path)
        # Reserved for a future image-input prediction model. Feature-based
        # prediction (structured crop/soil/weather context) ignores this.
        self.input_size = int(input_size or 224)
        self._session = None
        self._input_name = None
        self._input_shape = None
        self._num_classes = None
        self._labels = None
        self._load_error = None

    @property
    def model_id(self):
        return "onnx:%s" % os.path.basename(self.model_path)

    def _ensure_loaded(self):
        """Load the model + labels once. Returns an error string on
        failure (so predict() can answer MODEL_NOT_CONFIGURED safely),
        or None when ready."""
        if self._session is not None:
            return None
        if self._load_error is not None:
            return self._load_error

        try:
            import onnxruntime as ort
        except Exception as error:  # runtime not installed
            logger.warning(
                "onnxruntime unavailable; prediction not configured (%s)",
                error,
            )
            self._load_error = "Prediction model is not configured"
            return self._load_error

        try:
            self._session = ort.InferenceSession(
                self.model_path, providers=["CPUExecutionProvider"]
            )

            inputs = self._session.get_inputs()
            if not inputs:
                return self._fail("ONNX model exposes no input tensor")

            self._input_name = inputs[0].name
            self._input_shape = list(inputs[0].shape)

            outputs = self._session.get_outputs()
            out_shape = list(outputs[0].shape) if outputs else []
            self._num_classes = (
                out_shape[-1] if out_shape and out_shape[-1] else None
            )

            # Labels are only required for classification-style outputs
            # (more than one class). Regression models need no labels.
            if self._num_classes and self._num_classes > 1:
                self._labels = _read_labels(self.labels_path)
                if not self._labels:
                    return self._fail(
                        "Prediction labels file is missing or empty: "
                        "%s" % self.labels_path
                    )
                if len(self._labels) != self._num_classes:
                    return self._fail(
                        "Prediction labels count (%d) does not match "
                        "the model output (%d)"
                        % (len(self._labels), self._num_classes)
                    )

            logger.info(
                "Prediction model loaded: %s (input=%s, classes=%s)",
                self.model_path,
                self._input_shape,
                self._num_classes or "regression",
            )
            return None
        except Exception as error:  # corrupt / unsupported model
            logger.warning(
                "Failed to load prediction model %s: %s",
                self.model_path,
                error,
            )
            self._load_error = "Prediction model is not configured"
            return self._load_error

    def _fail(self, message):
        self._load_error = message
        logger.warning(message)
        return message

    def _build_features(self, context):
        """Extract a fixed-order numeric feature vector from context.

        Missing fields default to 0.0 so the tensor is always complete.
        A ``present`` mask records which fields were actually supplied
        and is returned as metadata so callers can see what was real.
        """
        soil = context.get("soil") or {}
        weather = context.get("weather") or {}
        features = []
        present = {}
        for group, name in self.FEATURE_FIELDS:
            value = (soil if group == "soil" else weather).get(name)
            present[name] = value is not None
            try:
                features.append(float(value))
            except (TypeError, ValueError):
                features.append(0.0)
        return features, present

    def _input_tensor(self, features):
        """Reshape the feature vector to the model's expected input."""
        count = len(features)
        shape = self._input_shape

        if not shape:
            return np.asarray(features, dtype=np.float32).reshape(1, -1)

        if len(shape) == 1:
            n = shape[0] if shape[0] and shape[0] > 1 else count
            padded = np.zeros(n, dtype=np.float32)
            padded[: min(count, n)] = features[:n]
            return padded

        if len(shape) == 2:
            n = shape[1] if shape[1] and shape[1] > 1 else count
            padded = np.zeros(n, dtype=np.float32)
            padded[: min(count, n)] = features[:n]
            return padded.reshape(1, n)

        # 3D+ fallback: [1, N, 1]
        return np.asarray(features, dtype=np.float32).reshape(1, count, 1)

    def predict(self, prediction_type: str, context: dict | None = None) -> dict:
        error = self._ensure_loaded()
        if error is not None:
            return {
                RESULT_STATUS: STATUS_MODEL_NOT_CONFIGURED,
                RESULT_RESULT: None,
                RESULT_CONFIDENCE: None,
                RESULT_MODEL: None,
                RESULT_METADATA: None,
                RESULT_MESSAGE: error,
            }

        context = context or {}
        features, present = self._build_features(context)
        tensor = self._input_tensor(features)

        outputs = self._session.run(None, {self._input_name: tensor})
        raw = np.asarray(outputs[0], dtype=np.float32)

        if self._num_classes and self._num_classes > 1:
            probs = _softmax(raw).reshape(-1)
            top = int(np.argmax(probs))
            label = (
                self._labels[top]
                if self._labels and top < len(self._labels)
                else "Class %d" % top
            )
            result = {"prediction": label}
            confidence = float(probs[top])
            metadata = {
                "type": prediction_type,
                "class_index": top,
                "features_used": present,
            }
        else:
            value = float(np.asarray(raw).reshape(-1)[0])
            if prediction_type == "crop_yield":
                result = {"yield_tons_per_hectare": value}
            else:
                result = {"value": value}
            confidence = None
            metadata = {
                "type": prediction_type,
                "features_used": present,
            }

        logger.info(
            "Prediction %s -> %s (model=%s)",
            prediction_type,
            result,
            self.model_id,
        )

        return {
            RESULT_STATUS: STATUS_PREDICTION_COMPLETE,
            RESULT_RESULT: result,
            RESULT_CONFIDENCE: confidence,
            RESULT_MODEL: self.model_id,
            RESULT_METADATA: metadata,
            RESULT_MESSAGE: "ok",
        }
