"""
KisanAI OS
Weather Service
Version: 3.0.0

Live weather provider:
Open-Meteo
"""

import json
import threading
import time
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from config.core.logger import logger
from config.core.models.weather import Weather
from config.core.repositories.weather_repository import WeatherRepository
from config.settings import settings


class WeatherServiceError(Exception):
    """Weather service error."""


# Serializes provider fetches across concurrent callers (single-flight).
_fetch_lock = threading.Lock()


class WeatherService:
    """Live Weather Service"""

    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
    WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, repo=None, location: str | None = None):
        # If a location string is provided (e.g. from the farmer's profile),
        # use it for geocoding; otherwise fall back to the configured default.
        self.location = location or settings.WEATHER_LOCATION
        self.country_code = settings.WEATHER_COUNTRY_CODE
        self.cache_ttl_seconds = settings.WEATHER_CACHE_TTL_SECONDS
        self.repo = repo or WeatherRepository()
        self._coordinates = None

    def _get_json(self, url, params, retries=2):
        """GET request and return JSON response.

        Open-Meteo responds with HTTP 429 when a caller exceeds its fair-use
        rate limit. A short retry-with-backoff absorbs transient throttling;
        persistent throttling still fails so the caller can fall back to the
        stale weather cache.
        """

        query_string = urlencode(params)
        request_url = f"{url}?{query_string}"

        request = Request(
            request_url,
            headers={
                "User-Agent": "KisanAI-OS/3.0",
                "Accept": "application/json",
            },
        )

        attempt = 0

        while True:
            try:
                with urlopen(request, timeout=10) as response:
                    return json.loads(
                        response.read().decode("utf-8")
                    )

            except HTTPError as error:
                if error.code == 429 and attempt < retries:
                    attempt += 1
                    time.sleep(2 ** attempt)
                    continue

                if error.code == 429:
                    raise WeatherServiceError(
                        "Weather provider is rate limited; retrying later"
                    ) from error

                raise WeatherServiceError(
                    f"Weather provider HTTP error: {error.code}"
                ) from error

            except URLError as error:
                raise WeatherServiceError(
                    "Weather provider is unreachable"
                ) from error

            except TimeoutError as error:
                raise WeatherServiceError(
                    "Weather provider request timed out"
                ) from error

            except json.JSONDecodeError as error:
                raise WeatherServiceError(
                    "Invalid response from weather provider"
                ) from error

            except Exception as error:
                raise WeatherServiceError(
                    "Unable to fetch weather data"
                ) from error

    def _get_coordinates(self):
        """Get latitude and longitude for the configured location.

        Fixed coordinates from settings are used when available; otherwise
        the geocoder is queried once and the result is cached in memory so
        the (rate-limited) geocoding endpoint is not hit on every refresh.
        """

        latitude = settings.WEATHER_LATITUDE
        longitude = settings.WEATHER_LONGITUDE

        if latitude is not None and longitude is not None:
            return latitude, longitude, self.location

        if self._coordinates is None:
            self._coordinates = self._geocode()

        return self._coordinates

    def _geocode_candidates(self):
        """Return location strings to try, most specific first.

        The composite farm location (e.g. "Rampur Sitapur Uttar Pradesh")
        often cannot be resolved by the geocoder as a whole, so we fall
        back through the individual parts in order (village, block,
        district, state), each of which the geocoder can usually resolve.
        """

        parts = [p for p in self.location.split() if p]

        if len(parts) <= 1:
            return [self.location]

        ordered = [self.location]
        seen = {self.location.lower()}

        for part in parts:
            key = part.lower()
            if key not in seen:
                seen.add(key)
                ordered.append(part)

        return ordered

    def _geocode(self):
        """Resolve the configured location through the geocoding API.

        The full location string is tried first; when the geocoder returns
        no results, progressively simpler fallbacks (prefixes, then the
        individual parts) are attempted so a village/district still
        resolves even when the composite string does not.
        """

        last_error: str | None = None

        for candidate in self._geocode_candidates():
            data = self._get_json(
                self.GEOCODING_URL,
                {
                    "name": candidate,
                    "count": 1,
                    "language": "en",
                    "format": "json",
                    "countryCode": self.country_code,
                },
            )

            results = data.get("results", [])

            if results:
                self.location = candidate
                location = results[0]
                break

            last_error = f"Location not found: {candidate}"

        else:
            raise WeatherServiceError(
                last_error or f"Location not found: {self.location}"
            )

        try:
            return (
                location["latitude"],
                location["longitude"],
                location.get("name", self.location),
            )
        except KeyError as error:
            raise WeatherServiceError(
                "Invalid location data received"
            ) from error

    def _weather_condition(self, weather_code):
        """Convert WMO weather code to readable condition."""

        conditions = {
            0: "Clear Sky",
            1: "Mainly Clear",
            2: "Partly Cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Rime Fog",
            51: "Light Drizzle",
            53: "Moderate Drizzle",
            55: "Dense Drizzle",
            56: "Light Freezing Drizzle",
            57: "Dense Freezing Drizzle",
            61: "Light Rain",
            63: "Moderate Rain",
            65: "Heavy Rain",
            66: "Light Freezing Rain",
            67: "Heavy Freezing Rain",
            71: "Light Snow",
            73: "Moderate Snow",
            75: "Heavy Snow",
            77: "Snow Grains",
            80: "Light Rain Showers",
            81: "Moderate Rain Showers",
            82: "Violent Rain Showers",
            85: "Light Snow Showers",
            86: "Heavy Snow Showers",
            95: "Thunderstorm",
            96: "Thunderstorm with Hail",
            99: "Thunderstorm with Heavy Hail",
        }

        return conditions.get(
            weather_code,
            "Unknown",
        )

    def _is_fresh(self, updated_at):
        """True if the cached snapshot is still within the TTL window."""
        try:
            parsed = datetime.strptime(
                updated_at, "%Y-%m-%d %H:%M:%S"
            )
        except (TypeError, ValueError):
            return False

        age_seconds = (datetime.now() - parsed).total_seconds()
        return age_seconds <= self.cache_ttl_seconds

    def _fetch_live(self):
        """Fetch live weather from the provider and return a Weather model."""
        latitude, longitude, _ = (
            self._get_coordinates()
        )

        data = self._get_json(
            self.WEATHER_URL,
            {
                "latitude": latitude,
                "longitude": longitude,
                "current": (
                    "temperature_2m,"
                    "relative_humidity_2m,"
                    "weather_code,"
                    "wind_speed_10m"
                ),
                "timezone": "auto",
            },
        )

        current = data.get("current", {})

        temperature = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")
        weather_code = current.get("weather_code")
        wind_speed = current.get("wind_speed_10m")

        if temperature is None:
            raise WeatherServiceError(
                "Temperature data unavailable"
            )

        if humidity is None:
            raise WeatherServiceError(
                "Humidity data unavailable"
            )

        if weather_code is None:
            raise WeatherServiceError(
                "Weather condition unavailable"
            )

        if wind_speed is None:
            raise WeatherServiceError(
                "Wind speed data unavailable"
            )

        return Weather(
            location=self.location,
            temperature=temperature,
            humidity=humidity,
            condition=self._weather_condition(
                weather_code
            ),
            wind_speed=wind_speed,
            updated_at=datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        )

    def get_weather(self):
        """Return weather data, serving from cache when fresh.

        Cache flow:
          1. Fresh cached snapshot for the location -> cache hit.
          2. No cache / expired -> fetch live from Open-Meteo and store.
          3. Live fetch fails but a cache exists -> serve stale cache.
          4. Live fetch fails with no cache -> WeatherServiceError.

        Concurrent callers are serialized with a process-wide lock
        (single-flight): when several requests arrive at the same moment
        and the cache is cold, only one actually queries the provider;
        the rest then hit the just-written cache.
        """
        with _fetch_lock:
            cached = self.repo.get_latest_by_location(self.location)

            if cached is not None and self._is_fresh(cached.updated_at):
                logger.info("Weather cache hit for %s", self.location)
                return cached.to_dict()

            try:
                weather = self._fetch_live()
            except WeatherServiceError as error:
                if cached is not None:
                    logger.warning(
                        "Weather fetch failed (%s); serving cached data",
                        error,
                    )
                    return cached.to_dict()
                raise

            self.repo.save(weather)

            return weather.to_dict()


if __name__ == "__main__":
    service = WeatherService()

    print("=" * 50)
    print("KisanAI Weather Service")
    print("=" * 50)

    try:
        print()
        print(service.get_weather())

    except WeatherServiceError as error:
        print()
        print("Weather Error:")
        print(error)