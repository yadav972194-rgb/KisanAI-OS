"""
KisanAI OS
My Farm Service
Version: 1.0.0

Self-service farm management for the authenticated farmer.

A farmer account is linked to exactly one Farmer row through
``farmers.user_id``. All operations below resolve the farm from the
current user id, so a farmer can never read, edit or delete someone
else's farm or crops.
"""

from config.core.models.crop import Crop
from config.core.models.farmer import Farmer
from config.core.models.user import User
from config.core.repositories.crop_repository import CropRepository
from config.core.repositories.farmer_repository import FarmerRepository


class MyFarmService:
    """My Farm Service"""

    def __init__(self, session=None):
        self.farmer_repo = FarmerRepository(session)
        self.crop_repo = CropRepository(session)

    # ==========================================================
    # Farm profile
    # ==========================================================

    def _farm_or_error(self, user_id):
        farm = self.farmer_repo.get_farmer_by_user_id(user_id)
        if farm is None:
            return None, {
                "success": False,
                "message": "Farm Not Found",
            }
        return farm, None

    def get_farm(self, user_id):
        farm, error = self._farm_or_error(user_id)
        if error is not None:
            return error
        return farm.to_dict()

    def create_farm(self, user: User, farm_data):
        existing = self.farmer_repo.get_farmer_by_user_id(user.id)
        if existing is not None:
            return {
                "success": False,
                "message": "Farm already exists",
            }

        mobile = (user.mobile or "").strip()

        farm = Farmer(
            user_id=user.id,
            name=(user.full_name or user.username).strip(),
            mobile=mobile,
            village=farm_data["village"],
            block=farm_data.get("block"),
            district=farm_data["district"],
            state=farm_data["state"],
            country=farm_data.get("country") or "India",
            farm_size=farm_data.get("farm_size"),
        )

        self.farmer_repo.insert_farmer(farm)

        return {
            "success": True,
            "message": "Farm Created Successfully",
        }

    def update_farm(self, user_id, farm_data):
        farm, error = self._farm_or_error(user_id)
        if error is not None:
            return error

        if "village" in farm_data and farm_data["village"] is not None:
            farm.village = farm_data["village"]
        if "block" in farm_data:
            farm.block = farm_data["block"]
        if "district" in farm_data and farm_data["district"] is not None:
            farm.district = farm_data["district"]
        if "state" in farm_data and farm_data["state"] is not None:
            farm.state = farm_data["state"]
        if "country" in farm_data and farm_data["country"] is not None:
            farm.country = farm_data["country"]
        if "farm_size" in farm_data:
            farm.farm_size = farm_data["farm_size"]

        self.farmer_repo.update_farmer(farm)

        return {
            "success": True,
            "message": "Farm Updated Successfully",
        }

    def delete_farm(self, user_id):
        farm, error = self._farm_or_error(user_id)
        if error is not None:
            return error

        self.farmer_repo.delete_farmer(farm.farmer_id)

        return {
            "success": True,
            "message": "Farm Deleted Successfully",
        }

    # ==========================================================
    # Farm crops
    # ==========================================================

    def get_crops(self, user_id):
        farm, error = self._farm_or_error(user_id)
        if error is not None:
            return error

        return [
            crop.to_dict()
            for crop in self.crop_repo.get_crops_by_farmer(farm.farmer_id)
        ]

    def add_crop(self, user_id, crop_data):
        farm, error = self._farm_or_error(user_id)
        if error is not None:
            return error

        crop_name = crop_data["crop_name"]

        if self.crop_repo.get_crop_by_farmer_and_name(
            farm.farmer_id, crop_name
        ) is not None:
            return {
                "success": False,
                "message": "Crop already added to this farm",
            }

        crop = Crop(
            farmer_id=farm.farmer_id,
            crop_name=crop_name,
            season=crop_data["season"],
            duration_days=crop_data["duration_days"],
            water_requirement=crop_data["water_requirement"],
        )

        self.crop_repo.add_crop(crop)

        return {
            "success": True,
            "message": "Crop Added Successfully",
        }

    def update_crop(self, user_id, crop_id, crop_data):
        farm, error = self._farm_or_error(user_id)
        if error is not None:
            return error

        crop = self.crop_repo.get_crop_by_id(crop_id)

        if crop is None or crop.farmer_id != farm.farmer_id:
            return {
                "success": False,
                "message": "Crop Not Found",
            }

        crop_name = crop_data["crop_name"]

        name_owner = self.crop_repo.get_crop_by_farmer_and_name(
            farm.farmer_id, crop_name
        )

        if name_owner is not None and name_owner.crop_id != crop_id:
            return {
                "success": False,
                "message": "Crop already added to this farm",
            }

        crop.crop_name = crop_name
        crop.season = crop_data["season"]
        crop.duration_days = crop_data["duration_days"]
        crop.water_requirement = crop_data["water_requirement"]

        self.crop_repo.update_crop(crop)

        return {
            "success": True,
            "message": "Crop Updated Successfully",
        }

    def delete_crop(self, user_id, crop_id):
        farm, error = self._farm_or_error(user_id)
        if error is not None:
            return error

        crop = self.crop_repo.get_crop_by_id(crop_id)

        if crop is None or crop.farmer_id != farm.farmer_id:
            return {
                "success": False,
                "message": "Crop Not Found",
            }

        self.crop_repo.delete_crop(crop_id)

        return {
            "success": True,
            "message": "Crop Deleted Successfully",
        }

    def close(self):
        self.farmer_repo.close()
        self.crop_repo.close()
