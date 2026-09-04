"""
KisanAI OS - Phase 1.11 Crop Water Stress Intent Routing tests.

Water-stress queries (e.g. "जल तनाव पहचान", "detect water stress") must
route to INTENT_WATER_STRESS and the assistant must return an honest
Hindi pointer to the 'जल तनाव पहचान' screen - never a fabricated
water stress level. Bare "पानी" (water) is deliberately NOT a keyword
because it is too generic.

Existing intents (CROP_STATUS, WEATHER, DISEASE_DETECTION,
PEST_DETECTION, WEED_DETECTION, NUTRIENT_DEFICIENCY, GROWTH_STAGE, ...)
and unknown inputs must keep their current behavior.
"""

from config.core.services.assistant_service import AssistantService
from config.core.services.intent_router import (
    INTENT_AI_ADVICE,
    INTENT_CROP_ADVICE,
    INTENT_CROP_STATUS,
    INTENT_DISEASE_DETECTION,
    INTENT_GROWTH_STAGE,
    INTENT_NUTRIENT_DEFICIENCY,
    INTENT_PEST_DETECTION,
    INTENT_UNKNOWN,
    INTENT_WATER_STRESS,
    INTENT_WEATHER,
    INTENT_WEED_DETECTION,
    classify_intent,
)
from config.core.services.weather_service import WeatherServiceError


# ==========================================================
# Intent router: Hindi / Hinglish / English water-stress phrases
# ==========================================================

def test_water_stress_hindi_query():
    result = classify_intent("जल तनाव पहचानना है")
    assert result.intent == INTENT_WATER_STRESS
    assert "जल तनाव" in result.keywords


def test_water_stress_english_query():
    result = classify_intent("detect crop water stress")
    assert result.intent == INTENT_WATER_STRESS
    assert "water stress" in result.keywords


def test_water_stress_multiple_hindi_phrases():
    for text in (
        "जल तनाव पहचान",
        "फसल में पानी की कमी हो गई है",
        "फसल सूखा झेल रही है",
        "सिंचाई कब करें",
        "फसल में विल्ट लग गया है",
    ):
        assert classify_intent(text).intent == INTENT_WATER_STRESS, text


def test_water_stress_multiple_english_phrases():
    for text in (
        "detect water stress",
        "is my crop under moisture stress",
        "check for drought",
        "crop wilting",
        "does my crop need irrigation",
    ):
        assert classify_intent(text).intent == INTENT_WATER_STRESS, text


def test_existing_intents_not_misclassified_as_water_stress():
    assert classify_intent("मेरी फसल के क्या हाल हैं?").intent == INTENT_CROP_STATUS
    assert classify_intent("आज मौसम कैसा है?").intent == INTENT_WEATHER
    assert classify_intent("पत्ती पर रोग लग गया है").intent == INTENT_DISEASE_DETECTION
    assert classify_intent("कीट पहचान").intent == INTENT_PEST_DETECTION
    assert classify_intent("खरपतवार पहचान").intent == INTENT_WEED_DETECTION
    assert classify_intent("पोषक तत्व की कमी पहचान").intent == INTENT_NUTRIENT_DEFICIENCY
    assert classify_intent("वृद्धि अवस्था पहचान").intent == INTENT_GROWTH_STAGE
    assert classify_intent("फसल के लिए क्या सलाह देंगे?").intent == INTENT_CROP_ADVICE
    assert classify_intent("मुझे सलाह दो").intent == INTENT_AI_ADVICE


def test_unknown_and_generic_input_remain_unknown():
    assert classify_intent("नमस्ते").intent == INTENT_UNKNOWN
    assert classify_intent("").intent == INTENT_UNKNOWN
    assert classify_intent(None).intent == INTENT_UNKNOWN
    assert classify_intent("   ").intent == INTENT_UNKNOWN


# ==========================================================
# Assistant service: water-stress pointer
# ==========================================================

class _FakeWeather:
    def get_weather(self):
        raise WeatherServiceError("pointer tests never fetch weather")


class _FakeRecommendation:
    def recommend(self, data):
        raise AssertionError("pointer tests never call recommendation")


def _service():
    return AssistantService(
        weather_service=_FakeWeather(),
        recommendation_service=_FakeRecommendation(),
    )


def test_water_stress_pointer_message():
    result = _service().pointer(INTENT_WATER_STRESS)
    assert result["intent"] == INTENT_WATER_STRESS
    assert result["status"] == "OK"
    assert "जल तनाव पहचान" in result["message"]


def test_water_stress_pointer_contract():
    result = _service().pointer(INTENT_WATER_STRESS)
    assert result["intent"] == INTENT_WATER_STRESS
    assert result["status"] == "OK"
    assert isinstance(result["message"], str) and result["message"]
    assert result["data"] is None


# ==========================================================
# Assistant API: water-stress intent E2E
# ==========================================================

def test_api_water_stress_intent_routes_to_pointer(client, user_headers):
    response = client.post(
        "/api/assistant",
        json={"text": "जल तनाव पहचान"},
        headers=user_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "WATER_STRESS"
    assert body["status"] == "OK"
    assert "जल तनाव पहचान" in body["message"]
    assert body["data"] is None


def test_api_existing_intents_unchanged(client, user_headers):
    growth = client.post(
        "/api/assistant",
        json={"text": "वृद्धि अवस्था पहचान"},
        headers=user_headers,
    )
    assert growth.status_code == 200
    assert growth.json()["intent"] == "GROWTH_STAGE"

    nutrient = client.post(
        "/api/assistant",
        json={"text": "पोषक तत्व की कमी पहचान"},
        headers=user_headers,
    )
    assert nutrient.status_code == 200
    assert nutrient.json()["intent"] == "NUTRIENT_DEFICIENCY"

    unknown = client.post(
        "/api/assistant",
        json={"text": "नमस्ते"},
        headers=user_headers,
    )
    assert unknown.status_code == 200
    assert unknown.json()["intent"] == "UNKNOWN"