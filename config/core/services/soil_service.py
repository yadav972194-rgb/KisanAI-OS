"""
KisanAI OS
Soil Service
Version: 5.3.0
"""

from config.core.models.soil import Soil
from config.core.repositories.farmer_repository import FarmerRepository
from config.core.repositories.soil_repository import SoilRepository


class SoilService:
    """Soil Service"""

    def __init__(self, session=None):
        self.repo = SoilRepository(session)
        self.farmer_repo = FarmerRepository(session)

    def _farmer_exists(self, farmer_id):
        return self.farmer_repo.get_farmer_by_id(farmer_id) is not None

    def add_soil(self, soil_data):

        farmer_id = soil_data.get("farmer_id")

        if farmer_id is not None and not self._farmer_exists(farmer_id):
            return {
                "success": False,
                "message": "Farmer Not Found",
            }

        soil = Soil(
            soil_id=soil_data.get("soil_id"),
            farmer_id=farmer_id,
            soil_type=soil_data["soil_type"],
            ph=soil_data["ph"],
            moisture=soil_data["moisture"],
            nitrogen=soil_data["nitrogen"],
            phosphorus=soil_data["phosphorus"],
            potassium=soil_data["potassium"],
        )

        self.repo.add_soil(soil)

        return {
            "success": True,
            "message": "Soil Added Successfully",
        }

    def get_soil(self, soil_id):

        soil = self.repo.get_soil_by_id(soil_id)

        if soil is None:
            return {
                "success": False,
                "message": "Soil Not Found",
            }

        return soil.to_dict()

    def get_all_soils(self):
        return [
            soil.to_dict()
            for soil in self.repo.get_all_soils()
        ]

    def update_soil(self, soil_id, soil_data):

        existing = self.repo.get_soil_by_id(soil_id)

        if existing is None:
            return {
                "success": False,
                "message": "Soil Not Found",
            }

        farmer_id = soil_data.get("farmer_id")

        if farmer_id is None:
            farmer_id = existing.farmer_id

        if farmer_id is not None and not self._farmer_exists(farmer_id):
            return {
                "success": False,
                "message": "Farmer Not Found",
            }

        soil = Soil(
            soil_id=soil_id,
            farmer_id=farmer_id,
            soil_type=soil_data["soil_type"],
            ph=soil_data["ph"],
            moisture=soil_data["moisture"],
            nitrogen=soil_data["nitrogen"],
            phosphorus=soil_data["phosphorus"],
            potassium=soil_data["potassium"],
        )

        self.repo.update_soil(soil)

        return {
            "success": True,
            "message": "Soil Updated Successfully",
        }

    def delete_soil(self, soil_id):

        existing = self.repo.get_soil_by_id(soil_id)

        if existing is None:
            return {
                "success": False,
                "message": "Soil Not Found",
            }

        self.repo.delete_soil(soil_id)

        return {
            "success": True,
            "message": "Soil Deleted Successfully",
        }

    def count_soils(self):
        return self.repo.count_soils()

    def close(self):
        self.repo.close()
        self.farmer_repo.close()
