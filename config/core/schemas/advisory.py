"""
KisanAI OS
Advisory Schemas
"""

from pydantic import BaseModel


class AdvisoryRequest(BaseModel):
    crop_name: str
    soil_type: str
    ph: float
    moisture: float
    nitrogen: int
    phosphorus: int
    potassium: int
    temperature: float
    humidity: float
    condition: str
    wind_speed: float
    disease_name: str = ""
    disease_severity: str = ""


class SoilSummary(BaseModel):
    type: str
    ph: float
    moisture: float
    nitrogen: int
    phosphorus: int
    potassium: int


class WeatherSummary(BaseModel):
    temperature: float
    humidity: float
    condition: str
    wind_speed: float


class DiseaseSummary(BaseModel):
    name: str
    severity: str


class AdvisoryOut(BaseModel):
    success: bool
    service: str
    version: str
    crop: str
    soil: SoilSummary
    weather: WeatherSummary
    disease: DiseaseSummary
    recommendations: list[str]
    warnings: list[str]
    generated_at: str
