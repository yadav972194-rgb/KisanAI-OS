"""
KisanAI OS
Advisory Controller
Version: 1.1.0
"""

from config.core.services.advisory_service import AdvisoryService


class AdvisoryController:
    """KisanAI Agricultural Advisory Controller"""

    def __init__(self, service=None):
        self.service = service or AdvisoryService()

    def generate_advisory(
        self,
        crop_name: str,
        soil_type: str,
        ph: float,
        moisture: float,
        nitrogen: int,
        phosphorus: int,
        potassium: int,
        temperature: float,
        humidity: float,
        condition: str,
        wind_speed: float,
        disease_name: str = "",
        disease_severity: str = "",
    ):
        return self.service.generate_advisory(
            crop_name=crop_name,
            soil_type=soil_type,
            ph=ph,
            moisture=moisture,
            nitrogen=nitrogen,
            phosphorus=phosphorus,
            potassium=potassium,
            temperature=temperature,
            humidity=humidity,
            condition=condition,
            wind_speed=wind_speed,
            disease_name=disease_name,
            disease_severity=disease_severity,
        )


# ==========================================================
# Local Test
# ==========================================================

if __name__ == "__main__":

    controller = AdvisoryController()

    print("=" * 60)
    print("KisanAI Advisory Controller")
    print("=" * 60)

    result = controller.generate_advisory(
        crop_name="Wheat",
        soil_type="Loamy",
        ph=6.8,
        moisture=45,
        nitrogen=50,
        phosphorus=25,
        potassium=30,
        temperature=30.3,
        humidity=81,
        condition="Overcast",
        wind_speed=6.0,
        disease_name="",
        disease_severity="",
    )

    print()
    print(result)
    print()
    print("KisanAI Advisory Controller Loaded Successfully")
    print("=" * 60)