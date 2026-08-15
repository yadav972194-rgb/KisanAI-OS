"""
KisanAI OS - Assistant Service unit tests.

The service answers CROP_STATUS and WEATHER only from verified data
and returns honest pointers for every other intent. Fakes are injected
so no network, weather provider or database is touched.
"""

from types import SimpleNamespace

import pytest

from config.core.services.assistant_service import (
    MSG_CROP_STATUS_MISSING,
    MSG_WEATHER_UNAVAILABLE,
    AssistantService,
)
from config.core.services.intent_router import (
    INTENT_AI_ADVICE,
    INTENT_CROP_ADVICE,
    INTENT_CROP_STATUS,
    INTENT_DISEASE_DETECTION,
    INTENT_HELP,
    INTENT_MY_FARM,
    INTENT_SOIL,
    INTENT_UNKNOWN,
    INTENT_WEATHER,
)
from config.core.services.weather_service import WeatherServiceError

_USER = SimpleNamespace(id=1)

_FARM = {
    "success": True,
    "farmer_id": 7,
    "village": "Rampur",
    "district": "Sitapur",
    "state": "Uttar Pradesh",
    "farm_size": 3.5,
}

_CROPS = [
    {"crop_name": "Wheat", "season": "Rabi"},
    {"crop_name": "Mustard", "season": "Rabi"},
]

_CROPS_ONE = [
    {"crop_name": "Wheat", "season": "Rabi"},
]

_WEATHER = {
    "location": "Sitapur",
    "temperature": 31.5,
    "humidity": 55,
    "condition": "Thunderstorm",
    "wind_speed": 8.0,
    "updated_at": "2026-08-13 10:00:00",
}

_SOIL = {
    "ph": 6.8,
    "moisture": 55,
    "nitrogen": 80,
    "phosphorus": 45,
    "potassium": 60,
}


class FakeMyFarm:
    def __init__(self, farm=_FARM, crops=_CROPS):
        self.farm = farm
        self.crops = crops

    def get_farm(self, user_id):
        if self.farm is None:
            return {"success": False, "message": "Farm Not Found"}
        return self.farm

    def get_crops(self, user_id):
        return self.crops

    def close(self):
        pass


class FakeWeather:
    def __init__(self, data=_WEATHER, error=False):
        self.data = data
        self.error = error

    def get_weather(self):
        if self.error:
            raise WeatherServiceError("provider down")
        return self.data


class FakeRecommendation:
    def __init__(self, status="RECOMMENDATION_AVAILABLE"):
        self.status = status

    def recommend(self, data):
        return {
            "status": self.status,
            "recommendation_type": "general",
            "recommendations": [
                {"category": "irrigation", "text": "Irrigate when needed"}
            ],
            "warnings": [],
            "missing": [],
            "reason": None,
            "confidence": None,
            "model": None,
            "provider": "rule-based",
            "message": "",
        }


def _service_with(farm=_FARM, crops=_CROPS, weather=None, reco=None):
    service = AssistantService(
        weather_service=weather or FakeWeather(),
        recommendation_service=reco or FakeRecommendation(),
    )
    service.my_farm = FakeMyFarm(farm=farm, crops=crops)
    return service


# ==========================================================
# CROP_STATUS - insufficient data (never guessed)
# ==========================================================

def test_crop_status_missing_farm_returns_insufficient():
    service = _service_with(farm=None, crops=_CROPS)
    result = service.crop_status(_USER, soil=_SOIL)

    assert result["intent"] == INTENT_CROP_STATUS
    assert result["status"] == "INSUFFICIENT_DATA"
    assert result["message"] == MSG_CROP_STATUS_MISSING
    assert "farm" in result["data"]["missing"]


def test_crop_status_missing_crops_returns_insufficient():
    service = _service_with(farm=_FARM, crops=[])
    result = service.crop_status(_USER, soil=_SOIL)

    assert result["status"] == "INSUFFICIENT_DATA"
    assert result["message"] == MSG_CROP_STATUS_MISSING
    assert "crops" in result["data"]["missing"]


# ==========================================================
# CROP_STATUS - full verified status
# ==========================================================

def test_crop_status_ok_with_full_data():
    service = _service_with(crops=_CROPS_ONE)
    result = service.crop_status(_USER, soil=_SOIL)

    assert result["intent"] == INTENT_CROP_STATUS
    assert result["status"] == "OK"

    data = result["data"]
    assert data["farm"]["village"] == "Rampur"
    assert data["farm"]["farm_size"] == 3.5
    assert [c["crop_name"] for c in data["crops"]] == ["Wheat"]

    assert data["weather"]["temperature"] == 31.5
    assert data["weather"]["condition"] == "Thunderstorm"

    assert data["soil"]["ph"] == 6.8

    # Advice from the recommendation engine is attached when the full
    # verified context is present.
    assert data["advice"]["status"] == "RECOMMENDATION_AVAILABLE"
    assert data["advice"]["recommendations"]

    assert "Wheat" in result["message"]
    assert "Rampur" in result["message"]


def test_crop_status_ok_without_weather_notes_it_honestly():
    service = _service_with(crops=_CROPS_ONE, weather=FakeWeather(error=True))
    result = service.crop_status(_USER, soil=_SOIL)

    assert result["status"] == "OK"
    assert result["data"]["weather_unavailable"] is True
    # No fabricated weather, no advice without weather.
    assert "weather" not in result["data"]
    assert "advice" not in result["data"]
    assert "मौसम" in result["message"]


def test_crop_status_ok_without_soil_notes_it_honestly():
    service = _service_with(crops=_CROPS_ONE)
    result = service.crop_status(_USER, soil=None)

    assert result["status"] == "OK"
    assert result["data"]["soil_missing"] is True
    assert "advice" not in result["data"]
    assert "मिट्टी" in result["message"]


def test_crop_status_advice_not_generated_for_multiple_crops():
    service = _service_with()
    result = service.crop_status(_USER, soil=_SOIL)

    # Two crops -> the engine refuses to pick one; no partial advice.
    assert "advice" not in result["data"]


# ==========================================================
# WEATHER
# ==========================================================

def test_weather_ok():
    service = _service_with()
    result = service.weather()

    assert result["intent"] == INTENT_WEATHER
    assert result["status"] == "OK"
    assert result["data"]["temperature"] == 31.5
    assert "मौसम" in result["message"]
    assert "Sitapur" in result["message"]


def test_weather_unavailable():
    service = _service_with(weather=FakeWeather(error=True))
    result = service.weather()

    assert result["intent"] == INTENT_WEATHER
    assert result["status"] == "UNAVAILABLE"
    assert result["message"] == MSG_WEATHER_UNAVAILABLE
    assert result["data"] is None


# ==========================================================
# Pointer intents
# ==========================================================

def test_pointer_messages_for_other_intents():
    service = _service_with()

    for intent, keyword in (
        (INTENT_MY_FARM, "मेरा खेत"),
        (INTENT_SOIL, "मिट्टी"),
        (INTENT_DISEASE_DETECTION, "रोग पहचान"),
        (INTENT_CROP_ADVICE, "AI सलाह"),
        (INTENT_AI_ADVICE, "AI सलाह"),
        (INTENT_HELP, "फसल के क्या हाल"),
        (INTENT_UNKNOWN, "समझ नहीं आया"),
    ):
        result = service.pointer(intent)
        assert result["intent"] == intent
        assert result["status"] == "OK"
        assert keyword in result["message"]


def test_unknown_pointer_is_default():
    service = _service_with()
    result = service.pointer("NOT_A_REAL_INTENT")
    assert result["intent"] == "NOT_A_REAL_INTENT"
    assert "समझ नहीं आया" in result["message"]
