"""
Configuration module for Prison Roll Call Server.

Provides Settings and FaceRecognitionPolicy configuration models
with environment variable support and validation.
"""
import secrets
from functools import lru_cache
from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class FaceRecognitionPolicy(BaseModel):
    """
    Face recognition policy configuration.

    Defines confidence thresholds and quality requirements for
    face detection, enrollment, and verification operations.
    """

    # Verification (during roll call)
    verification_threshold: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Minimum confidence for face verification",
    )

    # Enrollment (capturing reference photo)
    enrollment_quality_threshold: float = Field(
        default=0.80,
        ge=0.0,
        le=1.0,
        description="Minimum quality for enrollment photos",
    )

    # Auto-accept (no officer confirmation needed)
    auto_accept_threshold: float = Field(
        default=0.92,
        ge=0.0,
        le=1.0,
        description="Confidence threshold for automatic acceptance",
    )

    # Force manual review (low confidence)
    manual_review_threshold: float = Field(
        default=0.60,
        ge=0.0,
        le=1.0,
        description="Confidence threshold requiring manual review",
    )

    # Environmental adjustments
    low_light_adjustment: float = Field(
        default=-0.05,
        ge=-0.2,
        le=0.0,
        description="Threshold adjustment for low light conditions",
    )

    # Facility identifier
    facility_id: str = Field(
        default="default", description="Unique facility identifier"
    )

    @model_validator(mode="after")
    def validate_threshold_order(self) -> "FaceRecognitionPolicy":
        """Validate that thresholds are in logical order."""
        if self.auto_accept_threshold <= self.verification_threshold:
            raise ValueError(
                "auto_accept_threshold must be greater than verification_threshold"
            )
        if self.verification_threshold <= self.manual_review_threshold:
            raise ValueError(
                "verification_threshold must be greater than manual_review_threshold"
            )
        return self


class Settings(BaseSettings):
    """
    Application settings with environment variable support.

    Configuration can be overridden via environment variables.
    Example: HOST=192.168.1.1 PORT=9000 python main.py
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application metadata
    app_name: str = Field(default="Prison Roll Call Server")
    app_version: str = Field(default="0.1.0")

    # Server configuration
    host: str = Field(default="0.0.0.0", description="Server bind address")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    debug: bool = Field(default=False, description="Enable debug mode")

    # Database configuration
    database_url: str = Field(
        default="data/prison_rollcall.db",
        description="Database connection URL",
    )

    # Security
    api_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        min_length=32,
        description="API authentication key",
    )

    # CORS configuration
    cors_origins: list[str] = Field(
        default=["*"], description="Allowed CORS origins"
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
    )

    # ML Model configuration
    model_path: Path = Field(
        default_factory=lambda: Path("app/ml/models"),
        description="Path to ML model files",
    )

    # Face recognition policy
    policy: FaceRecognitionPolicy = Field(
        default_factory=FaceRecognitionPolicy,
        description="Face recognition policy configuration",
    )

    @field_validator("database_url")
    @classmethod
    def ensure_database_directory(cls, v: str) -> str:
        """Ensure database directory exists for SQLite databases."""
        if v.startswith("sqlite:///"):
            db_path = Path(v.replace("sqlite:///", ""))
            db_path.parent.mkdir(parents=True, exist_ok=True)
        return v


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings singleton.

    Uses lru_cache to ensure only one Settings instance is created.

    Returns:
        Settings: Application settings instance
    """
    return Settings()
