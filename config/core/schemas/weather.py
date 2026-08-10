"""
KisanAI OS
Weather Schemas
"""

from pydantic import BaseModel


class WeatherOut(BaseModel):
    location: str
    temperature: float
    humidity: int
    condition: str
    wind_speed: float
    updated_at: str
