"""
KisanAI OS
Recommendation Controller

Thin controller for the Recommendation Engine.
"""

from config.core.services.recommendation_service import (
    RecommendationService,
)


class RecommendationController:
    """Recommendation Controller"""

    def __init__(self, service=None):
        self.service = service or RecommendationService()

    def recommend(self, data):
        return self.service.recommend(data)
