"""
KisanAI OS - Mandatory E2E journey tests (V3).

One coherent, mobile-app-shaped journey is exercised against the real
backend for each mandatory flow:

    AUTH E2E     register -> login -> /me -> create farm+crop -> server
                 logout -> old token rejected (401) -> re-login -> /me
                 works again.
    CROP_STATUS  "मेरी फसल के क्या हाल हैं?" -> honest INSUFFICIENT_DATA
                 (exact Hindi message) when farm/crops are missing ->
                 after entering a farm and a crop -> OK with verified
                 sections (farm, crops, weather, advice). Never guessed.
    DISEASE E2E  register -> upload a real image -> honest
                 MODEL_NOT_CONFIGURED (no fabricated diagnosis) ->
                 knowledge base is readable.

A fake weather live-fetch is installed so the crop-status journey never
touches the network; the recommendation engine is the deterministic
rule provider.
"""

import random
import sqlite3
from datetime import datetime

import pytest

from config.core.models.weather import Weather
from config.core.services.assistant_service import MSG_CROP_STATUS_MISSING
from config.core.services.weather_service import WeatherService
from tests.conftest import TEST_DB_PATH


def _mobile():
    return f"9{random.randint(100000000, 999999999)}"


def _username(prefix):
    return f"{prefix}{random.randint(100000, 999999)}"


def _register(client, prefix="e2e"):
    username = _username(prefix)
    register = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "password123",
            "full_name": "E2E Farmer",
            "mobile": _mobile(),
            "role": "farmer",
        },
    )
    assert register.status_code == 200, register.text

    login = client.post(
        "/api/auth/token",
        data={"username": username, "password": "password123"},
    )
    assert login.status_code == 200, login.text
    return username, login.json()["access_token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


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
        "crop_name": f"E2ECrop{random.randint(100000, 999999)}",
        "season": "Rabi",
        "duration_days": 120,
        "water_requirement": "Medium",
    }


@pytest.fixture(autouse=True)
def _deterministic_weather(monkeypatch):
    """No network: a fixed weather snapshot for every journey test."""
    conn = sqlite3.connect(TEST_DB_PATH)
    try:
        conn.execute("DELETE FROM weather")
        conn.commit()
    finally:
        conn.close()

    def _fake_fetch(self):
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
    conn = sqlite3.connect(TEST_DB_PATH)
    try:
        conn.execute("DELETE FROM weather")
        conn.commit()
    finally:
        conn.close()


# ==========================================================
# AUTH E2E
# ==========================================================

def test_auth_e2e_full_journey(client):
    username, token = _register(client, "authe2e")
    headers = _headers(token)

    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200, me.text
    assert me.json()["username"] == username

    farm = client.post("/api/my-farm", json=_farm_payload(), headers=headers)
    assert farm.status_code == 200, farm.text
    crop = client.post(
        "/api/my-farm/crops", json=_crop_payload(), headers=headers
    )
    assert crop.status_code == 200, crop.text

    logout = client.post("/api/auth/logout", headers=headers)
    assert logout.status_code == 200, logout.text

    revoked = client.get("/api/auth/me", headers=headers)
    assert revoked.status_code == 401, revoked.text

    login2 = client.post(
        "/api/auth/token",
        data={"username": username, "password": "password123"},
    )
    assert login2.status_code == 200, login2.text
    token2 = login2.json()["access_token"]
    assert token2 != token

    me2 = client.get("/api/auth/me", headers=_headers(token2))
    assert me2.status_code == 200, me2.text
    assert me2.json()["username"] == username


def test_auth_e2e_wrong_password_rejected(client):
    username, token = _register(client, "authbad")
    assert client.get("/api/auth/me", headers=_headers(token)).status_code == 200

    bad = client.post(
        "/api/auth/token",
        data={"username": username, "password": "wrong-password"},
    )
    assert bad.status_code == 401
    assert bad.json()["detail"]["code"] == "AUTH_INVALID"

    # The old session still works: a failed login must not end it.
    assert client.get("/api/auth/me", headers=_headers(token)).status_code == 200


# ==========================================================
# CROP_STATUS E2E: "मेरी फसल के क्या हाल हैं?"
# ==========================================================

def test_crop_status_e2e_full_journey(client):
    _, token = _register(client, "cropstatus")
    headers = _headers(token)

    soil = {
        "ph": 6.8,
        "moisture": 55,
        "nitrogen": 80,
        "phosphorus": 45,
        "potassium": 60,
    }

    def ask(soil_payload=None):
        payload = {"text": "मेरी फसल के क्या हाल हैं?"}
        if soil_payload is not None:
            payload["soil"] = soil_payload
        return client.post("/api/assistant", json=payload, headers=headers)

    # 1. No farm yet -> honest INSUFFICIENT_DATA, exact Hindi message.
    first = ask()
    assert first.status_code == 200
    assert first.json()["intent"] == "CROP_STATUS"
    assert first.json()["status"] == "INSUFFICIENT_DATA"
    assert first.json()["message"] == MSG_CROP_STATUS_MISSING

    # 2. Farm present but no crop -> still INSUFFICIENT_DATA.
    client.post("/api/my-farm", json=_farm_payload(), headers=headers)
    second = ask()
    assert second.status_code == 200
    assert second.json()["status"] == "INSUFFICIENT_DATA"
    assert second.json()["message"] == MSG_CROP_STATUS_MISSING
    assert "crops" in second.json()["data"]["missing"]

    # 3. Crop added -> verified status with farm/crops/weather.
    client.post("/api/my-farm/crops", json=_crop_payload(), headers=headers)
    third = ask()
    assert third.status_code == 200
    body = third.json()
    assert body["intent"] == "CROP_STATUS"
    assert body["status"] == "OK"
    assert body["message"].startswith("आपके खेत")

    data = body["data"]
    assert data["farm"]["village"] == "Rampur"
    assert data["farm"]["farm_size"] == 3.5
    assert len(data["crops"]) == 1
    assert data["weather"]["condition"] == "Thunderstorm"

    # 3a. Without soil, no advice is fabricated; the gap is reported.
    assert data["soil_missing"] is True
    assert "advice" not in data

    # 3b. With soil, rule-based advice is attached from verified context.
    with_soil = ask(soil_payload=soil)
    assert with_soil.status_code == 200
    full = with_soil.json()
    assert full["status"] == "OK"
    assert full["data"]["soil"]["ph"] == 6.8
    assert full["data"]["advice"]["status"] == "RECOMMENDATION_AVAILABLE"
    assert full["data"]["advice"]["recommendations"]


# ==========================================================
# DISEASE E2E
# ==========================================================

@pytest.fixture()
def _isolated_upload_dir(monkeypatch, tmp_path):
    from config.settings import settings

    upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(upload_dir))
    return upload_dir


def test_disease_e2e_full_journey(client, _isolated_upload_dir):
    _, token = _register(client, "disease")
    headers = _headers(token)

    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 256

    # Honest MODEL_NOT_CONFIGURED: no bundled model, no fabricated diagnosis.
    detected = client.post(
        "/api/disease-detection",
        files={"file": ("leaf.png", png, "image/png")},
        data={"crop_name": "Wheat"},
        headers=headers,
    )
    assert detected.status_code == 200
    body = detected.json()
    assert body["success"] is True
    assert body["status"] == "MODEL_NOT_CONFIGURED"
    assert body["disease_name"] is None
    assert body["confidence"] is None
    assert body["model"] is None

    # Knowledge base remains readable for the farmer.
    diseases = client.get("/api/diseases", headers=headers)
    assert diseases.status_code == 200
    assert isinstance(diseases.json(), list)