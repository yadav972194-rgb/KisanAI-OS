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
    MyFarmCreate,
    MyFarmUpdate,
)
from config.core.schemas.crop import (
    CropCreate,
    CropOut,
    CropUpdate,
    MyFarmCropCreate,
    MyFarmCropUpdate,
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
from config.core.schemas.assistant import (
    AssistantOut,
    AssistantRequest,
)
from config.core.schemas.user import (
    ForgotUsernameRequest,
    OtpRegister,
    OtpRequest,
    OtpRequestOut,
    OtpVerify,
    ResetPasswordRequest,
    Token,
    UsernameOut,
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
    "MyFarmCreate",
    "MyFarmUpdate",
    "CropCreate",
    "CropOut",
    "CropUpdate",
    "MyFarmCropCreate",
    "MyFarmCropUpdate",
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
    "AssistantOut",
    "AssistantRequest",
    "UserCreate",
    "UserOut",
    "UserRoleUpdate",
    "Token",
    "OtpRequest",
    "OtpVerify",
    "OtpRegister",
    "OtpRequestOut",
    "UsernameOut",
    "ForgotUsernameRequest",
    "ResetPasswordRequest",
]
