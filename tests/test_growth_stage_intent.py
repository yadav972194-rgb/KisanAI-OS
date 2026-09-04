"""
KisanAI OS - Phase 1.10 Crop Growth Stage Intent Routing tests.

Growth-stage queries (e.g. "वृद्धि अवस्था पहचान", "growth stage detect")
must route to INTENT_GROWTH_STAGE and the assistant must return an
honest Hindi pointer to the 'वृद्धि अवस्था पहचान' screen - never a
fabricated growth stage.

Existing intents (CROP_STATUS, WEATHER, DISEASE_DETECTION,
PEST_DETECTION, WEED_DETECTION, NUTRIENT_DEFICIENCY, ...) and unknown
inputs must keep their current behavior.
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
    INTENT_WEATHER,
    INTENT_WEED_DETECTION,
    classify_intent,
)
from config.core.services.weather_service import WeatherServiceError


# ==========================================================
# Intent router: Hindi / Hinglish / English growth-stage phrases
# ==========================================================

def test_growth_stage_hindi_query():
    result = classify_intent("वृद्धि अवस्था पहचानना है")
    assert result.intent == INTENT_GROWTH_STAGE
    assert "वृद्धि अवस्था" in result.keywords


def test_growth_stage_english_query():
    result = classify_intent("detect crop growth stage")
    assert result.intent == INTENT_GROWTH_STAGE
    assert "growth" in result.keywords


def test_growth_stage_multiple_hindi_phrases():
    for text in (
        "वृद्धि अवस्था पहचान",
        "फसल की वृद्धि जांचो",
        "विकास अवस्था क्या है",
        "फसल किस अवस्था में है",
        "क्या फसल परिपक्व है",
    ):
        assert classify_intent(text).intent == INTENT_GROWTH_STAGE, text


def test_growth_stage_multiple_english_phrases():
    for text in (
        "growth stage detect",
        "detect crop growth",
        "identify growth stage",
        "crop maturity",
        "what growth stage is my crop",
    ):
        assert classify_intent(text).intent == INTENT_GROWTH_STAGE, text


def test_existing_intents_not_misclassified_as_growth_stage():
    assert classify_intent("मेरी फसल के क्या हाल हैं?").intent == INTENT_CROP_STATUS
    assert classify_intent("आज मौसम कैसा है?").intent == INTENT_WEATHER
    assert classify_intent("पत्ती पर रोग लग गया है").intent == INTENT_DISEASE_DETECTION
    assert classify_intent("कीट पहचान").intent == INTENT_PEST_DETECTION
    assert classify_intent("खरपतवार पहचान").intent == INTENT_WEED_DETECTION
    assert classify_intent("पोषक तत्व की कमी पहचान").intent == INTENT_NUTRIENT_DEFICIENCY
    assert classify_intent("फसल के लिए क्या सलाह देंगे?").intent == INTENT_CROP_ADVICE
    assert classify_intent("मुझे सलाह दो").intent == INTENT_AI_ADVICE


def test_unknown_and_generic_input_remain_unknown():
    assert classify_intent("नमस्ते").intent == INTENT_UNKNOWN
    assert classify_intent("").intent == INTENT_UNKNOWN
    assert classify_intent(None).intent == INTENT_UNKNOWN
    assert classify_intent("   ").intent == INTENT_UNKNOWN


# ==========================================================
# Assistant service: growth-stage pointer
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


def test_growth_stage_pointer_message():
    result = _service().pointer(INTENT_GROWTH_STAGE)
    assert result["intent"] == INTENT_GROWTH_STAGE
    assert result["status"] == "OK"
    assert "वृद्धि अवस्था पहचान" in result["message"]


def test_growth_stage_pointer_contract():
    result = _service().pointer(INTENT_GROWTH_STAGE)
    assert result["intent"] == INTENT_GROWTH_STAGE
    assert result["status"] == "OK"
    assert isinstance(result["message"], str) and result["message"]
    assert result["data"] is None


# ==========================================================
# Assistant API: growth-stage intent E2E
# ==========================================================

def test_api_growth_stage_intent_routes_to_pointer(client, user_headers):
    response = client.post(
        "/api/assistant",
        json={"text": "वृद्धि अवस्था पहचान"},
        headers=user_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "GROWTH_STAGE"
    assert body["status"] == "OK"
    assert "वृद्धि अवस्था पहचान" in body["message"]
    assert body["data"] is None


def test_api_existing_intents_unchanged(client, user_headers):
    nutrient = client.post(
        "/api/assistant",
        json={"text": "पोषक तत्व की कमी पहचान"},
        headers=user_headers,
    )
    assert nutrient.status_code == 200
    assert nutrient.json()["intent"] == "NUTRIENT_DEFICIENCY"

    weed = client.post(
        "/api/assistant",
        json={"text": "खरपतवार पहचान"},
        headers=user_headers,
    )
    assert weed.status_code == 200
    assert weed.json()["intent"] == "WEED_DETECTION"

    unknown = client.post(
        "/api/assistant",
        json={"text": "नमस्ते"},
        headers=user_headers,
    )
    assert unknown.status_code == 200
    assert unknown.json()["intent"] == "UNKNOWN"