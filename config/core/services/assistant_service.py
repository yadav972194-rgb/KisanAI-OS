"""
KisanAI OS
Assistant Service

Honest data-driven answers for the assistant / intent router.

CROP_STATUS contract (mirrors the recommendation engine):
- farm or crops missing  -> INSUFFICIENT_DATA with the exact Hindi
  message telling the farmer to enter crop info first; never a guess.
- farm + crops present   -> a structured status built ONLY from stored
  farm/crops, live-or-cached weather, and any soil/disease context the
  client supplied in the request.
- weather unavailable    -> an honest "UNAVAILABLE" note, never a
  fabricated forecast.
"""

from config.core.logger import logger
from config.core.models.user import User
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
)
from config.core.services.my_farm_service import MyFarmService
from config.core.services.recommendation_service import (
    RecommendationService,
)
from config.core.services.weather_service import WeatherService, WeatherServiceError

MSG_CROP_STATUS_MISSING = (
    "आपकी फसल की पूरी स्थिति बताने के लिए पहले अपनी फसल की जानकारी दर्ज करें।"
)
MSG_WEATHER_UNAVAILABLE = (
    "मौसम की जानकारी अभी उपलब्ध नहीं है। बाद में फिर कोशिश करें।"
)

_POINTERS = {
    INTENT_MY_FARM: (
        "आपके खेत की जानकारी 'मेरा खेत' स्क्रीन में देखी और जोड़ी जा सकती है।"
    ),
    INTENT_SOIL: (
        "मिट्टी की जानकारी 'मिट्टी' स्क्रीन में दर्ज कर सकते हैं।"
    ),
    INTENT_DISEASE_DETECTION: (
        "रोग पहचान के लिए पत्ती की फोटो लेकर 'रोग पहचान' स्क्रीन का उपयोग करें।"
    ),
    INTENT_CROP_ADVICE: (
        "फसल की सलाह के लिए 'AI सलाह' स्क्रीन में फसल, मिट्टी और मौसम की "
        "जानकारी भरें।"
    ),
    INTENT_AI_ADVICE: (
        "किसानी की सलाह के लिए 'AI सलाह' स्क्रीन में अपनी फसल, मिट्टी और मौसम "
        "की जानकारी भरें।"
    ),
    INTENT_AUTH: (
        "लॉगिन और खाते से जुड़ी मदद के लिए लॉगिन स्क्रीन का उपयोग करें।"
    ),
    INTENT_HELP: (
        "मैं ये सवाल समझ सकता हूँ: 'मेरी फसल के क्या हाल हैं?', 'आज मौसम कैसा "
        "है?', 'मेरा खेत कैसे देखूं?', 'रोग पहचान', 'फसल के लिए सलाह'।"
    ),
    INTENT_UNKNOWN: (
        "मुझे आपका सवाल समझ नहीं आया। आप पूछ सकते हैं: 'मेरी फसल के क्या हाल "
        "हैं?' या 'आज मौसम कैसा है?'।"
    ),
}


class AssistantService:
    """Assistant Service"""

    def __init__(self, session=None, weather_service=None, recommendation_service=None):
        self.my_farm = MyFarmService(session)
        self.weather_service = weather_service or WeatherService()
        self.recommendation = recommendation_service or RecommendationService()

    # ----------------------------------------------------------
    # CROP_STATUS
    # ----------------------------------------------------------

    def crop_status(self, user: User, soil=None, disease=None):
        farm = self.my_farm.get_farm(user.id)
        crops = self.my_farm.get_crops(user.id)

        if not isinstance(farm, dict) or not farm.get("success", True):
            logger.info(
                "CROP_STATUS: no farm for user %s -> INSUFFICIENT_DATA",
                user.id,
            )
            return self._insufficient(["farm"])

        if not isinstance(crops, list) or not crops:
            logger.info(
                "CROP_STATUS: no crops for user %s -> INSUFFICIENT_DATA",
                user.id,
            )
            return self._insufficient(["crops"])

        sections = {
            "farm": self._farm_section(farm),
            "crops": self._crops_section(crops),
        }

        # Weather: verified live/cached only; never fabricated.
        weather = self._weather_data()
        if weather is not None:
            sections["weather"] = weather
        else:
            sections["weather_unavailable"] = True

        if isinstance(soil, dict) and soil:
            sections["soil"] = soil
        else:
            sections["soil_missing"] = True

        if isinstance(disease, dict) and disease:
            sections["disease"] = disease

        advice = self._advice(crops, soil, weather)
        if advice is not None:
            sections["advice"] = advice

        message = self._status_message(sections)

        return {
            "intent": INTENT_CROP_STATUS,
            "status": "OK",
            "message": message,
            "data": sections,
        }

    def _insufficient(self, missing):
        return {
            "intent": INTENT_CROP_STATUS,
            "status": "INSUFFICIENT_DATA",
            "message": MSG_CROP_STATUS_MISSING,
            "data": {
                "missing": missing,
            },
        }

    def _farm_section(self, farm):
        return {
            "village": farm.get("village"),
            "district": farm.get("district"),
            "state": farm.get("state"),
            "farm_size": farm.get("farm_size"),
        }

    def _crops_section(self, crops):
        return [
            {
                "crop_name": crop.get("crop_name"),
                "season": crop.get("season"),
            }
            for crop in crops
        ]

    def _weather_data(self):
        try:
            weather = self.weather_service.get_weather()
        except WeatherServiceError as error:
            logger.warning("CROP_STATUS weather unavailable: %s", error)
            return None

        return {
            "temperature": weather.get("temperature"),
            "humidity": weather.get("humidity"),
            "condition": weather.get("condition"),
            "wind_speed": weather.get("wind_speed"),
            "location": weather.get("location"),
        }

    def _advice(self, crops, soil, weather):
        """Derive advice from the recommendation engine, only when the
        full verified context (one crop + soil + weather) is present.
        Returns None otherwise - no partial/guessed advice.
        """
        if weather is None or not isinstance(soil, dict) or not soil:
            return None

        if len(crops) != 1:
            return None

        crop = crops[0]

        try:
            result = self.recommendation.recommend(
                {
                    "crop_name": crop.get("crop_name"),
                    "soil": {
                        k: soil.get(k)
                        for k in (
                            "ph", "moisture", "nitrogen",
                            "phosphorus", "potassium",
                        )
                    },
                    "weather": {
                        k: weather.get(k)
                        for k in (
                            "temperature", "humidity",
                            "condition", "wind_speed",
                        )
                    },
                }
            )
        except Exception as error:  # recommendation never blocks status
            logger.warning("CROP_STATUS advice unavailable: %s", error)
            return None

        return {
            "status": result.get("status"),
            "recommendations": result.get("recommendations", []),
            "warnings": result.get("warnings", []),
            "message": result.get("message"),
        }

    def _status_message(self, sections):
        farm = sections.get("farm", {})
        crops = sections.get("crops", [])
        names = ", ".join(
            c.get("crop_name") for c in crops if c.get("crop_name")
        )
        base = f"आपके खेत ({farm.get('village') or ''}, {farm.get('district') or ''}) में फसलें: {names}।"

        if sections.get("weather_unavailable"):
            base += " मौसम की जानकारी अभी उपलब्ध नहीं है।"

        if sections.get("soil_missing"):
            base += " मिट्टी की जानकारी दर्ज करने पर पूरी सलाह मिल सकती है।"

        return base

    # ----------------------------------------------------------
    # WEATHER
    # ----------------------------------------------------------

    def weather(self):
        data = self._weather_data()

        if data is None:
            return {
                "intent": INTENT_WEATHER,
                "status": "UNAVAILABLE",
                "message": MSG_WEATHER_UNAVAILABLE,
                "data": None,
            }

        condition = data.get("condition") or "unknown"
        message = (
            f"{data.get('location')} में अभी मौसम: {condition}, "
            f"तापमान {data.get('temperature')}°C, नमी {data.get('humidity')}%।"
        )
        return {
            "intent": INTENT_WEATHER,
            "status": "OK",
            "message": message,
            "data": data,
        }

    # ----------------------------------------------------------
    # Other intents
    # ----------------------------------------------------------

    def pointer(self, intent):
        return {
            "intent": intent,
            "status": "OK",
            "message": _POINTERS.get(intent, _POINTERS[INTENT_UNKNOWN]),
            "data": None,
        }

    def close(self):
        self.my_farm.close()
