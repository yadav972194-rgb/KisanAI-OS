"""
KisanAI OS - Phase 1.9 Nutrient Deficiency Intent Routing tests.

Nutrient-deficiency queries (e.g. "पोषक तत्व की कमी पहचान", "nutrient
deficiency detect") must route to INTENT_NUTRIENT_DEFICIENCY and the
assistant must return an honest Hindi pointer to the 'पोषक तत्व पहचान'
screen - never a fabricated nutrient-deficiency identification.

Existing intents (CROP_STATUS, WEATHER, DISEASE_DETECTION,
PEST_DETECTION, WEED_DETECTION, ...) and unknown inputs must keep their
current behavior.
"""

from config.core.services.assistant_service import AssistantService
from config.core.services.intent_router import (
    INTENT_AI_ADVICE,
    INTENT_CROP_ADVICE,
    INTENT_CROP_STATUS,
    INTENT_DISEASE_DETECTION,
    INTENT_NUTRIENT_DEFICIENCY,
    INTENT_PEST_DETECTION,
    INTENT_UNKNOWN,
    INTENT_WEATHER,
    INTENT_WEED_DETECTION,
    classify_intent,
)
from config.core.services.weather_service import WeatherServiceError


# ==========================================================
# Intent router: Hindi / Hinglish / English nutrient phrases
# ==========================================================

def test_nutrient_deficiency_hindi_query():
    result = classify_intent("पोषक तत्व की कमी पहचानना है")
    assert result.intent == INTENT_NUTRIENT_DEFICIENCY
    assert "पोषक" in result.keywords


def test_nutrient_deficiency_english_query():
    result = classify_intent("detect nutrient deficiency")
    assert result.intent == INTENT_NUTRIENT_DEFICIENCY
    assert "nutrient" in result.keywords


def test_nutrient_deficiency_multiple_hindi_phrases():
    for text in (
        "पोषक तत्व की कमी पहचान",
        "फसल में पोषण की कमी है",
        "नाइट्रोजन की कमी पहचानो",
        "खेत में खाद की कमी लग रही है",
        "फास्फोरस की कमी जांचो",
    ):
        assert classify_intent(text).intent == INTENT_NUTRIENT_DEFICIENCY, text


def test_nutrient_deficiency_multiple_english_phrases():
    for text in (
        "nutrient deficiency detect",
        "detect deficiency",
        "identify nutrient deficiency",
        "nitrogen deficiency",
        "check phosphorus and potassium",
    ):
        assert classify_intent(text).intent == INTENT_NUTRIENT_DEFICIENCY, text


def test_existing_intents_not_misclassified_as_nutrient():
    assert classify_intent("मेरी फसल के क्या हाल हैं?").intent == INTENT_CROP_STATUS
    assert classify_intent("आज मौसम कैसा है?").intent == INTENT_WEATHER
    assert classify_intent("पत्ती पर रोग लग गया है").intent == INTENT_DISEASE_DETECTION
    assert classify_intent("कीट पहचान").intent == INTENT_PEST_DETECTION
    assert classify_intent("खरपतवार पहचान").intent == INTENT_WEED_DETECTION
    assert classify_intent("फसल के लिए क्या सलाह देंगे?").intent == INTENT_CROP_ADVICE
    assert classify_intent("मुझे सलाह दो").intent == INTENT_AI_ADVICE


def test_unknown_and_generic_input_remain_unknown():
    assert classify_intent("नमस्ते").intent == INTENT_UNKNOWN
    assert classify_intent("").intent == INTENT_UNKNOWN
    assert classify_intent(None).intent == INTENT_UNKNOWN
    assert classify_intent("   ").intent == INTENT_UNKNOWN


# ==========================================================
# Assistant service: nutrient-deficiency pointer
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


def test_nutrient_deficiency_pointer_message():
    result = _service().pointer(INTENT_NUTRIENT_DEFICIENCY)
    assert result["intent"] == INTENT_NUTRIENT_DEFICIENCY
    assert result["status"] == "OK"
    assert "पोषक तत्व पहचान" in result["message"]


def test_nutrient_deficiency_pointer_contract():
    result = _service().pointer(INTENT_NUTRIENT_DEFICIENCY)
    assert result["intent"] == INTENT_NUTRIENT_DEFICIENCY
    assert result["status"] == "OK"
    assert isinstance(result["message"], str) and result["message"]
    assert result["data"] is None


# ==========================================================
# Assistant API: nutrient-deficiency intent E2E
# ==========================================================

def test_api_nutrient_deficiency_intent_routes_to_pointer(client, user_headers):
    response = client.post(
        "/api/assistant",
        json={"text": "पोषक तत्व की कमी पहचान"},
        headers=user_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "NUTRIENT_DEFICIENCY"
    assert body["status"] == "OK"
    assert "पोषक तत्व पहचान" in body["message"]
    assert body["data"] is None


def test_api_existing_intents_unchanged(client, user_headers):
    disease = client.post(
        "/api/assistant",
        json={"text": "पत्ती पर रोग लग गया है"},
        headers=user_headers,
    )
    assert disease.status_code == 200
    assert disease.json()["intent"] == "DISEASE_DETECTION"

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
