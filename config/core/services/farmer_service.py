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
            district=farmer_data["district"],
            state=farmer_data["state"],
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
            district=farmer_data["district"],
            state=farmer_data["state"],
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
