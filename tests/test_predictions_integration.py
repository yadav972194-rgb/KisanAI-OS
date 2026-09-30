"""
KisanAI OS - Phase 1.14: Predictions API integration tests.

Exercise the public ``POST /api/predictions`` endpoint end-to-end through
the real FastAPI routing/validation/engine stack (TestClient), exactly as a
mobile client would: authentication, structured input, the controlled
``MODEL_NOT_CONFIGURED`` response, validation envelopes, and response
hygiene. No internals are monkeypatched here - that is the milestone test
suite's job.
"""

FULL_PAYLOAD = {
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

def test_unauthenticated_request_is_rejected(client):
    response = _predict(client, None, FULL_PAYLOAD)
    assert response.status_code == 401
    body = response.json()
    assert body["detail"]["success"] is False
    assert body["detail"]["code"] == "SESSION_EXPIRED"


def test_any_authenticated_user_can_predict(client, admin_headers, user_headers):
    for headers in (admin_headers, user_headers):
        response = _predict(client, headers, FULL_PAYLOAD)
        assert response.status_code == 200
        assert response.json()["success"] is True


# ==========================================================
# Request -> response lifecycle
# ==========================================================

def test_full_context_returns_controlled_model_not_configured(
    client, admin_headers
):
    body = _predict(client, admin_headers, FULL_PAYLOAD).json()
    assert body["success"] is True
    assert body["status"] == "MODEL_NOT_CONFIGURED"
    assert body["prediction_type"] == "crop_yield"
    assert body["result"] is None
    assert body["confidence"] is None
    assert body["model"] is None
    assert body["message"] == "Prediction model is not configured"


def test_minimal_input_only_requires_prediction_type(client, admin_headers):
    body = _predict(
        client, admin_headers, {"prediction_type": "soil_analysis"}
    ).json()
    assert body["success"] is True
    assert body["prediction_type"] == "soil_analysis"
    assert body["status"] == "MODEL_NOT_CONFIGURED"


def test_stable_response_shape(client, admin_headers):
    body = _predict(client, admin_headers, FULL_PAYLOAD).json()
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


# ==========================================================
# Validation via the public API
# ==========================================================

def test_unknown_prediction_type_is_422(client, admin_headers):
    response = _predict(
        client, admin_headers, {"prediction_type": "quantum_yield"}
    )
    assert response.status_code == 422
    assert response.json() == {
        "success": False,
        "message": "Validation failed",
        "code": "VALIDATION_ERROR",
    }


def test_missing_prediction_type_is_422(client, admin_headers):
    response = _predict(client, admin_headers, {"crop_name": "Wheat"})
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_invalid_soil_ph_is_422(client, admin_headers):
    payload = dict(FULL_PAYLOAD)
    payload["soil"] = {"ph": 42.0}
    response = _predict(client, admin_headers, payload)
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_invalid_weather_humidity_is_422(client, admin_headers):
    payload = dict(FULL_PAYLOAD)
    payload["weather"] = {"humidity": 150}
    response = _predict(client, admin_headers, payload)
    assert response.status_code == 422


# ==========================================================
# Response hygiene
# ==========================================================

def test_response_never_exposes_local_path(client, admin_headers):
    response = _predict(client, admin_headers, FULL_PAYLOAD)
    assert "\\" not in response.text
    assert "C:" not in response.text
    assert "PREDICTION_MODEL_PATH" not in response.text
    assert ".env" not in response.text