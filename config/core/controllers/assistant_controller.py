"""
KisanAI OS
Assistant Controller

Routs a farmer's free-text question to a stable intent and answers it
honestly from verified data only:

    - CROP_STATUS is answered only from the authenticated user's farm +
      crops (stored) plus weather (live/cached) and any soil/disease
      context supplied in the request. When the farm or crops are
      missing the response says so plainly; it never fabricates a
      crop status.
    - WEATHER is answered from the live/cached weather snapshot.
    - All other intents return honest pointers to the matching screens
      (help), never fake results.

Safety contract mirrors the recommendation engine: no fabricated data,
no invented confidence, no dosage advice.
"""

from config.core.logger import logger
from config.core.models.user import User
from config.core.services.assistant_service import AssistantService
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


class AssistantController:
    """Assistant Controller"""

    def __init__(self, session=None, service=None):
        self.service = service or AssistantService(session)

    def handle(self, user: User, text: str, soil=None, disease=None):
        """Route the query and produce an honest response.

        Never raises for a bad query; unknown intents receive a
        helpful pointer message instead.
        """
        intent = classify_intent(text).intent

        if intent == INTENT_CROP_STATUS:
            return self.service.crop_status(
                user, soil=soil, disease=disease
            )

        if intent == INTENT_WEATHER:
            return self.service.weather()

        return self.service.pointer(intent)