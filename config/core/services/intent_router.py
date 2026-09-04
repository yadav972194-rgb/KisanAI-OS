"""
KisanAI OS
Intent Router

Rule-based classification of farmer queries (in Hindi / Hinglish / English)
into a small set of stable intents. Deliberately NOT an LLM: it is
deterministic and testable, and it only routes the farmer to screens or
verified data. It never fabricates answers.

Intent codes:
    CROP_STATUS        - "मेरी फसल के क्या हाल हैं?" / crop health status
    WEATHER            - "आज मौसम कैसा है?"
    MY_FARM            - "मेरा खेत कैसे देखूं?"
    DISEASE_DETECTION  - "फोटो से रोग पहचान"
    PEST_DETECTION     - "फोटो से कीट पहचान"
    WEED_DETECTION     - "फोटो से खरपतवार पहचान"
    NUTRIENT_DEFICIENCY - "फोटो से पोषक तत्व की कमी पहचान"
    GROWTH_STAGE       - "फोटो से फसल की वृद्धि अवस्था पहचान"
    WATER_STRESS       - "फोटो से जल तनाव पहचान"
    CROP_ADVICE        - "फसल के लिए सलाह" (recommendation engine)
    SOIL               - "मिट्टी की जानकारी"
    AI_ADVICE          - generic ask for AI advice
    AUTH               - login / account / password queries
    HELP               - what can you do?
    UNKNOWN            - nothing matched
"""

from dataclasses import dataclass

INTENT_CROP_STATUS = "CROP_STATUS"
INTENT_WEATHER = "WEATHER"
INTENT_MY_FARM = "MY_FARM"
INTENT_DISEASE_DETECTION = "DISEASE_DETECTION"
INTENT_PEST_DETECTION = "PEST_DETECTION"
INTENT_WEED_DETECTION = "WEED_DETECTION"
INTENT_NUTRIENT_DEFICIENCY = "NUTRIENT_DEFICIENCY"
INTENT_GROWTH_STAGE = "GROWTH_STAGE"
INTENT_WATER_STRESS = "WATER_STRESS"
INTENT_CROP_ADVICE = "CROP_ADVICE"
INTENT_SOIL = "SOIL"
INTENT_AI_ADVICE = "AI_ADVICE"
INTENT_AUTH = "AUTH"
INTENT_HELP = "HELP"
INTENT_UNKNOWN = "UNKNOWN"

_ALL_INTENTS = (
    INTENT_CROP_STATUS,
    INTENT_WEATHER,
    INTENT_MY_FARM,
    INTENT_DISEASE_DETECTION,
    INTENT_PEST_DETECTION,
    INTENT_WEED_DETECTION,
    INTENT_NUTRIENT_DEFICIENCY,
    INTENT_GROWTH_STAGE,
    INTENT_WATER_STRESS,
    INTENT_CROP_ADVICE,
    INTENT_SOIL,
    INTENT_AI_ADVICE,
    INTENT_AUTH,
    INTENT_HELP,
    INTENT_UNKNOWN,
)

_HELP_WORDS = ("सहायता", "मदद", "help", "क्या कर सकते", "कैसे इस्तेमाल")
_AUTH_WORDS = (
    "लॉगिन", "login", "logout", "अकाउंट", "account", "खाता",
    "पासवर्ड", "password", "register", "साइन अप", "sign up",
)
_WEATHER_WORDS = ("मौसम", "बारिश", "बारिश होगी", "weather", "temperature", "तापमान")
_MY_FARM_WORDS = ("मेरा खेत", "मेरे खेत", "my farm", "खेत कैसा")
_SOIL_WORDS = ("मिट्टी", "soil")
_DISEASE_WORDS = ("रोग", "बीमारी", "बीमार", "disease", "पत्ती", "पीली पत्ती")
_PEST_WORDS = (
    "कीट", "कीड़ा", "कीड़े", "पेस्ट",
    "pest", "insect", "keet", "keeda",
)
_WEED_WORDS = (
    "खरपतवार", "जंगली घास", "घास", "खराब पौधा",
    "weed", "weeds", "unwanted plant",
)
_NUTRIENT_WORDS = (
    "पोषक", "पोषण", "पोषक तत्व", "खाद की कमी",
    "nutrient", "deficiency", "nitrogen", "phosphorus", "potassium",
    "नाइट्रोजन", "फास्फोरस", "पोटेशियम",
)
_GROWTH_STAGE_WORDS = (
    "वृद्धि अवस्था", "विकास अवस्था", "वृद्धि", "अवस्था", "परिपक्व",
    "growth stage", "growth", "maturity",
)
_WATER_STRESS_WORDS = (
    "जल तनाव", "पानी की कमी", "सूखा", "सिंचाई", "विल्ट", "पत्ती लटक",
    "water stress", "waterstress", "irrigation", "drought", "wilting",
    "thirsty", "dry", "moisture stress",
)
_STATUS_WORDS = ("हाल", "हालत", "स्थिति", "status", "हालचाल")
_ADVICE_WORDS = (
    "सलाह", "उपाय", "क्या करूं", "क्या करूँ", "क्या करना", "क्या छिड़क",
    "advice", "recommend", "guidance",
)


@dataclass(frozen=True)
class IntentResult:
    intent: str
    keywords: tuple = ()
    confidence: float = 1.0


def _has(text: str, words: tuple) -> list:
    return [w for w in words if w.lower() in text.lower()]


def classify_intent(text: str | None) -> IntentResult:
    """Classify a free-text farmer query into a stable intent.

    Keyword matching is case-insensitive. The ordering encodes priority:
    weather/soil/disease mentions beat a generic status phrase, and
    advice/status keywords must be anchored on "फसल" to avoid false
    positives on unrelated sentences.
    """
    raw = (text or "").strip()
    if not raw:
        return IntentResult(INTENT_UNKNOWN)

    hits = _has(raw, _HELP_WORDS)
    if hits:
        return IntentResult(INTENT_HELP, tuple(hits))

    hits = _has(raw, _AUTH_WORDS)
    if hits:
        return IntentResult(INTENT_AUTH, tuple(hits))

    hits = _has(raw, _WEATHER_WORDS)
    if hits:
        return IntentResult(INTENT_WEATHER, tuple(hits))

    hits = _has(raw, _MY_FARM_WORDS)
    if hits:
        return IntentResult(INTENT_MY_FARM, tuple(hits))

    hits = _has(raw, _SOIL_WORDS)
    if hits:
        return IntentResult(INTENT_SOIL, tuple(hits))

    hits = _has(raw, _DISEASE_WORDS)
    if hits:
        return IntentResult(INTENT_DISEASE_DETECTION, tuple(hits))

    hits = _has(raw, _PEST_WORDS)
    if hits:
        return IntentResult(INTENT_PEST_DETECTION, tuple(hits))

    hits = _has(raw, _WEED_WORDS)
    if hits:
        return IntentResult(INTENT_WEED_DETECTION, tuple(hits))

    hits = _has(raw, _NUTRIENT_WORDS)
    if hits:
        return IntentResult(INTENT_NUTRIENT_DEFICIENCY, tuple(hits))

    hits = _has(raw, _GROWTH_STAGE_WORDS)
    if hits:
        return IntentResult(INTENT_GROWTH_STAGE, tuple(hits))

    hits = _has(raw, _WATER_STRESS_WORDS)
    if hits:
        return IntentResult(INTENT_WATER_STRESS, tuple(hits))

    status_hits = _has(raw, _STATUS_WORDS)
    has_crop = "फसल" in raw.lower() or "crop" in raw.lower()
    if status_hits and has_crop:
        return IntentResult(INTENT_CROP_STATUS, tuple(status_hits))

    advice_hits = _has(raw, _ADVICE_WORDS)
    if advice_hits:
        if has_crop:
            return IntentResult(INTENT_CROP_ADVICE, tuple(advice_hits))
        return IntentResult(INTENT_AI_ADVICE, tuple(advice_hits))

    if has_crop:
        return IntentResult(INTENT_CROP_STATUS, ())

    return IntentResult(INTENT_UNKNOWN)