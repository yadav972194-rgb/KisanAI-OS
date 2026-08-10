"""
KisanAI OS - Phase 5.5 Weather module tests.

The weather module is provider-driven and read-only at the API layer.
These tests cover the full GET /api/weather cache flow (fresh hit,
live fetch, stale fallback, provider failure), the repository
upsert/duplicate handling, service freshness and WMO condition
mapping, response shape, and authentication/authorization.
"""

import sqlite3
from datetime import datetime

import pytest

from config.core.database import SessionLocal
from config.core.models.weather import Weather
from config.core.repositories.weather_repository import WeatherRepository
from config.core.services.weather_service import (
    WeatherService,
    WeatherServiceError,
)
from tests.conftest import TEST_DB_PATH


def _now_string():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _rowcount():
    conn = sqlite3.connect(TEST_DB_PATH)
    try:
        return conn.execute("SELECT COUNT(*) FROM weather").fetchone()[0]
    finally:
        conn.close()


def _seed_weather(location="Sitapur", updated_at=None, **overrides):
    payload = {
        "location": location,
        "temperature": 27.5,
        "humidity": 68,
        "condition": "Partly Cloudy",
        "wind_speed": 12.0,
        "updated_at": updated_at or _now_string(),
    }
    payload.update(overrides)
    conn = sqlite3.connect(TEST_DB_PATH)
    try:
        conn.execute(
            "INSERT INTO weather "
            "(location, temperature, humidity, condition, wind_speed, updated_at) "
            "VALUES (:location, :temperature, :humidity, :condition, "
            ":wind_speed, :updated_at)",
            payload,
        )
        conn.commit()
    finally:
        conn.close()


@pytest.fixture(autouse=True)
def _clean_weather():
    """Every weather test starts and ends with an empty weather table so
    results are deterministic (the unique location constraint allows only
    one row per location in the session-scoped test database)."""
    conn = sqlite3.connect(TEST_DB_PATH)
    try:
        conn.execute("DELETE FROM weather")
        conn.commit()
    finally:
        conn.close()
    yield
    conn = sqlite3.connect(TEST_DB_PATH)
    try:
        conn.execute("DELETE FROM weather")
        conn.commit()
    finally:
        conn.close()


# ==========================================================
# A. Authentication (401)
# ==========================================================

def test_weather_requires_auth(client):
    assert client.get("/api/weather").status_code == 401


def test_weather_authenticated_read(client, user_headers):
    _seed_weather(temperature=26.0, condition="Clear Sky")

    response = client.get("/api/weather", headers=user_headers)
    assert response.status_code == 200
    assert response.json()["condition"] == "Clear Sky"


# ==========================================================
# B. Fresh cache hit (no live fetch, no DB write)
# ==========================================================

def test_weather_fresh_cache_hit(client, user_headers):
    _seed_weather(temperature=26.0, condition="Clear Sky")

    response = client.get("/api/weather", headers=user_headers)
    assert response.status_code == 200

    body = response.json()
    assert body["location"] == "Sitapur"
    assert body["temperature"] == 26.0
    assert body["humidity"] == 68
    assert body["condition"] == "Clear Sky"
    assert body["wind_speed"] == 12.0
    assert "updated_at" in body

    assert set(body.keys()) == {
        "location",
        "temperature",
        "humidity",
        "condition",
        "wind_speed",
        "updated_at",
    }

    assert _rowcount() == 1


# ==========================================================
# C. Live fetch success path
# ==========================================================

def test_weather_live_fetch_success(client, user_headers, monkeypatch):
    fetched = Weather(
        location="Sitapur",
        temperature=31.5,
        humidity=55,
        condition="Thunderstorm",
        wind_speed=8.0,
        updated_at=_now_string(),
    )

    def _fake_fetch(self):
        return fetched

    monkeypatch.setattr(WeatherService, "_fetch_live", _fake_fetch)

    response = client.get("/api/weather", headers=user_headers)
    assert response.status_code == 200

    body = response.json()
    assert body["temperature"] == 31.5
    assert body["humidity"] == 55
    assert body["condition"] == "Thunderstorm"
    assert body["wind_speed"] == 8.0

    assert _rowcount() == 1


# ==========================================================
# D. Stale cache served when live fetch fails
# ==========================================================

def test_weather_stale_cache_served_on_fetch_failure(
    client, user_headers, monkeypatch
):
    _seed_weather(
        updated_at="2000-01-01 00:00:00",
        temperature=19.5,
        condition="Foggy",
    )

    def _raise_fetch(self):
        raise WeatherServiceError("provider down")

    monkeypatch.setattr(WeatherService, "_fetch_live", _raise_fetch)

    response = client.get("/api/weather", headers=user_headers)
    assert response.status_code == 200

    body = response.json()
    assert body["temperature"] == 19.5
    assert body["condition"] == "Foggy"


# ==========================================================
# E. Live fetch fails with no cache -> 502
# ==========================================================

def test_weather_fetch_failure_no_cache_502(
    client, user_headers, monkeypatch
):
    def _raise_fetch(self):
        raise WeatherServiceError("provider down")

    monkeypatch.setattr(WeatherService, "_fetch_live", _raise_fetch)

    response = client.get("/api/weather", headers=user_headers)
    assert response.status_code == 502
    assert response.json()["success"] is False


# ==========================================================
# F. Repository upsert / duplicate handling
# ==========================================================

def test_repository_save_upserts_by_location(client):
    repo = WeatherRepository()
    try:
        repo.save(
            Weather(
                location="UpsertCity",
                temperature=20.0,
                humidity=60,
                condition="Clear",
                wind_speed=5.0,
                updated_at=_now_string(),
            )
        )
        assert _rowcount() == 1
        first = repo.get_latest_by_location("UpsertCity")
        assert first is not None
        assert first.temperature == 20.0
        first_id = first.weather_id

        repo.save(
            Weather(
                weather_id=first_id + 50,
                location="UpsertCity",
                temperature=25.5,
                humidity=72,
                condition="Rainy",
                wind_speed=9.0,
                updated_at=_now_string(),
            )
        )

        assert _rowcount() == 1

        second = repo.get_latest_by_location("UpsertCity")
        assert second.weather_id == first_id
        assert second.temperature == 25.5
        assert second.humidity == 72
        assert second.condition == "Rainy"
        assert second.wind_speed == 9.0

        assert repo.get_latest() is not None
    finally:
        repo.close()


def test_repository_get_latest_by_location_missing(client):
    repo = WeatherRepository()
    try:
        assert repo.get_latest_by_location("Nowhere") is None
    finally:
        repo.close()


# ==========================================================
# G. Service: freshness logic
# ==========================================================

def test_is_fresh_logic(client):
    service = WeatherService(repo=WeatherRepository())
    try:
        assert service._is_fresh(_now_string()) is True
        assert service._is_fresh("2000-01-01 00:00:00") is False
        assert service._is_fresh(None) is False
        assert service._is_fresh("not-a-date") is False
    finally:
        service.repo.close()


# ==========================================================
# H. Service: WMO condition mapping
# ==========================================================

def test_weather_condition_mapping(client):
    service = WeatherService(repo=WeatherRepository())
    try:
        assert service._weather_condition(0) == "Clear Sky"
        assert service._weather_condition(2) == "Partly Cloudy"
        assert service._weather_condition(61) == "Light Rain"
        assert service._weather_condition(95) == "Thunderstorm"
        assert service._weather_condition(999) == "Unknown"
    finally:
        service.repo.close()
