"""
KisanAI OS
Advisory Service
Version: 1.1.0
"""

from datetime import datetime


class AdvisoryService:
    """KisanAI Agricultural Advisory Service"""

    def __init__(self):
        self.service_name = "KisanAI Advisory Engine"
        self.version = "1.1.0"

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
        """
        Generate basic agricultural advisory
        using crop, soil, weather and disease data.
        """

        crop_name = crop_name.strip()
        disease_name = disease_name.strip()
        disease_severity = disease_severity.strip()

        recommendations = []
        warnings = []

        # ======================================================
        # Soil Analysis
        # ======================================================

        if ph < 5.5:
            recommendations.append(
                "Soil pH is low. Consider applying suitable lime "
                "after proper soil testing."
            )

        elif ph > 8.0:
            recommendations.append(
                "Soil pH is high. Consider organic matter and "
                "appropriate soil amendments."
            )

        else:
            recommendations.append(
                "Soil pH is within a generally suitable range."
            )

        if moisture < 30:
            recommendations.append(
                "Soil moisture is low. Irrigation may be required."
            )

        elif moisture > 80:
            warnings.append(
                "Soil moisture is very high. Avoid unnecessary irrigation."
            )

        else:
            recommendations.append(
                "Soil moisture is currently in a reasonable range."
            )

        # ======================================================
        # Nutrient Analysis
        # ======================================================

        if nitrogen < 40:
            recommendations.append(
                "Nitrogen level appears low. Consider a balanced "
                "nitrogen source based on crop requirement."
            )

        if phosphorus < 20:
            recommendations.append(
                "Phosphorus level appears low. Consider phosphorus "
                "management based on soil test results."
            )

        if potassium < 20:
            recommendations.append(
                "Potassium level appears low. Consider potassium "
                "fertilization according to crop requirement."
            )

        # ======================================================
        # Weather Analysis
        # ======================================================

        condition_lower = condition.lower()

        if temperature >= 35:
            warnings.append(
                "High temperature detected. Monitor crop for heat stress "
                "and maintain appropriate irrigation."
            )

        elif temperature <= 10:
            warnings.append(
                "Low temperature detected. Monitor the crop for cold stress."
            )

        if humidity >= 80:
            warnings.append(
                "High humidity may increase fungal disease risk."
            )

        if "rain" in condition_lower:
            recommendations.append(
                "Rainy conditions detected. Avoid unnecessary irrigation "
                "and monitor field drainage."
            )

        if "cloud" in condition_lower or "overcast" in condition_lower:
            recommendations.append(
                "Cloudy conditions detected. Monitor crop moisture and "
                "disease development."
            )

        if wind_speed >= 20:
            warnings.append(
                "High wind speed detected. Avoid spraying during strong winds."
            )

        # ======================================================
        # Disease Analysis
        # ======================================================

        if disease_name:
            disease_text = disease_name.strip()

            recommendations.append(
                f"Monitor the crop for symptoms of {disease_text}."
            )

            if disease_severity.lower() == "high":
                warnings.append(
                    f"Disease severity is High for {disease_text}. "
                    "Field inspection and appropriate treatment are recommended."
                )

            elif disease_severity.lower() == "medium":
                recommendations.append(
                    f"Disease severity is Medium for {disease_text}. "
                    "Monitor affected plants closely."
                )

        # ======================================================
        # General Crop Advisory
        # ======================================================

        if crop_name:
            recommendations.append(
                f"Continue regular monitoring of {crop_name} "
                "according to its growth stage."
            )

        # ======================================================
        # Final Advisory
        # ======================================================

        if not recommendations:
            recommendations.append(
                "No major advisory generated from the supplied data."
            )

        return {
            "success": True,
            "service": self.service_name,
            "version": self.version,
            "crop": crop_name,
            "soil": {
                "type": soil_type,
                "ph": ph,
                "moisture": moisture,
                "nitrogen": nitrogen,
                "phosphorus": phosphorus,
                "potassium": potassium,
            },
            "weather": {
                "temperature": temperature,
                "humidity": humidity,
                "condition": condition,
                "wind_speed": wind_speed,
            },
            "disease": {
                "name": disease_name,
                "severity": disease_severity,
            },
            "recommendations": recommendations,
            "warnings": warnings,
            "generated_at": datetime.now().isoformat(
                timespec="seconds"
            ),
        }


# ==========================================================
# Local Test
# ==========================================================

if __name__ == "__main__":

    service = AdvisoryService()

    print("=" * 60)
    print("KisanAI Advisory Engine")
    print("=" * 60)

    result = service.generate_advisory(
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
    print("KisanAI Advisory Service Loaded Successfully")
    print("=" * 60)