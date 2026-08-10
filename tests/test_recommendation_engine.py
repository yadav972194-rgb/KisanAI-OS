"""
KisanAI OS - Recommendation Engine milestone tests.

Covers the full recommendation surface: authenticated request, 401
unauthenticated, authorization (any authenticated user), valid context,
missing crop / soil / weather, partial missing data, unavailable AI
model, deterministic rule behavior with traceability, provider
replacement, provider failure, structured response, no fake
recommendation / confidence, no unsupported dosage, no disease-context
health claims, and no local path leakage.
"""

import re

import pytest

from config.settings import settings

VALID_PAYLOAD = {
    "crop_name": "Wheat",
    "soil": {
        "soil_type": "Loamy",
        "ph": 6.5,
        "moisture": 45,
        "nitrogen": 50,
        "phosphorus": 25,
        "potassium": 30,
    },
    "weather": {
        "temperature": 28.0,
        "humidity": 60,
        "condition": "Partly Cloudy",
        "wind_speed": 8.0,
    },
}

DOSAGE_PATTERN = re.compile(
    r"\d+\s*(kg|ha|kg/ha|l/ha|ml|l|litre|liter|g|%|percent)\b",
    re.IGNORECASE,
)


def _recommend(client, headers, payload):
    return client.post("/api/recommendations", json=payload, headers=headers)


# ==========================================================
# Authentication / authorization
# ==========================================================

def test_recommendation_requires_auth(client):
    response = _recommend(client, None, VALID_PAYLOAD)
    assert response.status_code == 401


def test_recommendation_allows_any_authenticated_user(client, admin_headers, user_headers):
    for headers in (admin_headers, user_headers):
        response = _recommend(client, headers, VALID_PAYLOAD)
        assert response.status_code == 200
        assert response.json()["success"] is True


# ==========================================================
# Valid context
# ==========================================================

def test_recommendation_valid_context(client, admin_headers):
    body = _recommend(client, admin_headers, VALID_PAYLOAD).json()
    assert body["status"] == "RECOMMENDATION_AVAILABLE"
    assert body["recommendations"]
    assert body["missing"] == []
    assert body["confidence"] is None


def test_recommendation_categories_and_traceability(client, admin_headers):
    body = _recommend(client, admin_headers, VALID_PAYLOAD).json()
    categories = {item["category"] for item in body["recommendations"]}
    assert "irrigation" in categories
    assert "soil" in categories
    assert "crop_care" in categories

    for item in body["recommendations"]:
        assert item["source"] == "deterministic-rule"
        assert item["reason"]
        assert item["text"]


def test_recommendation_structured_response_shape(client, admin_headers):
    body = _recommend(client, admin_headers, VALID_PAYLOAD).json()
    assert set(body.keys()) == {
        "success",
        "status",
        "recommendation_type",
        "recommendations",
        "warnings",
        "required_context",
        "missing",
        "reason",
        "confidence",
        "model",
        "provider",
        "message",
    }


def test_response_never_exposes_local_path(client, admin_headers):
    response = _recommend(client, admin_headers, VALID_PAYLOAD)
    assert "\\" not in response.text
    assert "C:" not in response.text
    assert "RECOMMENDATION_MODEL_PATH" not in response.text
    assert ".env" not in response.text


# ==========================================================
# Insufficient data
# ==========================================================

def test_missing_crop_is_insufficient_data(client, admin_headers):
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "crop_name"}
    body = _recommend(client, admin_headers, payload).json()
    assert body["status"] == "INSUFFICIENT_DATA"
    assert body["recommendations"] == []
    assert "crop" in body["missing"]


def test_missing_soil_is_insufficient_data(client, admin_headers):
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "soil"}
    body = _recommend(client, admin_headers, payload).json()
    assert body["status"] == "INSUFFICIENT_DATA"
    assert "soil" in body["missing"]


def test_missing_weather_is_insufficient_data(client, admin_headers):
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "weather"}
    body = _recommend(client, admin_headers, payload).json()
    assert body["status"] == "INSUFFICIENT_DATA"
    assert "weather" in body["missing"]


def test_partial_soil_is_insufficient_data(client, admin_headers):
    payload = {
        "crop_name": "Wheat",
        "soil": {"ph": 6.5},
        "weather": VALID_PAYLOAD["weather"],
    }
    body = _recommend(client, admin_headers, payload).json()
    assert body["status"] == "INSUFFICIENT_DATA"
    assert "soil.moisture" in body["missing"]
    assert "soil.nitrogen" in body["missing"]


def test_no_fake_recommendation_on_insufficient_data(client, admin_headers):
    payload = {"crop_name": "Wheat"}
    body = _recommend(client, admin_headers, payload).json()
    assert body["status"] == "INSUFFICIENT_DATA"
    assert body["recommendations"] == []
    assert body["warnings"] == []
    assert body["message"] == "Insufficient data to generate a recommendation"


# ==========================================================
# Unavailable AI model
# ==========================================================

def test_unavailable_ai_model_returns_model_not_configured(client, admin_headers, monkeypatch):
    monkeypatch.setattr(settings, "RECOMMENDATION_PROVIDER", "ai")
    monkeypatch.setattr(settings, "RECOMMENDATION_MODEL_PATH", "")
    body = _recommend(client, admin_headers, VALID_PAYLOAD).json()
    assert body["status"] == "MODEL_NOT_CONFIGURED"
    assert body["recommendations"] == []
    assert body["message"] == "Recommendation model is not configured"


def test_model_not_configured_never_looks_available(client, admin_headers, monkeypatch):
    monkeypatch.setattr(settings, "RECOMMENDATION_PROVIDER", "ai")
    monkeypatch.setattr(settings, "RECOMMENDATION_MODEL_PATH", "")
    body = _recommend(client, admin_headers, VALID_PAYLOAD).json()
    assert body["status"] != "RECOMMENDATION_AVAILABLE"
    assert body["status"] != "INSUFFICIENT_DATA"
    assert body["confidence"] is None


# ==========================================================
# Deterministic rule behavior
# ==========================================================

def _texts(body):
    return [item["text"] for item in body["recommendations"]]


def test_low_moisture_triggers_irrigation_rule(client, admin_headers):
    payload = dict(VALID_PAYLOAD)
    payload["soil"] = dict(VALID_PAYLOAD["soil"], moisture=15)
    body = _recommend(client, admin_headers, payload).json()
    texts = _texts(body)
    assert any("Irrigation may be required" in t for t in texts)
    item = next(
        i for i in body["recommendations"] if "Irrigation may be required" in i["text"]
    )
    assert item["reason"] == "soil.moisture=15 below 30 threshold"


def test_low_ph_triggers_soil_rule(client, admin_headers):
    payload = dict(VALID_PAYLOAD)
    payload["soil"] = dict(VALID_PAYLOAD["soil"], ph=4.5)
    body = _recommend(client, admin_headers, payload).json()
    texts = _texts(body)
    assert any("Soil pH is low" in t for t in texts)


def test_low_nitrogen_triggers_nutrient_rule(client, admin_headers):
    payload = dict(VALID_PAYLOAD)
    payload["soil"] = dict(VALID_PAYLOAD["soil"], nitrogen=30)
    body = _recommend(client, admin_headers, payload).json()
    assert any("Nitrogen level appears low" in t for t in _texts(body))


def test_high_temperature_triggers_weather_warning(client, admin_headers):
    payload = dict(VALID_PAYLOAD)
    payload["weather"] = dict(VALID_PAYLOAD["weather"], temperature=37.0)
    body = _recommend(client, admin_headers, payload).json()
    assert any("heat stress" in w for w in body["warnings"])


def test_rain_condition_triggers_irrigation_rule(client, admin_headers):
    payload = dict(VALID_PAYLOAD)
    payload["weather"] = dict(VALID_PAYLOAD["weather"], condition="Light Rain")
    body = _recommend(client, admin_headers, payload).json()
    assert any("Rainy conditions detected" in t for t in _texts(body))


# ==========================================================
# Disease context handling
# ==========================================================

def test_disease_context_produces_disease_guidance(client, admin_headers):
    payload = dict(VALID_PAYLOAD)
    payload["disease"] = {"name": "Leaf Rust", "severity": "High"}
    body = _recommend(client, admin_headers, payload).json()
    categories = {item["category"] for item in body["recommendations"]}
    assert "disease" in categories
    assert any("Leaf Rust" in t for t in _texts(body))
    assert any("severity is High" in w for w in body["warnings"])


def test_no_disease_context_never_claims_healthy(client, admin_headers):
    body = _recommend(client, admin_headers, VALID_PAYLOAD).json()
    text = " ".join(_texts(body)) + " ".join(body["warnings"])
    assert body["status"] != "NO_DISEASE"
    assert "no disease" not in text.lower()
    assert "healthy" not in text.lower()


def test_invalid_disease_severity_422(client, admin_headers):
    payload = dict(VALID_PAYLOAD)
    payload["disease"] = {"name": "Leaf Rust", "severity": "Catastrophic"}
    response = _recommend(client, admin_headers, payload)
    assert response.status_code == 422


# ==========================================================
# No unsupported dosage
# ==========================================================

def test_no_dosage_in_any_recommendation(client, admin_headers):
    contexts = [
        VALID_PAYLOAD,
        {"crop_name": "Wheat", "soil": dict(VALID_PAYLOAD["soil"], ph=4.5, nitrogen=30, moisture=15), "weather": VALID_PAYLOAD["weather"]},
        {"crop_name": "Maize", "soil": dict(VALID_PAYLOAD["soil"], ph=8.5, phosphorus=10, potassium=10), "weather": VALID_PAYLOAD["weather"]},
        dict(VALID_PAYLOAD, disease={"name": "Blight", "severity": "High"}),
    ]

    for payload in contexts:
        body = _recommend(client, admin_headers, payload).json()
        assert body["status"] == "RECOMMENDATION_AVAILABLE"
        for item in body["recommendations"]:
            assert not DOSAGE_PATTERN.search(item["text"]), item["text"]
        for warning in body["warnings"]:
            assert not DOSAGE_PATTERN.search(warning), warning


# ==========================================================
# Validation
# ==========================================================

def test_invalid_soil_ph_422(client, admin_headers):
    payload = dict(VALID_PAYLOAD)
    payload["soil"] = {"ph": 42.0}
    response = _recommend(client, admin_headers, payload)
    assert response.status_code == 422


def test_invalid_weather_humidity_422(client, admin_headers):
    payload = dict(VALID_PAYLOAD)
    payload["weather"] = {"humidity": 150}
    response = _recommend(client, admin_headers, payload)
    assert response.status_code == 422


# ==========================================================
# Provider replacement / failure
# ==========================================================

def test_engine_returns_fake_provider_result():
    from config.core.services.recommendation_service import (
        RecommendationService,
    )

    class FakeProvider:
        def recommend(self, context):
            assert context["crop_name"] == "Wheat"
            return {
                "status": "RECOMMENDATION_AVAILABLE",
                "recommendation_type": "general",
                "recommendations": [
                    {
                        "category": "crop_care",
                        "text": "fake provider guidance",
                        "reason": "test",
                        "source": "fake-provider",
                    }
                ],
                "warnings": [],
                "missing": [],
                "reason": None,
                "confidence": 0.75,
                "model": "fake-reco-1.0",
                "provider": "fake",
                "message": "",
            }

    result = RecommendationService(provider=FakeProvider()).recommend(
        {
            "crop_name": "Wheat",
            "soil": {"ph": 6.5, "moisture": 45, "nitrogen": 50, "phosphorus": 25, "potassium": 30},
            "weather": {"temperature": 28.0, "humidity": 60, "condition": "Clear", "wind_speed": 8.0},
        }
    )

    assert result["status"] == "RECOMMENDATION_AVAILABLE"
    assert result["recommendations"][0]["text"] == "fake provider guidance"
    assert result["provider"] == "fake"


def test_engine_provider_failure_raises_controlled_error():
    from config.core.services.recommendation_service import (
        RecommendationError,
        RecommendationService,
    )

    class BrokenProvider:
        def recommend(self, context):
            raise RuntimeError("framework exploded")

    with pytest.raises(RecommendationError):
        RecommendationService(provider=BrokenProvider()).recommend(
            {
                "crop_name": "Wheat",
                "soil": {"ph": 6.5, "moisture": 45, "nitrogen": 50, "phosphorus": 25, "potassium": 30},
                "weather": {"temperature": 28.0, "humidity": 60, "condition": "Clear", "wind_speed": 8.0},
            }
        )


def test_engine_provider_failure_api_502(client, admin_headers, monkeypatch):
    import config.core.services.recommendation_service as service_module

    class BrokenProvider:
        def recommend(self, context):
            raise RuntimeError("provider exploded")

    monkeypatch.setattr(service_module, "get_recommendation_provider", lambda: BrokenProvider())

    response = _recommend(client, admin_headers, VALID_PAYLOAD)
    assert response.status_code == 502
    assert response.json()["message"] == "Recommendation service unavailable"


def test_factory_defaults_to_rule_provider(monkeypatch):
    from config.core.providers import get_recommendation_provider
    from config.core.providers.recommendation_provider import (
        RuleBasedRecommendationProvider,
    )

    monkeypatch.setattr(settings, "RECOMMENDATION_PROVIDER", "")
    assert isinstance(get_recommendation_provider(), RuleBasedRecommendationProvider)

    monkeypatch.setattr(settings, "RECOMMENDATION_PROVIDER", "rules")
    assert isinstance(get_recommendation_provider(), RuleBasedRecommendationProvider)


def test_factory_returns_unavailable_for_unloaded_ai_provider(monkeypatch):
    from config.core.providers import get_recommendation_provider
    from config.core.providers.recommendation_provider import (
        UnavailableRecommendationProvider,
    )

    monkeypatch.setattr(settings, "RECOMMENDATION_PROVIDER", "ai")
    monkeypatch.setattr(settings, "RECOMMENDATION_MODEL_PATH", "")
    assert isinstance(
        get_recommendation_provider(), UnavailableRecommendationProvider
    )
