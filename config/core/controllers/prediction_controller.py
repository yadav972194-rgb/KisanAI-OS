"""
KisanAI OS
Prediction Controller

Thin controller for the AI Prediction Engine.
"""

from config.core.services.prediction_service import PredictionService


class PredictionController:
    """Prediction Controller"""

    def __init__(self, service=None):
        self.service = service or PredictionService()

    def predict(self, prediction_data):
        prediction_type = prediction_data.pop("prediction_type")
        return self.service.predict(prediction_type, prediction_data)
