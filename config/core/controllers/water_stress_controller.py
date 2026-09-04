"""
KisanAI OS
Crop Water Stress Detection Controller

Thin controller for the AI crop-water-stress detection feature.
"""

from config.core.services.water_stress_service import WaterStressService


class WaterStressController:
    """Crop Water Stress Detection Controller"""

    def __init__(self, service=None):
        self.service = service or WaterStressService()

    def detect(self, file, crop_name=None):
        return self.service.detect(file, crop_name)