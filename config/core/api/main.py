"""
KisanAI OS
Main API
Version: 3.4.0
"""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException

from config.constants import ROLE_ADMIN
from config.core.api.auth import get_current_user, require_role
from config.core.controllers.advisory_controller import AdvisoryController
from config.core.controllers.assistant_controller import AssistantController
from config.core.controllers.farmer_controller import FarmerController
from config.core.controllers.crop_controller import CropController
from config.core.controllers.disease_controller import DiseaseController
from config.core.controllers.disease_detection_controller import (
    DiseaseDetectionController,
)
from config.core.controllers.pest_detection_controller import (
    PestDetectionController,
)
from config.core.controllers.weed_detection_controller import (
    WeedDetectionController,
)
from config.core.controllers.nutrient_deficiency_controller import (
    NutrientDeficiencyController,
)
from config.core.controllers.growth_stage_controller import (
    GrowthStageController,
)
from config.core.controllers.my_farm_controller import MyFarmController
from config.core.controllers.prediction_controller import PredictionController
from config.core.controllers.recommendation_controller import (
    RecommendationController,
)
from config.core.controllers.soil_controller import SoilController
from config.core.controllers.upload_controller import UploadController
from config.core.controllers.weather_controller import WeatherController
from config.core.controllers.water_stress_controller import WaterStressController
from config.core.api.auth_routes import (
    router as auth_router,
    user_service as auth_user_service,
)
from config.core.api.location_routes import router as location_router
from config.core.database import engine, get_db
from config.core.exceptions import (
    AppError,
    ConflictError,
    NotFoundError,
)
from config.core.logger import logger
from config.core.models.user import User
from config.settings import settings
from config.core.schemas import (
    AdvisoryOut,
    AdvisoryRequest,
    AssistantOut,
    AssistantRequest,
    CropCreate,
    CropOut,
    CropUpdate,
    DiseaseCreate,
    DiseaseDetectionOut,
    DiseaseOut,
    DiseaseUpdate,
    FarmerCreate,
    FarmerOut,
    FarmerUpdate,
    GrowthStageOut,
    MessageOut,
    MyFarmCreate,
    MyFarmCropCreate,
    MyFarmCropUpdate,
    MyFarmUpdate,
    NutrientDeficiencyOut,
    PestDetectionOut,
    PredictionOut,
    PredictionRequest,
    RecommendationOut,
    RecommendationRequest,
    SoilCreate,
    SoilOut,
    SoilUpdate,
    UploadOut,
    UserOut,
    UserRoleUpdate,
    WaterStressOut,
    WeatherOut,
    WeedDetectionOut,
)
from config.core.services.user_service import UserService
from config.core.services.disease_detection_service import (
    DiseaseDetectionError,
)
from config.core.services.pest_detection_service import (
    PestDetectionError,
)
from config.core.services.weed_detection_service import (
    WeedDetectionError,
)
from config.core.services.nutrient_deficiency_service import (
    NutrientDeficiencyError,
)
from config.core.services.growth_stage_service import GrowthStageError
from config.core.services.water_stress_service import WaterStressError
from config.core.services.prediction_service import PredictionError
from config.core.services.recommendation_service import RecommendationError
from config.core.services.upload_service import UploadError
from config.core.services.weather_service import WeatherServiceError


# ==========================================================
# Controllers
# ==========================================================

advisory = AdvisoryController()


# ==========================================================
# FastAPI Application
# ==========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    auth_user_service.bootstrap_admin()
    yield
    auth_user_service.close()


app = FastAPI(
    title="KisanAI OS API",
    version="3.4.0",
    description="KisanAI Operating System",
    lifespan=lifespan,
    # API reference docs are development conveniences. They are disabled
    # in production (DEBUG=false) to reduce the exposed attack surface.
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

# CORS is opt-in: the native Android app does not send browser preflight
# requests, so no origins are allowed by default. Configure
# CORS_ALLOW_ORIGINS (comma-separated) when a web frontend is deployed.
_origins = settings.cors_origins_list
if _origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_credentials="*" not in _origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth_router)

# Location hierarchy: Country -> State -> District -> Block/Tehsil -> Village
app.include_router(location_router)


# ==========================================================
# Error Mapping Helpers
# ==========================================================

def _ok(result):
    """Convert a service dict result into an HTTP response.

    Services return {"success": False, "message": ...} to signal a
    failed operation; translate those into proper HTTP exceptions so
    FastAPI returns a real error status instead of HTTP 200.
    """
    if isinstance(result, dict) and result.get("success") is False:
        message = result.get("message", "Request failed")

        if "Not Found" in message:
            raise NotFoundError(message)

        if "already" in message:
            raise ConflictError(message)

        raise AppError(message)

    return result


# ==========================================================
# Global Exception Handlers
# ==========================================================

@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.message, "code": exc.code},
    )


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.message, "code": exc.code},
    )


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.message, "code": exc.code},
    )


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Validation failed",
            "code": "VALIDATION_ERROR",
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
):
    """Shape every HTTPException into the stable error envelope.

    Route-specific exceptions (auth ``_fail``, role checks, upload errors)
    already carry ``{"success": False, "message": ..., "code": ...}`` in
    ``detail``; those are passed through unchanged. Bare exceptions (e.g. a
    route not found, or an unauthenticated request) receive a code based on
    the status so the app can classify them.
    """
    detail = exc.detail
    if isinstance(detail, dict):
        content = detail
    elif exc.status_code == 401:
        content = {
            "success": False,
            "message": detail or "Not authenticated",
            "code": "SESSION_EXPIRED",
        }
    elif exc.status_code == 404:
        content = {
            "success": False,
            "message": detail or "Not Found",
            "code": "NOT_FOUND",
        }
    elif exc.status_code == 405:
        content = {
            "success": False,
            "message": detail or "Method not allowed",
            "code": "VALIDATION_ERROR",
        }
    else:
        content = {
            "success": False,
            "message": detail or "Request failed",
            "code": "SERVER_ERROR",
        }
    # Keep the established ``{"detail": {...}}`` envelope so existing clients
    # and tests that read ``body["detail"]["message"]`` keep working.
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": content},
    )


@app.exception_handler(IntegrityError)
async def integrity_handler(request: Request, exc: IntegrityError):
    logger.warning("IntegrityError on %s %s: %s",
                   request.method, request.url.path, exc.orig)
    return JSONResponse(
        status_code=409,
        content={
            "success": False,
            "message": "Resource already exists",
            "code": "CONFLICT",
        },
    )


@app.exception_handler(WeatherServiceError)
async def weather_error_handler(request: Request, exc: WeatherServiceError):
    logger.warning("WeatherServiceError on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=502,
        content={
            "success": False,
            "message": str(exc),
            "code": "SERVER_ERROR",
        },
    )


@app.exception_handler(DiseaseDetectionError)
async def disease_detection_error_handler(
    request: Request, exc: DiseaseDetectionError
):
    logger.warning(
        "DiseaseDetectionError on %s: %s", request.url.path, exc
    )
    return JSONResponse(
        status_code=502,
        content={
            "success": False,
            "message": str(exc),
            "code": "MODEL_INVALID",
        },
    )


@app.exception_handler(PestDetectionError)
async def pest_detection_error_handler(
    request: Request, exc: PestDetectionError
):
    logger.warning(
        "PestDetectionError on %s: %s", request.url.path, exc
    )
    return JSONResponse(
        status_code=502,
        content={
            "success": False,
            "message": str(exc),
            "code": "MODEL_INVALID",
        },
    )


@app.exception_handler(WeedDetectionError)
async def weed_detection_error_handler(
    request: Request, exc: WeedDetectionError
):
    logger.warning(
        "WeedDetectionError on %s: %s", request.url.path, exc
    )
    return JSONResponse(
        status_code=502,
        content={
            "success": False,
            "message": str(exc),
            "code": "MODEL_INVALID",
        },
    )


@app.exception_handler(NutrientDeficiencyError)
async def nutrient_deficiency_error_handler(
    request: Request, exc: NutrientDeficiencyError
):
    logger.warning(
        "NutrientDeficiencyError on %s: %s", request.url.path, exc
    )
    return JSONResponse(
        status_code=502,
        content={
            "success": False,
            "message": str(exc),
            "code": "MODEL_INVALID",
        },
    )


@app.exception_handler(GrowthStageError)
async def growth_stage_error_handler(
    request: Request, exc: GrowthStageError
):
    logger.warning(
        "GrowthStageError on %s: %s", request.url.path, exc
    )
    return JSONResponse(
        status_code=502,
        content={
            "success": False,
            "message": str(exc),
            "code": "MODEL_INVALID",
        },
    )


@app.exception_handler(WaterStressError)
async def water_stress_error_handler(
    request: Request, exc: WaterStressError
):
    logger.warning(
        "WaterStressError on %s: %s", request.url.path, exc
    )
    return JSONResponse(
        status_code=502,
        content={
            "success": False,
            "message": str(exc),
            "code": "MODEL_INVALID",
        },
    )


@app.exception_handler(PredictionError)
async def prediction_error_handler(request: Request, exc: PredictionError):
    logger.warning("PredictionError on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=502,
        content={
            "success": False,
            "message": str(exc),
            "code": "SERVER_ERROR",
        },
    )


@app.exception_handler(RecommendationError)
async def recommendation_error_handler(
    request: Request, exc: RecommendationError
):
    logger.warning("RecommendationError on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=502,
        content={
            "success": False,
            "message": str(exc),
            "code": "SERVER_ERROR",
        },
    )


@app.exception_handler(Exception)
async def unhandled_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s",
                     request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "code": "SERVER_ERROR",
        },
    )


# ==========================================================
# Home API
# ==========================================================

@app.get("/")
def home():
    return {
        "success": True,
        "message": "Welcome to KisanAI OS",
        "version": "3.4.0",
    }


# ==========================================================
# Health API (production readiness)
# ==========================================================

@app.get("/health", tags=["health"])
def health():
    """Lightweight liveness/readiness probe.

    Verifies database connectivity without leaking any connection
    details, credentials, hostnames or error internals. Returns 200
    when the service and database are reachable, 503 otherwise.
    """
    db_ok = True
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:  # pragma: no cover - defensive
        logger.exception("Health check database probe failed")
        db_ok = False

    if not db_ok:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unavailable",
                "service": settings.APP_NAME,
                "version": settings.APP_VERSION,
            },
        )

    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


# ==========================================================
# Admin: User Role Management (Phase 5.9 Expert Role Activation)
# ==========================================================

@app.get("/api/admin/users", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(ROLE_ADMIN)),
):
    return UserService(db).get_all_users()


@app.patch("/api/admin/users/{user_id}/role", response_model=MessageOut)
def update_user_role(
    user_id: int,
    data: UserRoleUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(ROLE_ADMIN)),
):
    return _ok(UserService(db).set_user_role(user_id, data.role))


# ==========================================================
# Farmer CRUD API
# ==========================================================

@app.post("/api/farmers", response_model=MessageOut)
def create_farmer(
    data: FarmerCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(ROLE_ADMIN)),
):
    return _ok(FarmerController(db).create_farmer(data.model_dump()))


@app.get("/api/farmers", response_model=list[FarmerOut])
def get_all_farmers(
    db: Session = Depends(get_db),
    _current: User = Depends(get_current_user),
):
    return FarmerController(db).get_all_farmers()


@app.get("/api/farmers/by-mobile/{mobile}", response_model=FarmerOut)
def get_farmer_by_mobile(
    mobile: str,
    db: Session = Depends(get_db),
    _current: User = Depends(get_current_user),
):
    return _ok(FarmerController(db).get_farmer_by_mobile(mobile))


@app.get("/api/farmers/{farmer_id}", response_model=FarmerOut)
def get_farmer(
    farmer_id: int,
    db: Session = Depends(get_db),
    _current: User = Depends(get_current_user),
):
    return _ok(FarmerController(db).get_farmer(farmer_id))


@app.put("/api/farmers/{farmer_id}", response_model=MessageOut)
def update_farmer(
    farmer_id: int,
    data: FarmerUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(ROLE_ADMIN)),
):
    return _ok(FarmerController(db).update_farmer(
        farmer_id,
        data.model_dump(),
    ))


@app.delete("/api/farmers/{farmer_id}", response_model=MessageOut)
def delete_farmer(
    farmer_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(ROLE_ADMIN)),
):
    return _ok(FarmerController(db).delete_farmer(farmer_id))


# ==========================================================
# My Farm API (self-service for the authenticated farmer)
# ==========================================================

@app.get("/api/my-farm", response_model=FarmerOut)
def get_my_farm(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the logged-in user's own farm profile (404 when unset)."""
    return _ok(MyFarmController(db).get_farm(current_user))


@app.post("/api/my-farm", response_model=MessageOut)
def create_my_farm(
    data: MyFarmCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create the logged-in user's farm. Name and mobile come from the
    linked user account; the farmer supplies location and farm size."""
    return _ok(MyFarmController(db).create_farm(
        current_user,
        data.model_dump(),
    ))


@app.put("/api/my-farm", response_model=MessageOut)
def update_my_farm(
    data: MyFarmUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the logged-in user's farm. Only supplied fields change."""
    return _ok(MyFarmController(db).update_farm(
        current_user,
        data.model_dump(exclude_unset=True),
    ))


@app.delete("/api/my-farm", response_model=MessageOut)
def delete_my_farm(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete the logged-in user's farm and its dependent records."""
    return _ok(MyFarmController(db).delete_farm(current_user))


@app.get("/api/my-farm/crops", response_model=list[CropOut])
def get_my_farm_crops(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List crops planted on the logged-in user's farm."""
    return _ok(MyFarmController(db).get_crops(current_user))


@app.post("/api/my-farm/crops", response_model=MessageOut)
def create_my_farm_crop(
    data: MyFarmCropCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a crop to the logged-in user's farm."""
    return _ok(MyFarmController(db).add_crop(
        current_user,
        data.model_dump(),
    ))


@app.put("/api/my-farm/crops/{crop_id}", response_model=MessageOut)
def update_my_farm_crop(
    crop_id: int,
    data: MyFarmCropUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update one of the logged-in user's own crops (404 if it belongs
    to a different farm)."""
    return _ok(MyFarmController(db).update_crop(
        current_user,
        crop_id,
        data.model_dump(),
    ))


@app.delete("/api/my-farm/crops/{crop_id}", response_model=MessageOut)
def delete_my_farm_crop(
    crop_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete one of the logged-in user's own crops."""
    return _ok(MyFarmController(db).delete_crop(current_user, crop_id))


# ==========================================================
# Crop CRUD API
# ==========================================================

@app.post("/api/crops", response_model=MessageOut)
def create_crop(
    data: CropCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(ROLE_ADMIN)),
):
    return _ok(CropController(db).create_crop(data.model_dump()))


@app.get("/api/crops", response_model=list[CropOut])
def get_all_crops(
    farmer_id: int | None = None,
    db: Session = Depends(get_db),
    _current: User = Depends(get_current_user),
):
    if farmer_id is not None:
        return _ok(CropController(db).get_crops_by_farmer(farmer_id))

    return CropController(db).get_all_crops()


@app.get("/api/crops/{crop_id}", response_model=CropOut)
def get_crop(
    crop_id: int,
    db: Session = Depends(get_db),
    _current: User = Depends(get_current_user),
):
    return _ok(CropController(db).get_crop(crop_id))


@app.put("/api/crops/{crop_id}", response_model=MessageOut)
def update_crop(
    crop_id: int,
    data: CropUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(ROLE_ADMIN)),
):
    return _ok(CropController(db).update_crop(
        crop_id,
        data.model_dump(),
    ))


@app.delete("/api/crops/{crop_id}", response_model=MessageOut)
def delete_crop(
    crop_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(ROLE_ADMIN)),
):
    return _ok(CropController(db).delete_crop(crop_id))


# ==========================================================
# Disease CRUD API
# ==========================================================

@app.post("/api/diseases", response_model=MessageOut)
def create_disease(
    data: DiseaseCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(ROLE_ADMIN)),
):
    return _ok(DiseaseController(db).create_disease(
        data.model_dump()
    ))


@app.get("/api/diseases", response_model=list[DiseaseOut])
def get_all_diseases(
    db: Session = Depends(get_db),
    _current: User = Depends(get_current_user),
):
    return DiseaseController(db).get_all_diseases()


@app.get("/api/diseases/{disease_id}", response_model=DiseaseOut)
def get_disease(
    disease_id: int,
    db: Session = Depends(get_db),
    _current: User = Depends(get_current_user),
):
    return _ok(DiseaseController(db).get_disease(disease_id))


@app.put("/api/diseases/{disease_id}", response_model=MessageOut)
def update_disease(
    disease_id: int,
    data: DiseaseUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(ROLE_ADMIN)),
):
    return _ok(DiseaseController(db).update_disease(
        disease_id,
        data.model_dump(),
    ))


@app.delete("/api/diseases/{disease_id}", response_model=MessageOut)
def delete_disease(
    disease_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(ROLE_ADMIN)),
):
    return _ok(DiseaseController(db).delete_disease(disease_id))


# ==========================================================
# Soil CRUD API
# ==========================================================

@app.post("/api/soils", response_model=MessageOut)
def create_soil(
    data: SoilCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(ROLE_ADMIN)),
):
    return _ok(SoilController(db).create_soil(data.model_dump()))


@app.get("/api/soils", response_model=list[SoilOut])
def get_all_soils(
    db: Session = Depends(get_db),
    _current: User = Depends(get_current_user),
):
    return SoilController(db).get_all_soils()


@app.get("/api/soils/{soil_id}", response_model=SoilOut)
def get_soil(
    soil_id: int,
    db: Session = Depends(get_db),
    _current: User = Depends(get_current_user),
):
    return _ok(SoilController(db).get_soil(soil_id))


@app.put("/api/soils/{soil_id}", response_model=MessageOut)
def update_soil(
    soil_id: int,
    data: SoilUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(ROLE_ADMIN)),
):
    return _ok(SoilController(db).update_soil(
        soil_id,
        data.model_dump(),
    ))


@app.delete("/api/soils/{soil_id}", response_model=MessageOut)
def delete_soil(
    soil_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(ROLE_ADMIN)),
):
    return _ok(SoilController(db).delete_soil(soil_id))


# ==========================================================
# Weather API
# ==========================================================

@app.get("/api/weather", response_model=WeatherOut)
def get_weather(
    db: Session = Depends(get_db),
    _current: User = Depends(get_current_user),
):
    return WeatherController(session=db, current_user=_current).get_weather()


# ==========================================================
# Advisory API
# ==========================================================

@app.post("/api/advisory", response_model=AdvisoryOut)
def generate_advisory(
    data: AdvisoryRequest,
    _current: User = Depends(get_current_user),
):
    return advisory.generate_advisory(
        **data.model_dump()
    )


# ==========================================================
# Image Upload API
# ==========================================================

@app.post("/api/uploads", response_model=UploadOut)
def upload_image(
    file: UploadFile = File(...),
    _admin: User = Depends(require_role(ROLE_ADMIN)),
):
    """Upload an image (JPG/JPEG/PNG, max 5 MB).

    Files are stored under the configured media directory with a
    random safe filename; the client filename is never trusted or
    reused. Admin-only, matching all other write endpoints.
    """
    try:
        return UploadController().upload_image(file)
    except UploadError as error:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": str(error)},
        )


# ==========================================================
# AI Disease Detection API
# ==========================================================

@app.post("/api/disease-detection", response_model=DiseaseDetectionOut)
def detect_disease(
    file: UploadFile = File(...),
    crop_name: str | None = Form(default=None),
    _current: User = Depends(get_current_user),
):
    """Analyse an uploaded crop image (JPG/JPEG/PNG, max 5 MB).

    The image is validated by the existing secure upload layer, then
    passed to the configured model provider. No trained model is
    bundled, so the API returns a controlled ``MODEL_NOT_CONFIGURED``
    status - never a fabricated diagnosis.

    Open to any authenticated user (farmers are the intended users);
    the optional ``crop_name`` form field is passed to the provider as
    crop context.
    """
    try:
        return DiseaseDetectionController().detect(file, crop_name)
    except UploadError as error:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": str(error)},
        )


# ==========================================================
# AI Pest Detection API
# ==========================================================

@app.post("/api/pest/detect", response_model=PestDetectionOut)
def detect_pest(
    file: UploadFile = File(...),
    crop_name: str | None = Form(default=None),
    _current: User = Depends(get_current_user),
):
    """Analyse an uploaded crop image (JPG/JPEG/PNG, max 5 MB).

    The image is validated by the existing secure upload layer, then
    passed to the configured pest-model provider. No trained model is
    bundled, so the API returns a controlled ``MODEL_NOT_CONFIGURED``
    status - never a fabricated pest identification.

    Open to any authenticated user (farmers are the intended users);
    the optional ``crop_name`` form field is passed to the provider as
    crop context.
    """
    try:
        return PestDetectionController().detect(file, crop_name)
    except UploadError as error:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": str(error)},
        )


# ==========================================================
# AI Weed Detection API
# ==========================================================

@app.post("/api/weed/detect", response_model=WeedDetectionOut)
def detect_weed(
    file: UploadFile = File(...),
    crop_name: str | None = Form(default=None),
    _current: User = Depends(get_current_user),
):
    """Analyse an uploaded crop image (JPG/JPEG/PNG, max 5 MB).

    The image is validated by the existing secure upload layer, then
    passed to the configured weed-model provider. No trained model is
    bundled, so the API returns a controlled ``MODEL_NOT_CONFIGURED``
    status - never a fabricated weed identification.

    Open to any authenticated user (farmers are the intended users);
    the optional ``crop_name`` form field is passed to the provider as
    crop context.
    """
    try:
        return WeedDetectionController().detect(file, crop_name)
    except UploadError as error:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": str(error)},
        )


# ==========================================================
# AI Nutrient Deficiency Detection API
# ==========================================================

@app.post(
    "/api/nutrient-deficiency/detect",
    response_model=NutrientDeficiencyOut,
)
def detect_nutrient_deficiency(
    file: UploadFile = File(...),
    crop_name: str | None = Form(default=None),
    _current: User = Depends(get_current_user),
):
    """Analyse an uploaded crop image (JPG/JPEG/PNG, max 5 MB).

    The image is validated by the existing secure upload layer, then
    passed to the configured nutrient-deficiency model provider. No
    trained model is bundled, so the API returns a controlled
    ``MODEL_NOT_CONFIGURED`` status - never a fabricated nutrient
    deficiency identification.

    Open to any authenticated user (farmers are the intended users);
    the optional ``crop_name`` form field is passed to the provider as
    crop context.
    """
    try:
        return NutrientDeficiencyController().detect(file, crop_name)
    except UploadError as error:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": str(error)},
        )


# ==========================================================
# AI Crop Growth Stage Detection API
# ==========================================================

@app.post("/api/growth-stage/detect", response_model=GrowthStageOut)
def detect_growth_stage(
    file: UploadFile = File(...),
    crop_name: str | None = Form(default=None),
    _current: User = Depends(get_current_user),
):
    """Analyse an uploaded crop image (JPG/JPEG/PNG, max 5 MB).

    The image is validated by the existing secure upload layer, then
    passed to the configured crop-growth-stage model provider. No
    trained model is bundled, so the API returns a controlled
    ``MODEL_NOT_CONFIGURED`` status - never a fabricated growth stage.

    Open to any authenticated user (farmers are the intended users);
    the optional ``crop_name`` form field is passed to the provider as
    crop context.
    """
    try:
        return GrowthStageController().detect(file, crop_name)
    except UploadError as error:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": str(error)},
        )


# ==========================================================
# AI Crop Water Stress Detection API (Phase 1.11)
# ==========================================================

@app.post("/api/water-stress/detect", response_model=WaterStressOut)
def detect_water_stress(
    file: UploadFile = File(...),
    crop_name: str | None = Form(default=None),
    _current: User = Depends(get_current_user),
):
    """Analyse an uploaded crop image (JPG/JPEG/PNG, max 5 MB).

    The image is validated by the existing secure upload layer, then
    passed to the configured crop-water-stress model provider. No
    trained model is bundled, so the API returns a controlled
    ``MODEL_NOT_CONFIGURED`` status - never a fabricated water stress
    level.

    Open to any authenticated user (farmers are the intended users);
    the optional ``crop_name`` form field is passed to the provider as
    crop context.
    """
    try:
        return WaterStressController().detect(file, crop_name)
    except UploadError as error:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": str(error)},
        )


# ==========================================================
# AI Prediction Engine API
# ==========================================================

@app.post("/api/predictions", response_model=PredictionOut)
def create_prediction(
    data: PredictionRequest,
    _current: User = Depends(get_current_user),
):
    """Run a prediction for structured agricultural input.

    Open to any authenticated user. No validated model is bundled, so
    the engine returns a controlled ``MODEL_NOT_CONFIGURED`` status with
    ``result=None`` and ``confidence=None`` - never a fabricated
    prediction. ``prediction_type`` is required and must be supported
    (crop_yield, soil_analysis); unknown or malformed input is rejected.
    """
    return PredictionController().predict(data.model_dump())


# ==========================================================
# Recommendation Engine API
# ==========================================================

@app.post("/api/recommendations", response_model=RecommendationOut)
def generate_recommendation(
    data: RecommendationRequest,
    _current: User = Depends(get_current_user),
):
    """Generate a structured agricultural recommendation.

    Open to any authenticated user. Combines only verified context from
    the request (crop / soil / weather / optional disease). Missing
    required context returns ``INSUFFICIENT_DATA`` listing what is
    missing; an unavailable AI recommendation model returns
    ``MODEL_NOT_CONFIGURED``. No fabricated data, confidence or dosage
    is ever returned.
    """
    return RecommendationController().recommend(data.model_dump())


# ==========================================================
# Assistant / Intent Router API
# ==========================================================

@app.post("/api/assistant", response_model=AssistantOut)
def assistant_query(
    data: AssistantRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Answer a free-text farmer query honestly.

    The query is routed to a stable intent (CROP_STATUS, WEATHER,
    MY_FARM, DISEASE_DETECTION, CROP_ADVICE, SOIL, AI_ADVICE, AUTH,
    HELP or UNKNOWN). CROP_STATUS answers ONLY from verified data: the
    authenticated user's stored farm and crops, live-or-cached weather,
    and any soil/disease context supplied in the request. Missing data
    returns INSUFFICIENT_DATA with a clear Hindi message - never a
    guessed status. Other intents return honest pointers to the
    matching screens.
    """
    return AssistantController(db).handle(
        current_user,
        data.text,
        soil=data.soil,
        disease=data.disease,
    )


# ==========================================================
# Local Test
# ==========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("KisanAI OS API")
    print("=" * 60)

    print()
    print("Home:")
    print(home())

    print()
    print("Weather:")
    try:
        print(get_weather(next(get_db())))
    except WeatherServiceError as error:
        print("Weather Error:", error)

    print()
    print("KisanAI OS API Loaded Successfully")
    print("=" * 60)
