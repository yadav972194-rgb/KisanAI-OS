"""
KisanAI OS
Crop Growth Stage Detection Controller

Thin controller for the AI crop-growth-stage detection feature.
"""

from config.core.services.growth_stage_service import GrowthStageService


class GrowthStageController:
    """Crop Growth Stage Detection Controller"""

    def __init__(self, service=None):
        self.service = service or GrowthStageService()

    def detect(self, file, crop_name=None):
        return self.service.detect(file, crop_name)
