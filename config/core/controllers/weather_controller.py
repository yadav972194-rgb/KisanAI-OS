"""
KisanAI OS
Weather Controller
Version: 3.0.0
"""

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from config.core.repositories.weather_repository import WeatherRepository
from config.core.services.weather_service import (
    WeatherService,
    WeatherServiceError,
)
from config.core.models.user import User
from config.core.models.farmer import Farmer
from config.core.repositories.farmer_repository import FarmerRepository


class WeatherController:
    """Weather Controller"""

    def __init__(self, session: Session | None = None, current_user: User | None = None):
        self.user = current_user
        # Build a location override from the farmer's profile if available.
        location_override: str | None = None
        if current_user is not None:
            farmer_repo = FarmerRepository(session)
            farmer = farmer_repo.get_farmer_by_user_id(current_user.id)
            if farmer is not None and farmer.village:
                # Prefer village, then block, then district as the location string.
                village = farmer.village.strip()
                block = (farmer.block or "").strip()
                district = (farmer.district or "").strip()
                state = (farmer.state or "").strip()
                country = (farmer.country or "India").strip()
                # Construct a descriptive location string for geocoding.
                # Order: village > block > district, followed by state/country.
                parts = [v for v in [village, block, district] if v]
                if state:
                    parts.append(state)
                if country and country != "India":
                    parts.append(country)
                location_override = " ".join(parts) if parts else None
            # If no farmer profile or no village, we fall back to settings
            # (the existing behaviour) below.
        self.service = WeatherService(
            repo=WeatherRepository(session),
            location=location_override,
        )

    def get_weather(self):
        """Get live weather data, serving from cache when fresh.

        Cache flow:
          1. Fresh cached snapshot for the location -> cache hit.
          2. No cache / expired -> fetch live from Open-Meteo and store.
          3. Live fetch fails but a cache exists -> serve stale cache.
          4. Live fetch fails with no cache -> WeatherServiceError.
        """
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