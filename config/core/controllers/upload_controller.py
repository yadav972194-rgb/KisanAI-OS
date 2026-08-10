"""
KisanAI OS
Upload Controller

Thin controller for the image upload feature.
"""

from config.core.services.upload_service import UploadService


class UploadController:
    """Upload Controller"""

    def __init__(self, service=None):
        self.service = service or UploadService()

    def upload_image(self, file):
        return self.service.save_image(file.filename, file)
