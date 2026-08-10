"""
KisanAI OS
Weather Repository
Version: 2.0.0

Stores weather snapshots in the weather table.
"""

from sqlalchemy import select

from config.core.database import SessionLocal
from config.core.models.weather import Weather


class WeatherRepository:
    """Weather Repository"""

    def __init__(self, session=None):
        self.session = session or SessionLocal()

    def _commit(self):
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def save(self, weather: Weather):
        existing = self.session.scalar(
            select(Weather).where(
                Weather.location == weather.location
            )
        )

        if existing is None:
            self.session.add(weather)
        else:
            existing.temperature = weather.temperature
            existing.humidity = weather.humidity
            existing.condition = weather.condition
            existing.wind_speed = weather.wind_speed
            existing.updated_at = weather.updated_at

        self._commit()

    def get_latest(self):
        statement = select(Weather).order_by(
            Weather.weather_id.desc()
        )
        return self.session.scalars(statement).first()

    def get_latest_by_location(self, location):
        """Most recent weather snapshot for a given location."""
        statement = (
            select(Weather)
            .where(Weather.location == location)
            .order_by(Weather.weather_id.desc())
        )
        return self.session.scalars(statement).first()

    def close(self):
        self.session.close()
