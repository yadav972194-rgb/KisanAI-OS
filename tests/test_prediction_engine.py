"""
KisanAI OS - AI Prediction Engine milestone tests.

Covers the full prediction surface: authenticated request, 401
unauthenticated, authorization (any authenticated user), valid input
(with and without crop/soil/weather context), missing required input,
invalid input, MODEL_NOT_CONFIGURED behavior, the no-fake-prediction /
no-fake-confidence guarantee, the structured response shape, no local
path leakage, provider replacement, provider failure handling, and the
settings-driven provider factory.
"""

import pytest

from config.settings import settings

VALID_PAYLOAD = {
    "prediction_type": "crop_yield",
    "crop_name": "Wheat",
    "soil": {
        "soil_type": "Loamy",
        "ph": 6.5,
        "moisture": 30.0,
        "nitrogen": 40,
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


def _predict(client, headers, payload):
    return client.post("/api/predictions", json=payload, headers=headers)


# ==========================================================
# Authentication / authorization
# ==========================================================

def test_prediction_requires_auth(client):
    response = _predict(client, None, VALID_PAYLOAD)
    assert response.status_code == 401


def test_prediction_allows_any_authenticated_user(client, admin_headers, user_headers):
    """No special role is required - farmers are the intended users."""
    for headers in (admin_headers, user_headers):
        response = _predict(client, headers, VALID_PAYLOAD)
        assert response.status_code == 200
        assert response.json()["success"] is True


# ==========================================================
# Valid input
# ==========================================================

def test_prediction_valid_full_context(client, admin_headers):
    response = _predict(client, admin_headers, VALID_PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["status"] == "MODEL_NOT_CONFIGURED"
    assert body["prediction_type"] == "crop_yield"


def test_prediction_minimal_input(client, admin_headers):
    """Only the required prediction_type - context fields are optional."""
    response = _predict(client, admin_headers, {"prediction_type": "soil_analysis"})
    assert response.status_code == 200
    assert response.json()["prediction_type"] == "soil_analysis"


# ==========================================================
# Missing / invalid input (controlled validation)
# ==========================================================

def test_prediction_missing_type_422(client, admin_headers):
    response = _predict(client, admin_headers, {"crop_name": "Wheat"})
    assert response.status_code == 422


def test_prediction_blank_type_422(client, admin_headers):
    response = _predict(client, admin_headers, {"prediction_type": "   "})
    assert response.status_code == 422


def test_prediction_unknown_type_422(client, admin_headers):
    response = _predict(
        client, admin_headers, {"prediction_type": "quantum_yield"}
    )
    assert response.status_code == 422


def test_prediction_invalid_soil_ph_422(client, admin_headers):
    payload = dict(VALID_PAYLOAD)
    payload["soil"] = {"ph": 42.0}
    response = _predict(client, admin_headers, payload)
    assert response.status_code == 422


def test_prediction_invalid_weather_humidity_422(client, admin_headers):
    payload = dict(VALID_PAYLOAD)
    payload["weather"] = {"humidity": 150}
    response = _predict(client, admin_headers, payload)
    assert response.status_code == 422


def test_prediction_negative_nitrogen_422(client, admin_headers):
    payload = dict(VALID_PAYLOAD)
    payload["soil"] = {"nitrogen": -5}
    response = _predict(client, admin_headers, payload)
    assert response.status_code == 422


def test_prediction_validation_error_envelope(client, admin_headers):
    response = _predict(client, admin_headers, {"crop_name": "Wheat"})
    assert response.status_code == 422
    assert response.json() == {
        "success": False,
        "message": "Validation failed",
        "code": "VALIDATION_ERROR",
    }


# ==========================================================
# MODEL_NOT_CONFIGURED behavior (no fake predictions)
# ==========================================================

def test_model_not_configured_status(client, admin_headers):
    body = _predict(client, admin_headers, VALID_PAYLOAD).json()
    assert body["status"] == "MODEL_NOT_CONFIGURED"
    assert body["message"] == "Prediction model is not configured"


def test_no_fake_prediction(client, admin_headers):
    """'No model' must never look like a real prediction."""
    body = _predict(client, admin_headers, VALID_PAYLOAD).json()
    assert body["result"] is None
    assert body["confidence"] is None
    assert body["model"] is None


def test_structured_response_shape(client, admin_headers):
    body = _predict(client, admin_headers, VALID_PAYLOAD).json()
    assert set(body.keys()) == {
        "success",
        "status",
        "prediction_type",
        "result",
        "confidence",
        "model",
        "metadata",
        "message",
    }


def test_response_never_exposes_local_path(client, admin_headers):
    response = _predict(client, admin_headers, VALID_PAYLOAD)
    assert "\\" not in response.text
    assert "C:" not in response.text
    assert "PREDICTION_MODEL_PATH" not in response.text
    assert ".env" not in response.text


def test_model_path_set_but_no_loader_still_not_configured(client, admin_headers, monkeypatch):
    """Even if a model path is configured, without a loader we must not
    fabricate predictions."""
    monkeypatch.setattr(settings, "PREDICTION_MODEL_PATH", "models/yield.pt")
    body = _predict(client, admin_headers, VALID_PAYLOAD).json()
    assert body["status"] == "MODEL_NOT_CONFIGURED"
    assert body["result"] is None
    assert body["confidence"] is None


# ==========================================================
# Provider replacement / failure handling
# ==========================================================

def test_engine_returns_fake_provider_prediction():
    """A real provider implementation can be plugged in later: the engine
    simply forwards the provider's result."""
    from config.core.providers.base import STATUS_DISEASE_DETECTED
    from config.core.providers.prediction_provider import (
        RESULT_CONFIDENCE,
        RESULT_MESSAGE,
        RESULT_METADATA,
        RESULT_MODEL,
        RESULT_RESULT,
        RESULT_STATUS,
    )
    from config.core.services.prediction_service import PredictionService

    class FakeProvider:
        def predict(self, prediction_type, context):
            assert prediction_type == "crop_yield"
            assert context["crop_name"] == "Wheat"
            assert context["soil"]["ph"] == 6.5
            return {
                RESULT_STATUS: "COMPLETE",
                RESULT_RESULT: {"yield_tons_per_hectare": 4.2},
                RESULT_CONFIDENCE: 0.88,
                RESULT_MODEL: "fake-yield-1.0",
                RESULT_METADATA: {"samples": 1200},
                RESULT_MESSAGE: "ok",
            }

    result = PredictionService(provider=FakeProvider()).predict(
        "crop_yield",
        {"crop_name": "Wheat", "soil": {"ph": 6.5}},
    )

    assert result["status"] == "COMPLETE"
    assert result["result"] == {"yield_tons_per_hectare": 4.2}
    assert result["confidence"] == 0.88
    assert result["model"] == "fake-yield-1.0"
    assert result["metadata"] == {"samples": 1200}
    assert result["prediction_type"] == "crop_yield"


def test_engine_provider_failure_raises_controlled_error():
    from config.core.services.prediction_service import (
        PredictionError,
        PredictionService,
    )

    class BrokenProvider:
        def predict(self, prediction_type, context):
            raise RuntimeError("framework exploded")

    with pytest.raises(PredictionError):
        PredictionService(provider=BrokenProvider()).predict(
            "crop_yield", {}
        )


def test_engine_does_not_fabricate_missing_context():
    """Absent context stays absent - the engine never invents values."""
    from config.core.services.prediction_service import PredictionService

    class SpyProvider:
        def __init__(self):
            self.received = None

        def predict(self, prediction_type, context):
            self.received = context
            return {"status": "MODEL_NOT_CONFIGURED"}

    spy = SpyProvider()
    PredictionService(provider=spy).predict("crop_yield", {"crop_name": "Wheat"})

    assert spy.received == {"crop_name": "Wheat"}
    assert "soil" not in spy.received
    assert "weather" not in spy.received


def test_factory_returns_unavailable_provider_when_unconfigured(monkeypatch):
    from config.core.providers import get_prediction_provider
    from config.core.providers.prediction_provider import (
        UnavailablePredictionProvider,
    )

    monkeypatch.setattr(settings, "PREDICTION_MODEL_PATH", "")
    provider = get_prediction_provider()
    assert isinstance(provider, UnavailablePredictionProvider)
