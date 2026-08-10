"""
KisanAI OS
Disease Detection Controller

Thin controller for the AI disease-detection feature.
"""

from config.core.services.disease_detection_service import (
    DiseaseDetectionService,
)


class DiseaseDetectionController:
    """Disease Detection Controller"""

    def __init__(self, service=None):
        self.service = service or DiseaseDetectionService()

    def detect(self, file, crop_name=None):
        return self.service.detect(file, crop_name)
