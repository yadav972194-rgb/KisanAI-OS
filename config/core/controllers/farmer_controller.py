"""
KisanAI OS
Farmer Controller
Version: 3.1.0
"""

from config.core.services.farmer_service import FarmerService


class FarmerController:
    """Farmer Controller"""

    def __init__(self, session=None):
        self.service = FarmerService(session)

    def create_farmer(self, farmer_data):
        return self.service.add_farmer(farmer_data)

    def get_farmer(self, farmer_id):
        return self.service.get_farmer(farmer_id)

    def get_farmer_by_mobile(self, mobile):
        return self.service.get_farmer_by_mobile(mobile)

    def get_all_farmers(self):
        return self.service.get_all_farmers()

    def update_farmer(self, farmer_id, farmer_data):
        return self.service.update_farmer(
            farmer_id,
            farmer_data,
        )

    def delete_farmer(self, farmer_id):
        return self.service.delete_farmer(farmer_id)

    def count_farmers(self):
        return self.service.count_farmers()

    def close(self):
        self.service.close()


if __name__ == "__main__":

    controller = FarmerController()

    test_id = 9993

    farmer_data = {
        "farmer_id": test_id,
        "name": "Farmer Controller Test",
        "mobile": "9876543210",
        "village": "Test Village",
        "district": "Lakhimpur Kheri",
        "state": "Uttar Pradesh",
    }

    print("=" * 50)
    print("Farmer Controller Test")
    print("=" * 50)

    print()
    print("CREATE:")
    print(controller.create_farmer(farmer_data))

    print()
    print("GET:")
    print(controller.get_farmer(test_id))

    print()
    print("GET ALL:")
    print(controller.get_all_farmers())

    update_data = {
        "name": "Farmer Controller Updated",
        "mobile": "9876543211",
        "village": "Updated Village",
        "district": "Lakhimpur Kheri",
        "state": "Uttar Pradesh",
    }

    print()
    print("UPDATE:")
    print(controller.update_farmer(test_id, update_data))

    print()
    print("GET AFTER UPDATE:")
    print(controller.get_farmer(test_id))

    print()
    print("DELETE:")
    print(controller.delete_farmer(test_id))

    print()
    print("GET AFTER DELETE:")
    print(controller.get_farmer(test_id))

    print()
    print("FINAL COUNT:")
    print(controller.count_farmers())

    print()
    print("Farmer Controller Test Completed")

    controller.close()