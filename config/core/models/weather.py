"""
KisanAI OS
Weather Model
Version: 2.0.0
"""

from datetime import datetime

from sqlalchemy import Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from config.core.database import Base


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Weather(Base):
    """Weather Model"""

    __tablename__ = "weather"
    __table_args__ = (
        UniqueConstraint("location", name="uq_weather_location"),
    )

    weather_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    location: Mapped[str] = mapped_column(String(100))
    temperature: Mapped[float] = mapped_column(Float)
    humidity: Mapped[int] = mapped_column(Integer)
    condition: Mapped[str] = mapped_column(String(50))
    wind_speed: Mapped[float] = mapped_column(Float)
    updated_at: Mapped[str] = mapped_column(String(19), default=_now)

    def to_dict(self):
        return {
            "location": self.location,
            "temperature": self.temperature,
            "humidity": self.humidity,
            "condition": self.condition,
            "wind_speed": self.wind_speed,
            "updated_at": self.updated_at,
        }
