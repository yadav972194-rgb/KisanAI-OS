"""
KisanAI OS
Recommendation Provider Base

Replaceable provider contract for the Recommendation Engine.

The engine/API layer never depends on one AI vendor, ML framework,
database or external provider: it talks only to the
``RecommendationProvider`` interface. Future providers may be
deterministic rules, validated local/ONNX/PyTorch/TensorFlow models, a
remote AI service, or a government/agricultural data source.

Rule-based recommendations are explicit, deterministic, testable and
traceable: every item carries a ``category``, ``text``, a ``reason``
citing the verified input + threshold that produced it, and the source
identifier ``deterministic-rule``. No pesticide/fertilizer dosage is
ever emitted - no dosage logic exists here by design.
"""

import os
from abc import ABC, abstractmethod

import numpy as np

from config.core.logger import logger
from config.core.providers.base import STATUS_MODEL_NOT_CONFIGURED

# Stable recommendation statuses exposed by the API.
STATUS_RECOMMENDATION_AVAILABLE = "RECOMMENDATION_AVAILABLE"
STATUS_INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
STATUS_PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"

# Stable result keys.
RESULT_STATUS = "status"
RESULT_RECOMMENDATION_TYPE = "recommendation_type"
RESULT_RECOMMENDATIONS = "recommendations"
RESULT_WARNINGS = "warnings"
RESULT_REQUIRED_CONTEXT = "required_context"
RESULT_MISSING = "missing"
RESULT_REASON = "reason"
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

# Supported recommendation categories.
CATEGORY_IRRIGATION = "irrigation"
CATEGORY_SOIL = "soil"
CATEGORY_WEATHER = "weather"
CATEGORY_CROP_CARE = "crop_care"
CATEGORY_DISEASE = "disease"

# Category set used to map a model label to a known recommendation
# category; unknown labels fall back to general crop-care guidance.
_RECOMMENDATION_CATEGORIES = {
    CATEGORY_IRRIGATION,
    CATEGORY_SOIL,
    CATEGORY_WEATHER,
    CATEGORY_CROP_CARE,
    CATEGORY_DISEASE,
}


class RecommendationProvider(ABC):
    """Interface every recommendation provider must implement."""

    @abstractmethod
    def recommend(self, context: dict) -> dict:
        """Produce recommendations from a verified agricultural context.

        ``context`` is a validated dict (crop/soil/weather/disease)
        built exclusively from API input - never filesystem paths or
        secrets. Returns a dict matching the stable result keys above.
        """


class RuleBasedRecommendationProvider(RecommendationProvider):
    """Deterministic, explicit and traceable agricultural guidance.

    Every rule uses only verified inputs present in ``context`` and
    records a ``reason`` (input + threshold) for traceability. No
    dosage, no product names, no guaranteed-treatment claims. Missing
    context is never guessed - the engine reports INSUFFICIENT_DATA
    before calling this provider.
    """

    provider_id = RULE_PROVIDER_ID

    def recommend(self, context: dict) -> dict:
        recommendations = []
        warnings = []

        crop_name = context.get("crop_name") or ""
        soil = context.get("soil") or {}
        weather = context.get("weather") or {}
        disease = context.get("disease") or {}

        ph = soil.get("ph")
        moisture = soil.get("moisture")
        nitrogen = soil.get("nitrogen")
        phosphorus = soil.get("phosphorus")
        potassium = soil.get("potassium")

        temperature = weather.get("temperature")
        humidity = weather.get("humidity")
        condition = (weather.get("condition") or "").lower()
        wind_speed = weather.get("wind_speed")

        # ======================================================
        # Irrigation guidance
        # ======================================================

        if moisture is not None and moisture < 30:
            recommendations.append(self._item(
                CATEGORY_IRRIGATION,
                "Soil moisture is low. Irrigation may be required - "
                "verify soil moisture at the field before irrigating.",
                f"soil.moisture={self._fmt(moisture)} below 30 threshold",
            ))
        elif moisture is not None and moisture > 80:
            warnings.append(
                "Soil moisture is very high. Avoid unnecessary irrigation."
            )
        elif moisture is not None:
            recommendations.append(self._item(
                CATEGORY_IRRIGATION,
                "Soil moisture is currently in a reasonable range.",
                f"soil.moisture={self._fmt(moisture)} between 30 and 80",
            ))

        if "rain" in condition:
            recommendations.append(self._item(
                CATEGORY_IRRIGATION,
                "Rainy conditions detected. Avoid unnecessary irrigation "
                "and monitor field drainage.",
                f"weather.condition contains 'rain'",
            ))

        # ======================================================
        # Soil-related guidance
        # ======================================================

        if ph is not None and ph < 5.5:
            recommendations.append(self._item(
                CATEGORY_SOIL,
                "Soil pH is low. Consider applying suitable lime only "
                "after proper soil testing.",
                f"soil.ph={self._fmt(ph)} below 5.5 threshold",
            ))
        elif ph is not None and ph > 8.0:
            recommendations.append(self._item(
                CATEGORY_SOIL,
                "Soil pH is high. Consider organic matter and appropriate "
                "soil amendments based on soil testing.",
                f"soil.ph={self._fmt(ph)} above 8.0 threshold",
            ))
        elif ph is not None:
            recommendations.append(self._item(
                CATEGORY_SOIL,
                "Soil pH is within a generally suitable range.",
                f"soil.ph={self._fmt(ph)} between 5.5 and 8.0",
            ))

        if nitrogen is not None and nitrogen < 40:
            recommendations.append(self._item(
                CATEGORY_SOIL,
                "Nitrogen level appears low. Consider a balanced nitrogen "
                "source according to the crop requirement.",
                f"soil.nitrogen={self._fmt(nitrogen)} below 40 threshold",
            ))

        if phosphorus is not None and phosphorus < 20:
            recommendations.append(self._item(
                CATEGORY_SOIL,
                "Phosphorus level appears low. Consider phosphorus "
                "management based on soil test results.",
                f"soil.phosphorus={self._fmt(phosphorus)} below 20 threshold",
            ))

        if potassium is not None and potassium < 20:
            recommendations.append(self._item(
                CATEGORY_SOIL,
                "Potassium level appears low. Consider potassium "
                "management according to the crop requirement.",
                f"soil.potassium={self._fmt(potassium)} below 20 threshold",
            ))

        # ======================================================
        # Weather-related precaution
        # ======================================================

        if temperature is not None and temperature >= 35:
            warnings.append(
                "High temperature detected. Monitor the crop for heat "
                "stress and maintain appropriate irrigation."
            )

        elif temperature is not None and temperature <= 10:
            warnings.append(
                "Low temperature detected. Monitor the crop for cold stress."
            )

        if humidity is not None and humidity >= 80:
            warnings.append(
                "High humidity may increase fungal disease risk."
            )

        if "cloud" in condition or "overcast" in condition:
            recommendations.append(self._item(
                CATEGORY_WEATHER,
                "Cloudy conditions detected. Monitor crop moisture and "
                "disease development.",
                f"weather.condition contains 'cloud'/'overcast'",
            ))

        if wind_speed is not None and wind_speed >= 20:
            warnings.append(
                "High wind speed detected. Avoid spraying during strong winds."
            )

        # ======================================================
        # Disease-related next step (only from provided context)
        # ======================================================

        disease_name = (disease.get("name") or "").strip()
        disease_severity = (disease.get("severity") or "").strip()

        if disease_name:
            recommendations.append(self._item(
                CATEGORY_DISEASE,
                f"Monitor the crop for symptoms of {disease_name}.",
                "disease context provided in request",
            ))

            if disease_severity.lower() == "high":
                warnings.append(
                    f"Disease severity is High for {disease_name}. "
                    "Field inspection and appropriate treatment are "
                    "recommended."
                )
            elif disease_severity.lower() == "medium":
                recommendations.append(self._item(
                    CATEGORY_DISEASE,
                    f"Disease severity is Medium for {disease_name}. "
                    "Monitor affected plants closely.",
                    "disease.severity is medium",
                ))

        # ======================================================
        # General crop-care guidance
        # ======================================================

        if crop_name:
            recommendations.append(self._item(
                CATEGORY_CROP_CARE,
                f"Continue regular monitoring of {crop_name} according to "
                "its growth stage.",
                "crop context provided in request",
            ))

        if not recommendations:
            recommendations.append(self._item(
                CATEGORY_CROP_CARE,
                "No major recommendation generated from the supplied "
                "verified data.",
                "no rule thresholds matched",
            ))

        logger.info("Rule-based recommendation generated")

        return {
            RESULT_STATUS: STATUS_RECOMMENDATION_AVAILABLE,
            RESULT_RECOMMENDATION_TYPE: "general",
            RESULT_RECOMMENDATIONS: recommendations,
            RESULT_WARNINGS: warnings,
            RESULT_MISSING: [],
            RESULT_REASON: None,
            RESULT_CONFIDENCE: None,
            RESULT_MODEL: None,
            RESULT_PROVIDER: self.provider_id,
            RESULT_MESSAGE: "",
        }

    @staticmethod
    def _fmt(value):
        """Render a numeric threshold value without trailing '.0'."""
        return f"{value:g}"

    @staticmethod
    def _item(category, text, reason):
        """Build a traceable recommendation item."""
        return {
            "category": category,
            "text": text,
            "reason": reason,
            "source": RULE_SOURCE,
        }


class UnavailableRecommendationProvider(RecommendationProvider):
    """Provider returned when an AI-based recommendation provider is
    configured but no validated model can be loaded.

    Never fabricates a recommendation: returns a controlled
    ``MODEL_NOT_CONFIGURED`` status with empty recommendations and no
    confidence. Distinct from RECOMMENDATION_AVAILABLE and from
    INSUFFICIENT_DATA - an unavailable model is never presented as a
    positive agricultural result.
    """

    provider_id = "unavailable"

    def recommend(self, context: dict) -> dict:
        logger.info(
            "Recommendation skipped: model not configured "
            "(provider=%s)",
            self.provider_id,
        )
        return {
            RESULT_STATUS: STATUS_MODEL_NOT_CONFIGURED,
            RESULT_RECOMMENDATION_TYPE: "general",
            RESULT_RECOMMENDATIONS: [],
            RESULT_WARNINGS: [],
            RESULT_MISSING: [],
            RESULT_REASON: None,
            RESULT_CONFIDENCE: None,
            RESULT_MODEL: None,
            RESULT_PROVIDER: None,
            RESULT_MESSAGE: "Recommendation model is not configured",
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


class OnnxRecommendationProvider(RecommendationProvider):
    """Real local recommendation model backed by ONNX.

    Like the prediction provider, input is the validated structured
    context (crop / soil / weather). Numeric context fields are extracted
    in a fixed order into a feature vector and fed to the model; no image
    decoding is involved.

    Output handling:
      - classification (more than one output class): the top class is
        mapped to a single traceable recommendation item; confidence is
        the softmax probability of that class.
      - regression (single output value): the numeric value is reported
        as a general crop-care item; no confidence is produced.

    Runtime requirements (all free / open source):
      - ``onnxruntime``: CPU inference runtime.
      - ``RECOMMENDATION_MODEL_PATH``: a ``.onnx`` model exporting one
        input feature tensor and one output tensor.
      - a labels file (one class name per line, in the model's output
        order) - only required for classification-style outputs. Either
        ``<model>.txt`` next to the model or the
        ``RECOMMENDATION_MODEL_LABELS`` setting.

    The provider never fabricates a recommendation. If the model file is
    missing/corrupt, the runtime is unavailable, the labels file is
    missing (for classification outputs) or the output shape does not
    match the labels, it returns the controlled ``MODEL_NOT_CONFIGURED``
    result so the API and the app stay honest.
    """

    # Fixed feature ordering: soil fields then weather fields, matching
    # the RecommendationRequest schema so a model trained on this order
    # is reproducible across deployments.
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

    provider_id = ONNX_PROVIDER_ID

    def __init__(self, model_path, labels_path=None, input_size=224):
        self.model_path = model_path
        self.labels_path = labels_path or _default_labels_path(model_path)
        # Reserved for a future image-input recommendation model.
        # Feature-based recommendation (structured crop/soil/weather
        # context) ignores this.
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
        failure (so recommend() can answer MODEL_NOT_CONFIGURED safely),
        or None when ready."""
        if self._session is not None:
            return None
        if self._load_error is not None:
            return self._load_error

        try:
            import onnxruntime as ort
        except Exception as error:  # runtime not installed
            logger.warning(
                "onnxruntime unavailable; recommendation not configured (%s)",
                error,
            )
            self._load_error = "Recommendation model is not configured"
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
                        "Recommendation labels file is missing or empty: "
                        "%s" % self.labels_path
                    )
                if len(self._labels) != self._num_classes:
                    return self._fail(
                        "Recommendation labels count (%d) does not match "
                        "the model output (%d)"
                        % (len(self._labels), self._num_classes)
                    )

            logger.info(
                "Recommendation model loaded: %s (input=%s, classes=%s)",
                self.model_path,
                self._input_shape,
                self._num_classes or "regression",
            )
            return None
        except Exception as error:  # corrupt / unsupported model
            logger.warning(
                "Failed to load recommendation model %s: %s",
                self.model_path,
                error,
            )
            self._load_error = "Recommendation model is not configured"
            return self._load_error

    def _fail(self, message):
        self._load_error = message
        logger.warning(message)
        return message

    def _build_features(self, context):
        """Extract a fixed-order numeric feature vector from context.

        Missing fields default to 0.0 so the tensor is always complete.
        """
        soil = context.get("soil") or {}
        weather = context.get("weather") or {}
        features = []
        for group, name in self.FEATURE_FIELDS:
            value = (soil if group == "soil" else weather).get(name)
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

    @staticmethod
    def _category_for_label(label):
        """Map a model label to a known recommendation category when
        possible; unknown labels fall back to general crop care."""
        normalized = (label or "").strip().lower()
        if normalized in _RECOMMENDATION_CATEGORIES:
            return normalized
        return CATEGORY_CROP_CARE

    def recommend(self, context: dict) -> dict:
        error = self._ensure_loaded()
        if error is not None:
            return {
                RESULT_STATUS: STATUS_MODEL_NOT_CONFIGURED,
                RESULT_RECOMMENDATION_TYPE: "general",
                RESULT_RECOMMENDATIONS: [],
                RESULT_WARNINGS: [],
                RESULT_MISSING: [],
                RESULT_REASON: None,
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
            item = {
                "category": self._category_for_label(label),
                "text": "Model-based recommendation: %s" % label,
                "reason": "onnx model %s classified context as '%s'"
                % (self.model_id, label),
                "source": ONNX_SOURCE,
            }
        else:
            value = float(np.asarray(raw).reshape(-1)[0])
            confidence = None
            item = {
                "category": CATEGORY_CROP_CARE,
                "text": "Model-based recommendation value: %s" % value,
                "reason": "onnx model %s produced value %s"
                % (self.model_id, value),
                "source": ONNX_SOURCE,
            }

        logger.info(
            "Recommendation generated from model %s (confidence=%s)",
            self.model_id,
            confidence,
        )

        return {
            RESULT_STATUS: STATUS_RECOMMENDATION_AVAILABLE,
            RESULT_RECOMMENDATION_TYPE: "general",
            RESULT_RECOMMENDATIONS: [item],
            RESULT_WARNINGS: [],
            RESULT_MISSING: [],
            RESULT_REASON: None,
            RESULT_CONFIDENCE: confidence,
            RESULT_MODEL: self.model_id,
            RESULT_PROVIDER: self.provider_id,
            RESULT_MESSAGE: "ok",
        }
