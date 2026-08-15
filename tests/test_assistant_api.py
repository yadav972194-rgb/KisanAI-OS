"""
KisanAI OS - Assistant API (intent router) tests.

E2E coverage for the natural-language CROP_STATUS flow:
    "मेरी फसल के क्या हाल हैं?"

Honesty contract enforced at the API layer:
    - no farm / no crops -> INSUFFICIENT_DATA with the exact Hindi
      message; a status is never guessed.
    - farm + crops present -> OK with verified sections only.
    - every intent routes correctly; unknown queries get a pointer.

A fake weather live-fetch is installed (autouse) so these tests never
touch the network; recommendation uses the deterministic rule provider.
"""

import random
import sqlite3

import pytest

from config.core.models.weather import Weather
from config.core.services.assistant_service import MSG_CROP_STATUS_MISSING
from config.core.services.weather_service import WeatherService
from tests.conftest import TEST_DB_PATH


def _mobile():
    return f"9{random.randint(100000000, 999999999)}"


def _register(client, role="farmer"):
    uniq = random.randint(100000, 999999)
    username = f"assistant{role}{uniq}"
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "password123",
            "full_name": "Assistant Tester",
            "mobile": _mobile(),
            "role": role,
        },
    )
    assert response.status_code == 200, response.text
    login = client.post(
        "/api/auth/token",
        data={"username": username, "password": "password123"},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _farm_payload():
    return {
        "farm_size": 3.5,
        "village": "Rampur",
        "block": "Sitapur",
        "district": "Sitapur",
        "state": "Uttar Pradesh",
    }


def _crop_payload():
    return {
        "crop_name": f"AssistCrop{random.randint(100000, 999999)}",
        "season": "Rabi",
        "duration_days": 120,
        "water_requirement": "Medium",
    }


def _clear_weather():
    conn = sqlite3.connect(TEST_DB_PATH)
    try:
        conn.execute("DELETE FROM weather")
        conn.commit()
    finally:
        conn.close()


@pytest.fixture(autouse=True)
def _fake_weather(monkeypatch):
    """Deterministic weather: no network ever. Returns a fixed snapshot."""
    _clear_weather()

    def _fake_fetch(self):
        from datetime import datetime

        return Weather(
            location="Sitapur",
            temperature=31.5,
            humidity=55,
            condition="Thunderstorm",
            wind_speed=8.0,
            updated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

    monkeypatch.setattr(WeatherService, "_fetch_live", _fake_fetch)
    yield
    _clear_weather()


# ==========================================================
# A. Authentication
# ==========================================================

def test_assistant_requires_auth(client):
    response = client.post("/api/assistant", json={"text": "नमस्ते"})
    assert response.status_code == 401


def test_assistant_empty_text_is_rejected(client, user_headers):
    response = client.post("/api/assistant", json={"text": ""}, headers=user_headers)
    assert response.status_code == 422


# ==========================================================
# B. CROP_STATUS E2E: "मेरी फसल के क्या हाल हैं?"
# ==========================================================

def test_crop_status_e2e_no_farm_is_honest(client):
    headers = _register(client)
    response = client.post(
        "/api/assistant",
        json={"text": "मेरी फसल के क्या हाल हैं?"},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "CROP_STATUS"
    assert body["status"] == "INSUFFICIENT_DATA"
    assert body["message"] == MSG_CROP_STATUS_MISSING


def test_crop_status_e2e_farm_but_no_crops_is_honest(client):
    headers = _register(client)
    created = client.post("/api/my-farm", json=_farm_payload(), headers=headers)
    assert created.status_code == 200, created.text

    response = client.post(
        "/api/assistant",
        json={"text": "मेरी फसल के क्या हाल हैं?"},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "CROP_STATUS"
    assert body["status"] == "INSUFFICIENT_DATA"
    assert body["message"] == MSG_CROP_STATUS_MISSING
    assert "crops" in body["data"]["missing"]


def test_crop_status_e2e_with_farm_and_crop_returns_verified_status(client):
    headers = _register(client)
    created = client.post("/api/my-farm", json=_farm_payload(), headers=headers)
    assert created.status_code == 200, created.text
    added = client.post(
        "/api/my-farm/crops", json=_crop_payload(), headers=headers
    )
    assert added.status_code == 200, added.text

    response = client.post(
        "/api/assistant",
        json={
            "text": "मेरी फसल के क्या हाल हैं?",
            "soil": {
                "ph": 6.8,
                "moisture": 55,
                "nitrogen": 80,
                "phosphorus": 45,
                "potassium": 60,
            },
        },
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "CROP_STATUS"
    assert body["status"] == "OK"

    data = body["data"]
    assert data["farm"]["village"] == "Rampur"
    assert data["farm"]["district"] == "Sitapur"
    assert data["farm"]["farm_size"] == 3.5
    assert len(data["crops"]) == 1
    assert data["crops"][0]["season"] == "Rabi"
    # Verified weather from the fake live-fetch, and rule-based advice
    # because the full context (one crop + soil + weather) is present.
    assert data["weather"]["condition"] == "Thunderstorm"
    assert data["advice"]["status"] == "RECOMMENDATION_AVAILABLE"


# ==========================================================
# C. Other intents route correctly
# ==========================================================

def test_weather_intent_returns_honest_weather(client, user_headers):
    response = client.post(
        "/api/assistant",
        json={"text": "आज मौसम कैसा है?"},
        headers=user_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "WEATHER"
    assert body["status"] == "OK"
    assert "मौसम" in body["message"]
    assert body["data"]["temperature"] == 31.5


def test_my_farm_intent_routes_to_pointer(client, user_headers):
    response = client.post(
        "/api/assistant",
        json={"text": "मेरा खेत कैसे देखूं?"},
        headers=user_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "MY_FARM"
    assert "मेरा खेत" in body["message"]


def test_disease_detection_intent_routes_to_pointer(client, user_headers):
    response = client.post(
        "/api/assistant",
        json={"text": "पत्ती पर रोग लग गया है"},
        headers=user_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "DISEASE_DETECTION"
    assert "रोग पहचान" in body["message"]


def test_crop_advice_intent_routes_to_pointer(client, user_headers):
    response = client.post(
        "/api/assistant",
        json={"text": "फसल के लिए क्या सलाह देंगे?"},
        headers=user_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "CROP_ADVICE"
    assert "AI सलाह" in body["message"]


def test_unknown_intent_returns_helpful_pointer(client, user_headers):
    response = client.post(
        "/api/assistant",
        json={"text": "नमस्ते"},
        headers=user_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "UNKNOWN"
    assert "समझ नहीं आया" in body["message"]
