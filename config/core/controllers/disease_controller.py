"""
KisanAI OS
Disease Controller
Version: 4.0.0
"""

from config.core.services.disease_service import DiseaseService


class DiseaseController:
    """Disease Controller"""

    def __init__(self, session=None):
        self.service = DiseaseService(session)

    def create_disease(self, disease_data):
        return self.service.create_disease(disease_data)

    def get_disease(self, disease_id):
        return self.service.get_disease(disease_id)

    def get_all_diseases(self):
        return self.service.get_all_diseases()

    def update_disease(self, disease_id, disease_data):
        return self.service.update_disease(
            disease_id,
            disease_data,
        )

    def delete_disease(self, disease_id):
        return self.service.delete_disease(disease_id)

    def count_diseases(self):
        return self.service.count_diseases()

    def close(self):
        self.service.close()


if __name__ == "__main__":

    controller = DiseaseController()

    test_id = 9996

    disease_data = {
        "disease_id": test_id,
        "crop_name": "Wheat",
        "disease_name": "Rust Test",
        "symptoms": "Yellow spots on leaves",
        "solution": "Spray recommended fungicide",
        "severity": "Medium",
    }

    print("=" * 50)
    print("Disease Controller Test")
    print("=" * 50)

    print()
    print("CREATE:")
    print(controller.create_disease(disease_data))

    print()
    print("GET:")
    print(controller.get_disease(test_id))

    print()
    print("GET ALL:")
    print(controller.get_all_diseases())

    update_data = {
        "crop_name": "Wheat",
        "disease_name": "Wheat Rust Updated",
        "symptoms": "Yellow and brown spots on leaves",
        "solution": (
            "Spray recommended fungicide "
            "and remove infected leaves"
        ),
        "severity": "High",
    }

    print()
    print("UPDATE:")
    print(
        controller.update_disease(
            test_id,
            update_data,
        )
    )

    print()
    print("GET AFTER UPDATE:")
    print(controller.get_disease(test_id))

    print()
    print("DELETE:")
    print(controller.delete_disease(test_id))

    print()
    print("GET AFTER DELETE:")
    print(controller.get_disease(test_id))

    print()
    print("FINAL COUNT:")
    print(controller.count_diseases())

    print()
    print("Disease Controller Test Completed")

    controller.close()