"""
KisanAI OS
My Farm Controller
Version: 1.0.0
"""

from config.core.models.user import User
from config.core.services.my_farm_service import MyFarmService


class MyFarmController:
    """My Farm Controller - self-service farm management."""

    def __init__(self, session=None):
        self.service = MyFarmService(session)

    def get_farm(self, user: User):
        return self.service.get_farm(user.id)

    def create_farm(self, user: User, farm_data):
        return self.service.create_farm(user, farm_data)

    def update_farm(self, user: User, farm_data):
        return self.service.update_farm(user.id, farm_data)

    def delete_farm(self, user: User):
        return self.service.delete_farm(user.id)

    def get_crops(self, user: User):
        return self.service.get_crops(user.id)

    def add_crop(self, user: User, crop_data):
        return self.service.add_crop(user.id, crop_data)

    def update_crop(self, user: User, crop_id, crop_data):
        return self.service.update_crop(user.id, crop_id, crop_data)

    def delete_crop(self, user: User, crop_id):
        return self.service.delete_crop(user.id, crop_id)

    def close(self):
        self.service.close()
