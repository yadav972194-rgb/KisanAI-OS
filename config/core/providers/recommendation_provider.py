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

from abc import ABC, abstractmethod

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

# Supported recommendation categories.
CATEGORY_IRRIGATION = "irrigation"
CATEGORY_SOIL = "soil"
CATEGORY_WEATHER = "weather"
CATEGORY_CROP_CARE = "crop_care"
CATEGORY_DISEASE = "disease"


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
