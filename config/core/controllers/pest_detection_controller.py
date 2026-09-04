"""
KisanAI OS
Pest Detection Controller

Thin controller for the AI pest-detection feature.
"""

from config.core.services.pest_detection_service import (
    PestDetectionService,
)


class PestDetectionController:
    """Pest Detection Controller"""

    def __init__(self, service=None):
        self.service = service or PestDetectionService()

    def detect(self, file, crop_name=None):
        return self.service.detect(file, crop_name)
