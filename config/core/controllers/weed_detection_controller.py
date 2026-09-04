"""
KisanAI OS
Weed Detection Controller

Thin controller for the AI weed-detection feature.
"""

from config.core.services.weed_detection_service import (
    WeedDetectionService,
)


class WeedDetectionController:
    """Weed Detection Controller"""

    def __init__(self, service=None):
        self.service = service or WeedDetectionService()

    def detect(self, file, crop_name=None):
        return self.service.detect(file, crop_name)
