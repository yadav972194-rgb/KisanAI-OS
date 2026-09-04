"""
KisanAI OS
Nutrient Deficiency Detection Controller

Thin controller for the AI nutrient-deficiency detection feature.
"""

from config.core.services.nutrient_deficiency_service import (
    NutrientDeficiencyService,
)


class NutrientDeficiencyController:
    """Nutrient Deficiency Detection Controller"""

    def __init__(self, service=None):
        self.service = service or NutrientDeficiencyService()

    def detect(self, file, crop_name=None):
        return self.service.detect(file, crop_name)
