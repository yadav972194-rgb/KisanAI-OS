"""
KisanAI OS - Phase 1.7 Pest Detection Intent Routing tests.

Pest-detection queries (e.g. "कीट पहचान", "pest detect") must route to
INTENT_PEST_DETECTION and the assistant must return an honest Hindi
pointer to the 'कीट पहचान' screen - never a fabricated pest diagnosis.

Existing intents (CROP_STATUS, WEATHER, DISEASE_DETECTION, ...) and
unknown inputs must keep their current behavior.
"""

from config.core.services.assistant_service import AssistantService
from config.core.services.intent_router import (
    INTENT_AI_ADVICE,
    INTENT_CROP_ADVICE,
    INTENT_CROP_STATUS,
    INTENT_DISEASE_DETECTION,
    INTENT_PEST_DETECTION,
    INTENT_UNKNOWN,
    INTENT_WEATHER,
    classify_intent,
)
from config.core.services.weather_service import WeatherServiceError


# ==========================================================
# Intent router: Hindi / Hinglish / English pest phrases
# ==========================================================

def test_pest_detection_hindi_query():
    result = classify_intent("कीड़ा पहचानना है")
    assert result.intent == INTENT_PEST_DETECTION
    assert "कीड़ा" in result.keywords


def test_pest_detection_english_query():
    result = classify_intent("detect pest")
    assert result.intent == INTENT_PEST_DETECTION
    assert "pest" in result.keywords


def test_pest_detection_multiple_hindi_phrases():
    for text in (
        "कीट पहचान",
        "फसल में कीड़ा लग गया",
        "कीड़े का पता लगाओ",
        "कीटनाशक कौन सा इस्तेमाल करूं",
    ):
        assert classify_intent(text).intent == INTENT_PEST_DETECTION, text


def test_pest_detection_multiple_english_phrases():
    for text in (
        "pest detect",
        "detect pest",
        "identify pest",
        "insect on my crop",
        "keet pehchan karo",
    ):
        assert classify_intent(text).intent == INTENT_PEST_DETECTION, text


def test_existing_intents_not_misclassified_as_pest():
    assert classify_intent("मेरी फसल के क्या हाल हैं?").intent == INTENT_CROP_STATUS
    assert classify_intent("आज मौसम कैसा है?").intent == INTENT_WEATHER
    assert classify_intent("पत्ती पर रोग लग गया है").intent == INTENT_DISEASE_DETECTION
    assert classify_intent("फसल के लिए क्या सलाह देंगे?").intent == INTENT_CROP_ADVICE
    assert classify_intent("मुझे सलाह दो").intent == INTENT_AI_ADVICE


def test_unknown_and_generic_input_remain_unknown():
    assert classify_intent("नमस्ते").intent == INTENT_UNKNOWN
    assert classify_intent("").intent == INTENT_UNKNOWN
    assert classify_intent(None).intent == INTENT_UNKNOWN
    assert classify_intent("   ").intent == INTENT_UNKNOWN


# ==========================================================
# Assistant service: pest-detection pointer
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


def test_pest_detection_pointer_message():
    result = _service().pointer(INTENT_PEST_DETECTION)
    assert result["intent"] == INTENT_PEST_DETECTION
    assert result["status"] == "OK"
    assert "कीट पहचान" in result["message"]


def test_pest_detection_pointer_contract():
    result = _service().pointer(INTENT_PEST_DETECTION)
    assert result["intent"] == INTENT_PEST_DETECTION
    assert result["status"] == "OK"
    assert isinstance(result["message"], str) and result["message"]
    assert result["data"] is None


# ==========================================================
# Assistant API: pest-detection intent E2E
# ==========================================================

def test_api_pest_detection_intent_routes_to_pointer(client, user_headers):
    response = client.post(
        "/api/assistant",
        json={"text": "कीट पहचान"},
        headers=user_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "PEST_DETECTION"
    assert body["status"] == "OK"
    assert "कीट पहचान" in body["message"]
    assert body["data"] is None


def test_api_existing_intents_unchanged(client, user_headers):
    disease = client.post(
        "/api/assistant",
        json={"text": "पत्ती पर रोग लग गया है"},
        headers=user_headers,
    )
    assert disease.status_code == 200
    assert disease.json()["intent"] == "DISEASE_DETECTION"

    unknown = client.post(
        "/api/assistant",
        json={"text": "नमस्ते"},
        headers=user_headers,
    )
    assert unknown.status_code == 200
    assert unknown.json()["intent"] == "UNKNOWN"
