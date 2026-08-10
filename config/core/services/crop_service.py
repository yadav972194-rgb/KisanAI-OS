"""
KisanAI OS
Crop Service
Version: 5.2.0
"""

from config.core.models.crop import Crop
from config.core.repositories.crop_repository import CropRepository
from config.core.repositories.farmer_repository import FarmerRepository


class CropService:
    """Crop Service"""

    def __init__(self, session=None):
        self.repo = CropRepository(session)
        self.farmer_repo = FarmerRepository(session)

    def _farmer_exists(self, farmer_id):
        return self.farmer_repo.get_farmer_by_id(farmer_id) is not None

    def add_crop(self, crop_data):

        farmer_id = crop_data.get("farmer_id")

        if farmer_id is not None and not self._farmer_exists(farmer_id):
            return {
                "success": False,
                "message": "Farmer Not Found",
            }

        crop_name = crop_data["crop_name"]

        if self.repo.get_crop_by_name(crop_name) is not None:
            return {
                "success": False,
                "message": "Crop name already exists",
            }

        crop = Crop(
            crop_id=crop_data.get("crop_id"),
            farmer_id=farmer_id,
            crop_name=crop_name,
            season=crop_data["season"],
            duration_days=crop_data["duration_days"],
            water_requirement=crop_data["water_requirement"],
        )

        self.repo.add_crop(crop)

        return {
            "success": True,
            "message": "Crop Added Successfully",
        }

    def get_crop(self, crop_id):

        crop = self.repo.get_crop_by_id(crop_id)

        if crop is None:
            return {
                "success": False,
                "message": "Crop Not Found",
            }

        return crop.to_dict()

    def get_all_crops(self):
        return [
            crop.to_dict()
            for crop in self.repo.get_all_crops()
        ]

    def get_crops_by_farmer(self, farmer_id):

        if not self._farmer_exists(farmer_id):
            return {
                "success": False,
                "message": "Farmer Not Found",
            }

        return [
            crop.to_dict()
            for crop in self.repo.get_crops_by_farmer(farmer_id)
        ]

    def update_crop(self, crop_id, crop_data):

        existing = self.repo.get_crop_by_id(crop_id)

        if existing is None:
            return {
                "success": False,
                "message": "Crop Not Found",
            }

        farmer_id = crop_data.get("farmer_id")

        if farmer_id is None:
            farmer_id = existing.farmer_id

        if farmer_id is not None and not self._farmer_exists(farmer_id):
            return {
                "success": False,
                "message": "Farmer Not Found",
            }

        crop_name = crop_data["crop_name"]

        name_owner = self.repo.get_crop_by_name(crop_name)

        if name_owner is not None and name_owner.crop_id != crop_id:
            return {
                "success": False,
                "message": "Crop name already exists",
            }

        crop = Crop(
            crop_id=crop_id,
            farmer_id=farmer_id,
            crop_name=crop_name,
            season=crop_data["season"],
            duration_days=crop_data["duration_days"],
            water_requirement=crop_data["water_requirement"],
        )

        self.repo.update_crop(crop)

        return {
            "success": True,
            "message": "Crop Updated Successfully",
        }

    def delete_crop(self, crop_id):

        existing = self.repo.get_crop_by_id(crop_id)

        if existing is None:
            return {
                "success": False,
                "message": "Crop Not Found",
            }

        self.repo.delete_crop(crop_id)

        return {
            "success": True,
            "message": "Crop Deleted Successfully",
        }

    def count_crops(self):
        return self.repo.count_crops()

    def close(self):
        self.repo.close()
        self.farmer_repo.close()
