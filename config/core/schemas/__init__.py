"""
KisanAI OS
Pydantic Schemas Package
"""

from config.core.schemas.common import (
    ApiResponse,
    ErrorOut,
    MessageOut,
)
from config.core.schemas.farmer import (
    FarmerCreate,
    FarmerOut,
    FarmerUpdate,
)
from config.core.schemas.crop import (
    CropCreate,
    CropOut,
    CropUpdate,
)
from config.core.schemas.soil import (
    SoilCreate,
    SoilOut,
    SoilUpdate,
)
from config.core.schemas.disease import (
    DiseaseCreate,
    DiseaseOut,
    DiseaseUpdate,
)
from config.core.schemas.weather import WeatherOut
from config.core.schemas.upload import UploadOut
from config.core.schemas.disease_detection import DiseaseDetectionOut
from config.core.schemas.prediction import (
    PredictionOut,
    PredictionRequest,
    SoilContext,
    WeatherContext,
)
from config.core.schemas.recommendation import (
    RecommendationItem,
    RecommendationOut,
    RecommendationRequest,
)
from config.core.schemas.advisory import (
    AdvisoryOut,
    AdvisoryRequest,
)
from config.core.schemas.user import (
    Token,
    UserCreate,
    UserOut,
    UserRoleUpdate,
)

__all__ = [
    "ApiResponse",
    "ErrorOut",
    "MessageOut",
    "FarmerCreate",
    "FarmerOut",
    "FarmerUpdate",
    "CropCreate",
    "CropOut",
    "CropUpdate",
    "SoilCreate",
    "SoilOut",
    "SoilUpdate",
    "DiseaseCreate",
    "DiseaseOut",
    "DiseaseUpdate",
    "WeatherOut",
    "UploadOut",
    "DiseaseDetectionOut",
    "PredictionOut",
    "PredictionRequest",
    "SoilContext",
    "WeatherContext",
    "RecommendationItem",
    "RecommendationOut",
    "RecommendationRequest",
    "AdvisoryOut",
    "AdvisoryRequest",
    "UserCreate",
    "UserOut",
    "UserRoleUpdate",
    "Token",
]
