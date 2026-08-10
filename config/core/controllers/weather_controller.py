"""
KisanAI OS
Weather Controller
Version: 2.0.0
"""

from config.core.repositories.weather_repository import WeatherRepository
from config.core.services.weather_service import (
    WeatherService,
    WeatherServiceError,
)


class WeatherController:
    """Weather Controller"""

    def __init__(self, session=None):
        self.service = WeatherService(
            repo=WeatherRepository(session)
        )

    def get_weather(self):
        """Get live weather data."""

        return self.service.get_weather()


if __name__ == "__main__":
    controller = WeatherController()

    print("=" * 50)
    print("Weather Controller Loaded Successfully")
    print("=" * 50)

    try:
        print()
        print(controller.get_weather())

    except WeatherServiceError as error:
        print()
        print("Weather Error:")
        print(error)