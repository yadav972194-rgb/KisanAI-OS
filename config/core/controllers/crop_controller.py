"""
KisanAI OS
Crop Controller
Version: 4.0.0
"""

from config.core.services.crop_service import CropService


class CropController:
    """Crop Controller"""

    def __init__(self, session=None):
        self.service = CropService(session)

    def create_crop(self, crop_data):
        return self.service.add_crop(crop_data)

    def get_crop(self, crop_id):
        return self.service.get_crop(crop_id)

    def get_all_crops(self):
        return self.service.get_all_crops()

    def get_crops_by_farmer(self, farmer_id):
        return self.service.get_crops_by_farmer(farmer_id)

    def update_crop(self, crop_id, crop_data):
        return self.service.update_crop(
            crop_id,
            crop_data,
        )

    def delete_crop(self, crop_id):
        return self.service.delete_crop(crop_id)

    def count_crops(self):
        return self.service.count_crops()

    def close(self):
        self.service.close()


if __name__ == "__main__":

    controller = CropController()

    test_id = 9996

    crop_data = {
        "crop_id": test_id,
        "crop_name": "Maize Test",
        "season": "Kharif",
        "duration_days": 110,
        "water_requirement": "Medium",
    }

    update_data = {
        "crop_name": "Maize Test Updated",
        "season": "Kharif",
        "duration_days": 115,
        "water_requirement": "Medium",
    }

    print("=" * 50)
    print("Crop Controller Test")
    print("=" * 50)

    print()
    print("CREATE:")
    print(controller.create_crop(crop_data))

    print()
    print("GET:")
    print(controller.get_crop(test_id))

    print()
    print("GET ALL:")
    print(controller.get_all_crops())

    print()
    print("UPDATE:")
    print(controller.update_crop(test_id, update_data))

    print()
    print("GET AFTER UPDATE:")
    print(controller.get_crop(test_id))

    print()
    print("DELETE:")
    print(controller.delete_crop(test_id))

    print()
    print("GET AFTER DELETE:")
    print(controller.get_crop(test_id))

    print()
    print("FINAL COUNT:")
    print(controller.count_crops())

    print()
    print("Crop Controller Test Completed")

    controller.close()