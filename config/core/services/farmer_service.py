"""
KisanAI OS
Farmer Service
Version: 5.1.0
"""

from config.core.models.farmer import Farmer
from config.core.repositories.farmer_repository import FarmerRepository


class FarmerService:
    """Farmer Service"""

    def __init__(self, session=None):
        self.repo = FarmerRepository(session)

    def add_farmer(self, farmer_data):

        mobile = farmer_data["mobile"].strip()

        if self.repo.get_farmer_by_mobile(mobile) is not None:
            return {
                "success": False,
                "message": "Mobile number already exists",
            }

        farmer = Farmer(
            farmer_id=farmer_data.get("farmer_id"),
            name=farmer_data["name"],
            mobile=mobile,
            village=farmer_data["village"],
            block=farmer_data.get("block"),
            district=farmer_data["district"],
            state=farmer_data["state"],
            country=farmer_data.get("country") or "India",
            farm_size=farmer_data.get("farm_size"),
        )

        self.repo.insert_farmer(farmer)

        return {
            "success": True,
            "message": "Farmer Added Successfully",
        }

    def get_farmer(self, farmer_id):

        farmer = self.repo.get_farmer_by_id(farmer_id)

        if farmer is None:
            return {
                "success": False,
                "message": "Farmer Not Found",
            }

        return farmer.to_dict()

    def get_farmer_by_mobile(self, mobile):

        farmer = self.repo.get_farmer_by_mobile(str(mobile).strip())

        if farmer is None:
            return {
                "success": False,
                "message": "Farmer Not Found",
            }

        return farmer.to_dict()

    def get_all_farmers(self):
        return [
            farmer.to_dict()
            for farmer in self.repo.get_all_farmers()
        ]

    def get_farmers_for_user(self, user_id):
        """Ownership-scoped list: a farmer account is linked to exactly one
        Farmer row, so this never returns another farmer's record."""
        farm = self.repo.get_farmer_by_user_id(user_id)
        return [farm.to_dict()] if farm is not None else []

    def get_farmer_for_user(self, user_id, farmer_id):
        """Ownership-scoped single read. Returns the same "Not Found"
        result as a missing record so ids cannot be probed."""
        farm = self.repo.get_farmer_by_id_for_user(user_id, farmer_id)

        if farm is None:
            return {
                "success": False,
                "message": "Farmer Not Found",
            }

        return farm.to_dict()

    def get_farmer_by_mobile_for_user(self, user_id, mobile):
        """Ownership-scoped mobile lookup."""
        farm = self.repo.get_farmer_by_mobile_for_user(user_id, mobile)

        if farm is None:
            return {
                "success": False,
                "message": "Farmer Not Found",
            }

        return farm.to_dict()

    def update_farmer(self, farmer_id, farmer_data):

        existing = self.repo.get_farmer_by_id(farmer_id)

        if existing is None:
            return {
                "success": False,
                "message": "Farmer Not Found",
            }

        mobile = farmer_data["mobile"].strip()

        mobile_owner = self.repo.get_farmer_by_mobile(mobile)

        if mobile_owner is not None and mobile_owner.farmer_id != farmer_id:
            return {
                "success": False,
                "message": "Mobile number already exists",
            }

        farmer = Farmer(
            farmer_id=farmer_id,
            name=farmer_data["name"],
            mobile=mobile,
            village=farmer_data["village"],
            block=farmer_data.get("block", existing.block),
            district=farmer_data["district"],
            state=farmer_data["state"],
            country=farmer_data.get("country") or "India",
            farm_size=farmer_data.get("farm_size", existing.farm_size),
        )

        self.repo.update_farmer(farmer)

        return {
            "success": True,
            "message": "Farmer Updated Successfully",
        }

    def delete_farmer(self, farmer_id):

        existing = self.repo.get_farmer_by_id(farmer_id)

        if existing is None:
            return {
                "success": False,
                "message": "Farmer Not Found",
            }

        self.repo.delete_farmer(farmer_id)

        return {
            "success": True,
            "message": "Farmer Deleted Successfully",
        }

    def count_farmers(self):
        return self.repo.count_farmers()

    def close(self):
        self.repo.close()
