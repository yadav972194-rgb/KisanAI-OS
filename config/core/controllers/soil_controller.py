"""
KisanAI OS
Soil Controller
Version: 4.0.0
"""

from config.core.services.soil_service import SoilService


class SoilController:
    """Soil Controller"""

    def __init__(self, session=None):
        self.service = SoilService(session)

    def create_soil(self, soil_data):
        return self.service.add_soil(soil_data)

    def get_soil(self, soil_id):
        return self.service.get_soil(soil_id)

    def get_all_soils(self):
        return self.service.get_all_soils()

    def update_soil(self, soil_id, soil_data):
        return self.service.update_soil(
            soil_id,
            soil_data,
        )

    def delete_soil(self, soil_id):
        return self.service.delete_soil(soil_id)

    def count_soils(self):
        return self.service.count_soils()

    def close(self):
        self.service.close()


if __name__ == "__main__":

    controller = SoilController()

    test_id = 9996

    soil_data = {
        "soil_id": test_id,
        "soil_type": "Loamy Test",
        "ph": 6.8,
        "moisture": 45.5,
        "nitrogen": 80,
        "phosphorus": 40,
        "potassium": 60,
    }

    print("=" * 50)
    print("Soil Controller Test")
    print("=" * 50)

    print()
    print("CREATE:")
    print(controller.create_soil(soil_data))

    print()
    print("GET:")
    print(controller.get_soil(test_id))

    print()
    print("GET ALL:")
    print(controller.get_all_soils())

    update_data = {
        "soil_type": "Clay Loam Updated",
        "ph": 7.1,
        "moisture": 50,
        "nitrogen": 85,
        "phosphorus": 45,
        "potassium": 65,
    }

    print()
    print("UPDATE:")
    print(controller.update_soil(test_id, update_data))

    print()
    print("GET AFTER UPDATE:")
    print(controller.get_soil(test_id))

    print()
    print("DELETE:")
    print(controller.delete_soil(test_id))

    print()
    print("GET AFTER DELETE:")
    print(controller.get_soil(test_id))

    print()
    print("FINAL COUNT:")
    print(controller.count_soils())

    print()
    print("Soil Controller Test Completed")

    controller.close()