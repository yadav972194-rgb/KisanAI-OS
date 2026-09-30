"""
KisanAI OS - Phase 1.14: Recommendations API integration tests.

Exercise the public ``POST /api/recommendations`` endpoint end-to-end
through the real FastAPI routing/validation/engine stack (TestClient),
exactly as a mobile client would: authentication, structured context,
``RECOMMENDATION_AVAILABLE``, ``INSUFFICIENT_DATA`` with exact missing
keys, validation envelopes, and response hygiene. No internals are
monkeypatched here - that is the milestone test suite's job.
"""

FULL_PAYLOAD = {
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

SOIL_ONLY = {"crop_name": "Wheat", "soil": {"ph": 6.5}}


def _recommend(client, headers, payload):
    return client.post("/api/recommendations", json=payload, headers=headers)


# ==========================================================
# Authentication / authorization
# ==========================================================

def test_unauthenticated_request_is_rejected(client):
    response = _recommend(client, None, FULL_PAYLOAD)
    assert response.status_code == 401
    body = response.json()
    assert body["detail"]["success"] is False
    assert body["detail"]["code"] == "SESSION_EXPIRED"


def test_any_authenticated_user_can_get_recommendations(
    client, admin_headers, user_headers
):
    for headers in (admin_headers, user_headers):
        response = _recommend(client, headers, FULL_PAYLOAD)
        assert response.status_code == 200
        assert response.json()["success"] is True


# ==========================================================
# Request -> response lifecycle
# ==========================================================

def test_full_context_returns_traceable_recommendations(
    client, admin_headers
):
    body = _recommend(client, admin_headers, FULL_PAYLOAD).json()
    assert body["status"] == "RECOMMENDATION_AVAILABLE"
    assert body["recommendations"]
    assert body["missing"] == []
    for item in body["recommendations"]:
        assert item["source"] == "deterministic-rule"
        assert item["text"]
        assert item["reason"]


def test_stable_response_shape(client, admin_headers):
    body = _recommend(client, admin_headers, FULL_PAYLOAD).json()
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


def test_missing_context_reports_exact_missing_keys(client, admin_headers):
    body = _recommend(client, admin_headers, SOIL_ONLY).json()
    assert body["status"] == "INSUFFICIENT_DATA"
    assert body["recommendations"] == []
    assert "weather" in body["missing"]
    assert "soil.moisture" in body["missing"]
    assert "soil.nitrogen" in body["missing"]
    assert set(body["required_context"]) == {"crop", "soil", "weather"}
    assert body["message"] == "Insufficient data to generate a recommendation"


def test_missing_crop_is_reported_never_guessed(client, admin_headers):
    payload = {k: v for k, v in FULL_PAYLOAD.items() if k != "crop_name"}
    body = _recommend(client, admin_headers, payload).json()
    assert body["status"] == "INSUFFICIENT_DATA"
    assert "crop" in body["missing"]
    assert body["recommendations"] == []
    assert body["warnings"] == []


def test_full_context_never_claims_disease_or_dosage(client, admin_headers):
    body = _recommend(client, admin_headers, FULL_PAYLOAD).json()
    text = " ".join(_texts(body)) + " ".join(body["warnings"]).lower()
    assert body["status"] == "RECOMMENDATION_AVAILABLE"
    assert "no disease" not in text.lower()
    assert "healthy" not in text.lower()
    assert " kg" not in text.lower()


def _texts(body):
    return [item["text"] for item in body["recommendations"]]


# ==========================================================
# Validation via the public API
# ==========================================================

def test_invalid_disease_severity_is_422(client, admin_headers):
    payload = dict(FULL_PAYLOAD)
    payload["disease"] = {"name": "Leaf Rust", "severity": "Catastrophic"}
    response = _recommend(client, admin_headers, payload)
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_invalid_soil_ph_is_422(client, admin_headers):
    payload = dict(FULL_PAYLOAD)
    payload["soil"] = {"ph": 42.0}
    response = _recommend(client, admin_headers, payload)
    assert response.status_code == 422


# ==========================================================
# Response hygiene
# ==========================================================

def test_response_never_exposes_local_path(client, admin_headers):
    response = _recommend(client, admin_headers, FULL_PAYLOAD)
    assert "\\" not in response.text
    assert "C:" not in response.text
    assert "RECOMMENDATION_MODEL_PATH" not in response.text
    assert ".env" not in response.text