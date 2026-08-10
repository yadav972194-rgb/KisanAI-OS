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
    # Weather
    # ==========================

    WEATHER_LOCATION: str = "Sitapur"
    WEATHER_COUNTRY_CODE: str = "IN"
    WEATHER_CACHE_TTL_SECONDS: int = 600

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

    # ==========================
    # AI Prediction Engine
    # ==========================

    # Server-controlled path to a validated prediction model.
    # Empty = model not configured; the engine then returns a controlled
    # MODEL_NOT_CONFIGURED status instead of a fabricated prediction.
    # NEVER sourced from client input.
    PREDICTION_MODEL_PATH: str = ""

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

        return self


settings = Settings()
