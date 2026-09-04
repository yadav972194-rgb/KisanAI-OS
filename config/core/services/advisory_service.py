"""
KisanAI OS
Advisory Service
Version: 1.1.0

Central advisory engine combining only verified agricultural context
through replaceable providers:

    Verified Agricultural Context
      -> AdvisoryService
      -> AdvisoryProvider (replaceable)
      -> structured advisory result

Safety contract:
- the default rule-based advisory is deterministic, explicit and
  traceable; every rule uses only verified inputs present in context
- an unavailable AI model returns MODEL_NOT_CONFIGURED (never confused
  with advisory-available, never fabricated)
- no fabricated advice, no confidence, no dosage guidance
"""

import os
from abc import ABC, abstractmethod
from datetime import datetime

import numpy as np

from config.core.logger import logger
from config.core.providers import get_advisory_provider
from config.core.providers.base import STATUS_MODEL_NOT_CONFIGURED

# Stable advisory statuses exposed by the API.
STATUS_ADVISORY_AVAILABLE = "ADVISORY_AVAILABLE"
STATUS_PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"

# Stable result keys.
RESULT_STATUS = "status"
RESULT_RECOMMENDATIONS = "recommendations"
RESULT_WARNINGS = "warnings"
RESULT_CONFIDENCE = "confidence"
RESULT_MODEL = "model"
RESULT_PROVIDER = "provider"
RESULT_MESSAGE = "message"

# Source identifier for deterministic rule-based guidance.
RULE_SOURCE = "deterministic-rule"
RULE_PROVIDER_ID = "rule-based"

# Source identifier for model-driven (ONNX) guidance.
ONNX_SOURCE = "onnx"
ONNX_PROVIDER_ID = "onnx"


class AdvisoryProvider(ABC):
    """Interface every advisory provider must implement."""

    @abstractmethod
    def generate(self, context: dict) -> dict:
        """Produce advisory recommendations/warnings from verified context.

        ``context`` is a validated flat dict (crop/soil/weather/disease)
        built exclusively from API input - never filesystem paths or
        secrets. Returns a dict matching the stable result keys above.
        """


class RuleBasedAdvisoryProvider(AdvisoryProvider):
    """Deterministic, explicit and traceable agricultural advisory.

    Every rule uses only verified inputs present in ``context``. No
    dosage, no product names, no guaranteed-treatment claims - the exact
    behaviour of the original KisanAI rule engine, unchanged.
    """

    provider_id = RULE_PROVIDER_ID

    def generate(self, context: dict) -> dict:
        context = context or {}
        recommendations = []
        warnings = []

        crop_name = (context.get("crop_name") or "").strip()
        soil_type = context.get("soil_type") or ""
        ph = context.get("ph")
        moisture = context.get("moisture")
        nitrogen = context.get("nitrogen")
        phosphorus = context.get("phosphorus")
        potassium = context.get("potassium")
        temperature = context.get("temperature")
        humidity = context.get("humidity")
        condition = (context.get("condition") or "").lower()
        wind_speed = context.get("wind_speed")
        disease_name = (context.get("disease_name") or "").strip()
        disease_severity = (context.get("disease_severity") or "").strip()

        # ======================================================
        # Soil Analysis
        # ======================================================

        if ph is not None and ph < 5.5:
            recommendations.append(
                "Soil pH is low. Consider applying suitable lime "
                "after proper soil testing."
            )

        elif ph is not None and ph > 8.0:
            recommendations.append(
                "Soil pH is high. Consider organic matter and "
                "appropriate soil amendments."
            )

        elif ph is not None:
            recommendations.append(
                "Soil pH is within a generally suitable range."
            )

        if moisture is not None and moisture < 30:
            recommendations.append(
                "Soil moisture is low. Irrigation may be required."
            )

        elif moisture is not None and moisture > 80:
            warnings.append(
                "Soil moisture is very high. Avoid unnecessary irrigation."
            )

        elif moisture is not None:
            recommendations.append(
                "Soil moisture is currently in a reasonable range."
            )

        # ======================================================
        # Nutrient Analysis
        # ======================================================

        if nitrogen is not None and nitrogen < 40:
            recommendations.append(
                "Nitrogen level appears low. Consider a balanced "
                "nitrogen source based on crop requirement."
            )

        if phosphorus is not None and phosphorus < 20:
            recommendations.append(
                "Phosphorus level appears low. Consider phosphorus "
                "management based on soil test results."
            )

        if potassium is not None and potassium < 20:
            recommendations.append(
                "Potassium level appears low. Consider potassium "
                "fertilization according to crop requirement."
            )

        # ======================================================
        # Weather Analysis
        # ======================================================

        if temperature is not None and temperature >= 35:
            warnings.append(
                "High temperature detected. Monitor crop for heat stress "
                "and maintain appropriate irrigation."
            )

        elif temperature is not None and temperature <= 10:
            warnings.append(
                "Low temperature detected. Monitor the crop for cold stress."
            )

        if humidity is not None and humidity >= 80:
            warnings.append(
                "High humidity may increase fungal disease risk."
            )

        if "rain" in condition:
            recommendations.append(
                "Rainy conditions detected. Avoid unnecessary irrigation "
                "and monitor field drainage."
            )

        if "cloud" in condition or "overcast" in condition:
            recommendations.append(
                "Cloudy conditions detected. Monitor crop moisture and "
                "disease development."
            )

        if wind_speed is not None and wind_speed >= 20:
            warnings.append(
                "High wind speed detected. Avoid spraying during strong winds."
            )

        # ======================================================
        # Disease Analysis
        # ======================================================

        if disease_name:
            recommendations.append(
                f"Monitor the crop for symptoms of {disease_name}."
            )

            if disease_severity.lower() == "high":
                warnings.append(
                    f"Disease severity is High for {disease_name}. "
                    "Field inspection and appropriate treatment are recommended."
                )

            elif disease_severity.lower() == "medium":
                recommendations.append(
                    f"Disease severity is Medium for {disease_name}. "
                    "Monitor affected plants closely."
                )

        # ======================================================
        # General Crop Advisory
        # ======================================================

        if crop_name:
            recommendations.append(
                f"Continue regular monitoring of {crop_name} "
                "according to its growth stage."
            )

        # ======================================================
        # Final Advisory
        # ======================================================

        if not recommendations:
            recommendations.append(
                "No major advisory generated from the supplied data."
            )

        logger.info("Rule-based advisory generated (crop=%s)", crop_name)

        return {
            RESULT_STATUS: STATUS_ADVISORY_AVAILABLE,
            RESULT_RECOMMENDATIONS: recommendations,
            RESULT_WARNINGS: warnings,
            RESULT_CONFIDENCE: None,
            RESULT_MODEL: None,
            RESULT_PROVIDER: self.provider_id,
            RESULT_MESSAGE: "",
        }


class UnavailableAdvisoryProvider(AdvisoryProvider):
    """Provider returned when an AI-based advisory provider is configured
    but no validated model can be loaded.

    Never fabricates advice: returns a controlled ``MODEL_NOT_CONFIGURED``
    status with empty recommendations and no confidence. Distinct from
    ADVISORY_AVAILABLE - an unavailable model is never presented as a
    positive agricultural result.
    """

    provider_id = "unavailable"

    def generate(self, context: dict) -> dict:
        logger.info(
            "Advisory skipped: model not configured (provider=%s)",
            self.provider_id,
        )
        return {
            RESULT_STATUS: STATUS_MODEL_NOT_CONFIGURED,
            RESULT_RECOMMENDATIONS: [],
            RESULT_WARNINGS: [],
            RESULT_CONFIDENCE: None,
            RESULT_MODEL: None,
            RESULT_PROVIDER: None,
            RESULT_MESSAGE: "Advisory model is not configured",
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


class OnnxAdvisoryProvider(AdvisoryProvider):
    """Real local advisory model backed by ONNX.

    Like the recommendation provider, input is the validated structured
    context (crop / soil / weather). Numeric context fields are extracted
    in a fixed order into a feature vector and fed to the model; no image
    decoding is involved.

    Output handling:
      - classification (more than one output class): the top class is
        reported as a single advisory recommendation string; confidence
        is the softmax probability of that class.
      - regression (single output value): the numeric value is reported
        as a single advisory recommendation string; no confidence is
        produced.

    Runtime requirements (all free / open source):
      - ``onnxruntime``: CPU inference runtime.
      - ``ADVISORY_MODEL_PATH``: a ``.onnx`` model exporting one input
        feature tensor and one output tensor.
      - a labels file (one class name per line, in the model's output
        order) - only required for classification-style outputs. Either
        ``<model>.txt`` next to the model or the ``ADVISORY_MODEL_LABELS``
        setting.

    The provider never fabricates an advisory. If the model file is
    missing/corrupt, the runtime is unavailable, the labels file is
    missing (for classification outputs) or the output shape does not
    match the labels, it returns the controlled ``MODEL_NOT_CONFIGURED``
    result so the API and the app stay honest.
    """

    # Fixed feature ordering: soil fields then weather fields, matching
    # the AdvisoryRequest schema so a model trained on this order is
    # reproducible across deployments.
    FEATURE_FIELDS = (
        "ph",
        "moisture",
        "nitrogen",
        "phosphorus",
        "potassium",
        "temperature",
        "humidity",
        "wind_speed",
    )

    provider_id = ONNX_PROVIDER_ID

    def __init__(self, model_path, labels_path=None, input_size=224):
        self.model_path = model_path
        self.labels_path = labels_path or _default_labels_path(model_path)
        # Reserved for a future image-input advisory model.
        # Feature-based advisory (structured crop/soil/weather context)
        # ignores this.
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
        failure (so generate() can answer MODEL_NOT_CONFIGURED safely),
        or None when ready."""
        if self._session is not None:
            return None
        if self._load_error is not None:
            return self._load_error

        try:
            import onnxruntime as ort
        except Exception as error:  # runtime not installed
            logger.warning(
                "onnxruntime unavailable; advisory not configured (%s)",
                error,
            )
            self._load_error = "Advisory model is not configured"
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
                        "Advisory labels file is missing or empty: "
                        "%s" % self.labels_path
                    )
                if len(self._labels) != self._num_classes:
                    return self._fail(
                        "Advisory labels count (%d) does not match "
                        "the model output (%d)"
                        % (len(self._labels), self._num_classes)
                    )

            logger.info(
                "Advisory model loaded: %s (input=%s, classes=%s)",
                self.model_path,
                self._input_shape,
                self._num_classes or "regression",
            )
            return None
        except Exception as error:  # corrupt / unsupported model
            logger.warning(
                "Failed to load advisory model %s: %s",
                self.model_path,
                error,
            )
            self._load_error = "Advisory model is not configured"
            return self._load_error

    def _fail(self, message):
        self._load_error = message
        logger.warning(message)
        return message

    def _build_features(self, context):
        """Extract a fixed-order numeric feature vector from context.

        Missing fields default to 0.0 so the tensor is always complete.
        """
        context = context or {}
        features = []
        for name in self.FEATURE_FIELDS:
            value = context.get(name)
            try:
                features.append(float(value))
            except (TypeError, ValueError):
                features.append(0.0)
        return features

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

    def generate(self, context: dict) -> dict:
        error = self._ensure_loaded()
        if error is not None:
            return {
                RESULT_STATUS: STATUS_MODEL_NOT_CONFIGURED,
                RESULT_RECOMMENDATIONS: [],
                RESULT_WARNINGS: [],
                RESULT_CONFIDENCE: None,
                RESULT_MODEL: None,
                RESULT_PROVIDER: None,
                RESULT_MESSAGE: error,
            }

        context = context or {}
        features = self._build_features(context)
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
            confidence = float(probs[top])
            text = "Model-based advisory: %s" % label
        else:
            value = float(np.asarray(raw).reshape(-1)[0])
            confidence = None
            text = "Model-based advisory value: %s" % value

        logger.info(
            "Advisory generated from model %s (confidence=%s)",
            self.model_id,
            confidence,
        )

        return {
            RESULT_STATUS: STATUS_ADVISORY_AVAILABLE,
            RESULT_RECOMMENDATIONS: [text],
            RESULT_WARNINGS: [],
            RESULT_CONFIDENCE: confidence,
            RESULT_MODEL: self.model_id,
            RESULT_PROVIDER: self.provider_id,
            RESULT_MESSAGE: "ok",
        }


class AdvisoryService:
    """KisanAI Agricultural Advisory Service"""

    def __init__(self, provider=None):
        self.service_name = "KisanAI Advisory Engine"
        self.version = "1.1.0"
        self.provider = provider

    def _get_provider(self):
        """Resolve the advisory provider per call.

        The default ``provider=None`` resolves through the settings-driven
        factory on every request so configuration changes (and tests that
        monkeypatch settings) take effect immediately, even when a
        module-level controller singleton was created at startup.
        """
        if self.provider is not None:
            return self.provider
        return get_advisory_provider()

    def generate_advisory(
        self,
        crop_name: str,
        soil_type: str,
        ph: float,
        moisture: float,
        nitrogen: int,
        phosphorus: int,
        potassium: int,
        temperature: float,
        humidity: float,
        condition: str,
        wind_speed: float,
        disease_name: str = "",
        disease_severity: str = "",
    ):
        """
        Generate basic agricultural advisory
        using crop, soil, weather and disease data.
        """

        crop_name = crop_name.strip()
        disease_name = disease_name.strip()
        disease_severity = disease_severity.strip()

        context = {
            "crop_name": crop_name,
            "soil_type": soil_type,
            "ph": ph,
            "moisture": moisture,
            "nitrogen": nitrogen,
            "phosphorus": phosphorus,
            "potassium": potassium,
            "temperature": temperature,
            "humidity": humidity,
            "condition": condition,
            "wind_speed": wind_speed,
            "disease_name": disease_name,
            "disease_severity": disease_severity,
        }

        logger.info("Advisory request: crop=%s", crop_name)

        try:
            result = self._get_provider().generate(context)
        except Exception as error:  # never leak provider internals
            logger.exception("Advisory provider failed")
            result = {
                RESULT_STATUS: STATUS_MODEL_NOT_CONFIGURED,
                RESULT_RECOMMENDATIONS: [],
                RESULT_WARNINGS: [],
                RESULT_CONFIDENCE: None,
                RESULT_MODEL: None,
                RESULT_PROVIDER: None,
                RESULT_MESSAGE: "Advisory model is not configured",
            }

        return {
            "success": True,
            "service": self.service_name,
            "version": self.version,
            "status": result.get(RESULT_STATUS, STATUS_ADVISORY_AVAILABLE),
            "crop": crop_name,
            "soil": {
                "type": soil_type,
                "ph": ph,
                "moisture": moisture,
                "nitrogen": nitrogen,
                "phosphorus": phosphorus,
                "potassium": potassium,
            },
            "weather": {
                "temperature": temperature,
                "humidity": humidity,
                "condition": condition,
                "wind_speed": wind_speed,
            },
            "disease": {
                "name": disease_name,
                "severity": disease_severity,
            },
            "recommendations": result.get(RESULT_RECOMMENDATIONS, []),
            "warnings": result.get(RESULT_WARNINGS, []),
            "confidence": result.get(RESULT_CONFIDENCE),
            "model": result.get(RESULT_MODEL),
            "provider": result.get(RESULT_PROVIDER),
            "message": result.get(RESULT_MESSAGE, ""),
            "generated_at": datetime.now().isoformat(
                timespec="seconds"
            ),
        }


# ==========================================================
# Local Test
# ==========================================================

if __name__ == "__main__":

    service = AdvisoryService()

    print("=" * 60)
    print("KisanAI Advisory Engine")
    print("=" * 60)

    result = service.generate_advisory(
        crop_name="Wheat",
        soil_type="Loamy",
        ph=6.8,
        moisture=45,
        nitrogen=50,
        phosphorus=25,
        potassium=30,
        temperature=30.3,
        humidity=81,
        condition="Overcast",
        wind_speed=6.0,
        disease_name="",
        disease_severity="",
    )

    print()
    print(result)
    print()
    print("KisanAI Advisory Service Loaded Successfully")
    print("=" * 60)
