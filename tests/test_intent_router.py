"""
KisanAI OS - Intent Router unit tests.

The router maps free-text farmer queries (Hindi / Hinglish / English)
to a stable set of intents. Tests cover every intent code, ordering
priority (weather/soil/disease beat generic status phrases), case
insensitivity and the unknown/empty fallbacks.
"""

from config.core.services.intent_router import (
    INTENT_AI_ADVICE,
    INTENT_AUTH,
    INTENT_CROP_ADVICE,
    INTENT_CROP_STATUS,
    INTENT_DISEASE_DETECTION,
    INTENT_HELP,
    INTENT_MY_FARM,
    INTENT_SOIL,
    INTENT_UNKNOWN,
    INTENT_WEATHER,
    classify_intent,
)


def test_crop_status_hindi_question():
    result = classify_intent("मेरी फसल के क्या हाल हैं?")
    assert result.intent == INTENT_CROP_STATUS
    assert "हाल" in result.keywords


def test_crop_status_english():
    assert classify_intent("What is the status of my crop?").intent == INTENT_CROP_STATUS
    assert classify_intent("My crop status").intent == INTENT_CROP_STATUS


def test_crop_status_hindi_halat():
    assert classify_intent("फसल की हालत कैसी है?").intent == INTENT_CROP_STATUS


def test_weather_intent():
    result = classify_intent("आज मौसम कैसा है?")
    assert result.intent == INTENT_WEATHER
    assert classify_intent("weather today").intent == INTENT_WEATHER
    assert classify_intent("बारिश होगी क्या?").intent == INTENT_WEATHER


def test_weather_beats_generic_status_phrase():
    # "कैसा" alone would match a status phrase; weather must win.
    assert classify_intent("मौसम कैसा है?").intent == INTENT_WEATHER


def test_my_farm_intent():
    assert classify_intent("मेरा खेत कैसे देखूं?").intent == INTENT_MY_FARM


def test_soil_intent():
    assert classify_intent("मिट्टी की जानकारी दो").intent == INTENT_SOIL


def test_disease_detection_intent():
    assert classify_intent("पत्ती पर रोग लग गया है").intent == INTENT_DISEASE_DETECTION
    assert classify_intent("फसल में बीमारी है").intent == INTENT_DISEASE_DETECTION


def test_crop_advice_intent():
    result = classify_intent("फसल के लिए क्या सलाह देंगे?")
    assert result.intent == INTENT_CROP_ADVICE
    assert "सलाह" in result.keywords


def test_ai_advice_intent_without_crop():
    assert classify_intent("मुझे सलाह दो").intent == INTENT_AI_ADVICE
    assert classify_intent("क्या करूं?").intent == INTENT_AI_ADVICE


def test_auth_intent():
    assert classify_intent("पासवर्ड भूल गया हूं").intent == INTENT_AUTH
    assert classify_intent("login karne me problem").intent == INTENT_AUTH


def test_help_intent():
    assert classify_intent("आप क्या कर सकते हैं?").intent == INTENT_HELP
    assert classify_intent("सहायता चाहिए").intent == INTENT_HELP


def test_unknown_intent():
    assert classify_intent("नमस्ते").intent == INTENT_UNKNOWN


def test_empty_and_none_are_unknown():
    assert classify_intent("").intent == INTENT_UNKNOWN
    assert classify_intent(None).intent == INTENT_UNKNOWN
    assert classify_intent("   ").intent == INTENT_UNKNOWN


def test_case_insensitive_english():
    assert classify_intent("MY CROP STATUS").intent == INTENT_CROP_STATUS
    assert classify_intent("How is the WEATHER?").intent == INTENT_WEATHER
