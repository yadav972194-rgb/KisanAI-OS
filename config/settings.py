"""
KisanAI OS
Application Settings
Version: 2.1.0

Environment-based settings loaded via Pydantic BaseSettings.
Values can be overridden through the .env file or real environment
variables (the latter take precedence). Production deployments must
supply SECRET_KEY and DATABASE_URL explicitly; the app refuses to
start in production mode with weak/placeholder values.
"""

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ==========================
    # Application
    # ==========================

    APP_NAME: str = "KisanAI OS"
    APP_VERSION: str = "3.4.0"
    APP_MODE: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    TIME_ZONE: str = "Asia/Kolkata"
    DEFAULT_LANGUAGE: str = "hi"

    # ==========================
    # Database
    # ==========================
    # SQLite (development) or any SQLAlchemy-supported URL, e.g.
    # PostgreSQL:  postgresql+psycopg://user:password@host:5432/kisanai

    DATABASE_URL: str = "sqlite:///./kisanai.db"

    # ==========================
    # Server (production startup)
    # ==========================

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    # When unset, uvicorn hot-reload follows DEBUG (True in development,
    # False in production). Set explicitly to override.
    RELOAD: bool | None = None

    # ==========================
    # CORS
    # ==========================
    # Comma-separated list of allowed browser origins, e.g.
    #   CORS_ALLOW_ORIGINS=https://app.example.com,https://admin.example.com
    # Empty = CORS disabled (the native Android app does not need CORS).
    # "*" allows any origin but disables credentials.

    CORS_ALLOW_ORIGINS: str = ""

    # ==========================
    # Security / Auth (Phase 3)
    # ==========================

    # MUST be overridden in production. Generate with:
    #   python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    ADMIN_USERNAME: str = ""
    ADMIN_PASSWORD: str = ""

    # ==========================
    # OTP / SMS (Phase 3 OTP auth)
    # ==========================

    # Development convenience: when true the OTP code is never really
    # sent - it is logged and returned in the API response as ``dev_otp``
    # so local flows (and tests) can complete without an SMS provider.
    # MUST be false in production (the production validator enforces this).
    OTP_MOCK: bool = True

    # Real SMS/OTP provider name ("mock", "console" or a future gateway).
    # "console" prints the code to the server log, "mock" is equivalent
    # but also returns dev_otp in the response. Production deployments
    # must configure a real gateway provider.
    OTP_PROVIDER: str = "mock"

    OTP_LENGTH: int = 6
    OTP_TTL_SECONDS: int = 300
    OTP_COOLDOWN_SECONDS: int = 60
    OTP_MAX_ATTEMPTS: int = 5
    # Max OTP requests allowed per mobile number per sliding window.
    OTP_REQUEST_LIMIT: int = 5
    OTP_REQUEST_WINDOW_SECONDS: int = 900
    # Max OTP requests allowed per client IP per sliding window. A secondary
    # control that stops flooding many *different* numbers from one source;
    # the per-mobile limits above remain the primary safeguard.
    OTP_IP_REQUEST_LIMIT: int = 60

    # Production OTP delivery via Twilio (only used when OTP_PROVIDER=twilio).
    # Credentials are server-controlled; NEVER sourced from client input.
    # They are never logged or returned to callers.
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""

    # Sender for Twilio Messages: a Messaging Service SID is preferred;
    # alternatively a From phone number. One of the two is required for
    # the Twilio provider to be considered configured.
    TWILIO_MESSAGING_SERVICE_SID: str = ""
    TWILIO_FROM_NUMBER: str = ""

    # Rate limiting (Phase 11 security): max login attempts per identity
    # before temporary lockout, and the lockout window in seconds.
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_SECONDS: int = 900

    # ==========================
    # Weather
    # ==========================

    WEATHER_LOCATION: str = "Sitapur"
    WEATHER_COUNTRY_CODE: str = "IN"
    WEATHER_CACHE_TTL_SECONDS: int = 600
    # Optional fixed coordinates for WEATHER_LOCATION. When both are set,
    # the geocoding lookup is skipped entirely, removing the most common
    # source of Open-Meteo HTTP 429 (rate-limit) responses. Coordinates
    # take precedence over the live geocoder and are never re-queried.
    WEATHER_LATITUDE: float | None = None
    WEATHER_LONGITUDE: float | None = None

    # ==========================
    # Image Upload
    # ==========================

    UPLOAD_DIR: str = "media/uploads"
    MAX_UPLOAD_SIZE_MB: int = 5

    # ==========================
    # AI Disease Detection
    # ==========================

    # Server-controlled path to a trained disease-detection model.
    # Empty = model not configured; the API then returns a controlled
    # MODEL_NOT_CONFIGURED status instead of a fake diagnosis.
    # NEVER sourced from client input.
    DISEASE_MODEL_PATH: str = ""

    # Optional override for the disease-model labels file (one class name
    # per line, in the model's output order). Empty = auto-derive a
    # sibling "<model>.txt" file next to DISEASE_MODEL_PATH.
    DISEASE_MODEL_LABELS: str = ""

    # Square resize size (pixels) applied to the image before inference.
    DISEASE_MODEL_INPUT_SIZE: int = 224

    # ==========================
    # AI Pest Detection (Phase 1.6)
    # ==========================

    # Server-controlled path to a trained pest-detection model.
    # Empty = model not configured; the API then returns a controlled
    # MODEL_NOT_CONFIGURED status instead of a fake pest identification.
    # NEVER sourced from client input.
    PEST_MODEL_PATH: str = ""

    # Optional override for the pest-model labels file (one class name
    # per line, in the model's output order). Empty = auto-derive a
    # sibling "<model>.txt" file next to PEST_MODEL_PATH.
    PEST_MODEL_LABELS: str = ""

    # Square resize size (pixels) applied to the image before inference.
    PEST_MODEL_INPUT_SIZE: int = 224

    # ==========================
    # AI Weed Detection (Phase 1.8)
    # ==========================

    # Server-controlled path to a trained weed-detection model.
    # Empty = model not configured; the API then returns a controlled
    # MODEL_NOT_CONFIGURED status instead of a fake weed identification.
    # NEVER sourced from client input.
    WEED_MODEL_PATH: str = ""

    # Optional override for the weed-model labels file (one class name
    # per line, in the model's output order). Empty = auto-derive a
    # sibling "<model>.txt" file next to WEED_MODEL_PATH.
    WEED_MODEL_LABELS: str = ""

    # Square resize size (pixels) applied to the image before inference.
    WEED_MODEL_INPUT_SIZE: int = 224

    # ==========================
    # AI Nutrient Deficiency Detection (Phase 1.9)
    # ==========================

    # Server-controlled path to a trained nutrient-deficiency detection
    # model. Empty = model not configured; the API then returns a
    # controlled MODEL_NOT_CONFIGURED status instead of a fake nutrient
    # deficiency identification.
    # NEVER sourced from client input.
    NUTRIENT_DEFICIENCY_MODEL_PATH: str = ""

    # Optional override for the nutrient-deficiency model labels file
    # (one class name per line, in the model's output order). Empty =
    # auto-derive a sibling "<model>.txt" file next to the model.
    NUTRIENT_DEFICIENCY_MODEL_LABELS: str = ""

    # Square resize size (pixels) applied to the image before inference.
    NUTRIENT_DEFICIENCY_MODEL_INPUT_SIZE: int = 224

    # ==========================
    # AI Crop Growth Stage Detection (Phase 1.10)
    # ==========================

    # Server-controlled path to a trained crop-growth-stage detection
    # model. Empty = model not configured; the API then returns a
    # controlled MODEL_NOT_CONFIGURED status instead of a fabricated
    # growth stage.
    # NEVER sourced from client input.
    GROWTH_STAGE_MODEL_PATH: str = ""

    # Optional override for the crop-growth-stage model labels file (one
    # class name per line, in the model's output order). Empty =
    # auto-derive a sibling "<model>.txt" file next to the model.
    GROWTH_STAGE_MODEL_LABELS: str = ""

    # Square resize size (pixels) applied to the image before inference.
    GROWTH_STAGE_MODEL_INPUT_SIZE: int = 224

    # ==========================
    # AI Crop Water Stress Detection (Phase 1.11)
    # ==========================

    # Server-controlled path to a trained crop-water-stress detection
    # model. Empty = model not configured; the API then returns a
    # controlled MODEL_NOT_CONFIGURED status instead of a fabricated
    # water stress level.
    # NEVER sourced from client input.
    WATER_STRESS_MODEL_PATH: str = ""

    # Optional override for the crop-water-stress model labels file (one
    # class name per line, in the model's output order). Empty =
    # auto-derive a sibling "<model>.txt" file next to the model.
    # Labels normally match the stable stress scale: NO_STRESS /
    # MILD_STRESS / MODERATE_STRESS / SEVERE_STRESS.
    WATER_STRESS_MODEL_LABELS: str = ""

    # Square resize size (pixels) applied to the image before inference.
    WATER_STRESS_MODEL_INPUT_SIZE: int = 224

    # ==========================
    # AI Prediction Engine
    # ==========================

    # Server-controlled path to a validated prediction model.
    # Empty = model not configured; the engine then returns a controlled
    # MODEL_NOT_CONFIGURED status instead of a fabricated prediction.
    # NEVER sourced from client input.
    PREDICTION_MODEL_PATH: str = ""

    # Optional override for the prediction-model labels file (one class
    # name per line, in the model's output order) - only used when the
    # model outputs class scores. Empty = auto-derive a sibling
    # "<model>.txt" file next to PREDICTION_MODEL_PATH.
    PREDICTION_MODEL_LABELS: str = ""

    # Reserved for a future image-input prediction model. Feature-based
    # prediction (structured crop/soil/weather context) ignores this.
    PREDICTION_MODEL_INPUT_SIZE: int = 224

    # ==========================
    # Recommendation Engine
    # ==========================

    # Provider selector: "rules" (default, deterministic rule-based, no
    # model required) or a future AI provider name. Non-rule providers
    # need a validated model, otherwise MODEL_NOT_CONFIGURED is returned.
    # NEVER sourced from client input.
    RECOMMENDATION_PROVIDER: str = "rules"

    # Server-controlled path to a validated recommendation model (only
    # relevant when RECOMMENDATION_PROVIDER is not "rules").
    # NEVER sourced from client input.
    RECOMMENDATION_MODEL_PATH: str = ""

    # Optional override for the recommendation-model labels file (one
    # class name per line, in the model's output order) - only used when
    # the model outputs class scores. Empty = auto-derive a sibling
    # "<model>.txt" file next to RECOMMENDATION_MODEL_PATH.
    RECOMMENDATION_MODEL_LABELS: str = ""

    # Reserved for a future image-input recommendation model. Feature-
    # based recommendation (structured crop/soil/weather context) ignores
    # this.
    RECOMMENDATION_MODEL_INPUT_SIZE: int = 224

    # ==========================
    # Advisory Engine
    # ==========================

    # Provider selector: "rules" (default, deterministic rule-based, no
    # model required) or a future AI provider name. Non-rule providers
    # need a validated model, otherwise MODEL_NOT_CONFIGURED is returned.
    # NEVER sourced from client input.
    ADVISORY_PROVIDER: str = "rules"

    # Server-controlled path to a validated advisory model (only
    # relevant when ADVISORY_PROVIDER is not "rules").
    # NEVER sourced from client input.
    ADVISORY_MODEL_PATH: str = ""

    # Optional override for the advisory-model labels file (one class
    # name per line, in the model's output order) - only used when the
    # model outputs class scores. Empty = auto-derive a sibling
    # "<model>.txt" file next to ADVISORY_MODEL_PATH.
    ADVISORY_MODEL_LABELS: str = ""

    # Reserved for a future image-input advisory model. Feature-
    # based advisory (structured crop/soil/weather context) ignores
    # this.
    ADVISORY_MODEL_INPUT_SIZE: int = 224

    # ==========================
    # Derived helpers
    # ==========================

    @property
    def cors_origins_list(self) -> list[str]:
        """Parsed CORS origins. Empty list = CORS middleware disabled."""
        return [
            origin.strip()
            for origin in self.CORS_ALLOW_ORIGINS.split(",")
            if origin.strip()
        ]

    @model_validator(mode="after")
    def _validate_production(self) -> "Settings":
        """Fail fast on unsafe production configuration.

        Development mode keeps the permissive defaults so local work is
        unaffected; production requires a strong SECRET_KEY and an
        explicit DATABASE_URL. Never auto-generate secrets here - a
        boot-time error is the safe outcome.
        """
        is_production = (
            self.APP_MODE.strip().lower() == "production" or not self.DEBUG
        )

        if not is_production:
            return self

        if (
            not self.SECRET_KEY
            or self.SECRET_KEY == "change-me-in-production"
            or len(self.SECRET_KEY) < 32
        ):
            raise ValueError(
                "SECRET_KEY must be set to a strong value "
                "(at least 32 characters) in production mode"
            )

        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL must be set in production mode")

        if self.RELOAD:
            raise ValueError(
                "RELOAD must be false/disabled in production mode"
            )

        if self.OTP_MOCK:
            raise ValueError(
                "OTP_MOCK must be false in production mode"
            )

        if (self.OTP_PROVIDER or "").lower() in {"mock", "console"}:
            raise ValueError(
                "OTP_PROVIDER must be a real SMS gateway in production mode"
            )

        return self


settings = Settings()
