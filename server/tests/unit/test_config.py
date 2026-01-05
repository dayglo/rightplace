"""
Test suite for configuration module.

Tests the Settings and FaceRecognitionPolicy configuration models.
"""
import os
from pathlib import Path

import pytest
from pydantic import ValidationError


class TestFaceRecognitionPolicy:
    """Test FaceRecognitionPolicy configuration."""

    def test_default_policy_values(self):
        """Should have correct default threshold values."""
        from app.config import FaceRecognitionPolicy

        policy = FaceRecognitionPolicy()

        assert policy.verification_threshold == 0.75
        assert policy.enrollment_quality_threshold == 0.80
        assert policy.auto_accept_threshold == 0.92
        assert policy.manual_review_threshold == 0.60
        assert policy.low_light_adjustment == -0.05
        assert policy.facility_id == "default"

    def test_custom_policy_values(self):
        """Should accept custom threshold values."""
        from app.config import FaceRecognitionPolicy

        policy = FaceRecognitionPolicy(
            verification_threshold=0.80,
            enrollment_quality_threshold=0.85,
            auto_accept_threshold=0.95,
            manual_review_threshold=0.65,
            low_light_adjustment=-0.10,
            facility_id="facility-123",
        )

        assert policy.verification_threshold == 0.80
        assert policy.enrollment_quality_threshold == 0.85
        assert policy.auto_accept_threshold == 0.95
        assert policy.manual_review_threshold == 0.65
        assert policy.low_light_adjustment == -0.10
        assert policy.facility_id == "facility-123"

    def test_threshold_validation_ranges(self):
        """Should validate threshold values are between 0 and 1."""
        from app.config import FaceRecognitionPolicy

        # Valid values at boundaries (respecting logical order)
        policy = FaceRecognitionPolicy(
            manual_review_threshold=0.0,
            verification_threshold=0.5,
            auto_accept_threshold=1.0
        )
        assert policy.manual_review_threshold == 0.0
        assert policy.verification_threshold == 0.5
        assert policy.auto_accept_threshold == 1.0

        # Invalid: above 1.0
        with pytest.raises(ValidationError) as exc_info:
            FaceRecognitionPolicy(verification_threshold=1.5)
        assert "verification_threshold" in str(exc_info.value)

        # Invalid: below 0.0
        with pytest.raises(ValidationError) as exc_info:
            FaceRecognitionPolicy(verification_threshold=-0.1)
        assert "verification_threshold" in str(exc_info.value)

    def test_threshold_logical_order(self):
        """Should validate thresholds are in logical order."""
        from app.config import FaceRecognitionPolicy

        # Valid: auto_accept > verification > manual_review
        policy = FaceRecognitionPolicy(
            auto_accept_threshold=0.92,
            verification_threshold=0.75,
            manual_review_threshold=0.60,
        )
        assert policy.auto_accept_threshold > policy.verification_threshold
        assert policy.verification_threshold > policy.manual_review_threshold

        # Invalid: thresholds out of order should raise error
        with pytest.raises(ValidationError) as exc_info:
            FaceRecognitionPolicy(
                auto_accept_threshold=0.60,  # Lower than verification
                verification_threshold=0.75,
            )
        assert "auto_accept_threshold" in str(exc_info.value)

    def test_low_light_adjustment_range(self):
        """Should validate low_light_adjustment is reasonable."""
        from app.config import FaceRecognitionPolicy

        # Valid negative adjustment
        policy = FaceRecognitionPolicy(low_light_adjustment=-0.10)
        assert policy.low_light_adjustment == -0.10

        # Invalid: too large negative adjustment
        with pytest.raises(ValidationError) as exc_info:
            FaceRecognitionPolicy(low_light_adjustment=-0.5)
        assert "low_light_adjustment" in str(exc_info.value)


class TestSettings:
    """Test application Settings configuration."""

    def test_default_settings(self):
        """Should have correct default configuration values."""
        from app.config import Settings

        settings = Settings()

        assert settings.app_name == "Prison Roll Call Server"
        assert settings.app_version == "0.1.0"
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000
        assert settings.debug is False
        assert settings.database_url.startswith("sqlite:///")
        assert settings.api_key is not None
        assert len(settings.api_key) >= 32

    def test_settings_from_environment(self, monkeypatch):
        """Should load settings from environment variables."""
        from app.config import Settings

        # Set environment variables
        monkeypatch.setenv("HOST", "192.168.1.100")
        monkeypatch.setenv("PORT", "9000")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
        monkeypatch.setenv("API_KEY", "test-api-key-12345678901234567890")

        settings = Settings()

        assert settings.host == "192.168.1.100"
        assert settings.port == 9000
        assert settings.debug is True
        assert settings.database_url == "sqlite:///test.db"
        assert settings.api_key == "test-api-key-12345678901234567890"

    def test_database_path_creation(self):
        """Should ensure database directory exists."""
        from app.config import Settings

        settings = Settings()

        # Extract directory from database URL
        if settings.database_url.startswith("sqlite:///"):
            db_path = settings.database_url.replace("sqlite:///", "")
            db_dir = Path(db_path).parent
            # Database directory should exist or be creatable
            assert db_dir.exists() or db_dir == Path(".")

    def test_api_key_generation(self):
        """Should generate secure API key if not provided."""
        from app.config import Settings

        settings1 = Settings()
        settings2 = Settings()

        # Should generate API keys
        assert len(settings1.api_key) >= 32
        assert len(settings2.api_key) >= 32

        # Generated keys should be different (random)
        # Note: This could theoretically fail with very low probability
        assert settings1.api_key != settings2.api_key

    def test_policy_integration(self):
        """Should include FaceRecognitionPolicy in settings."""
        from app.config import Settings

        settings = Settings()

        assert hasattr(settings, "policy")
        assert settings.policy.verification_threshold == 0.75
        assert settings.policy.auto_accept_threshold == 0.92

    def test_custom_policy_in_settings(self):
        """Should allow custom policy configuration."""
        from app.config import Settings, FaceRecognitionPolicy

        custom_policy = FaceRecognitionPolicy(
            verification_threshold=0.80, facility_id="test-facility"
        )

        settings = Settings(policy=custom_policy)

        assert settings.policy.verification_threshold == 0.80
        assert settings.policy.facility_id == "test-facility"

    def test_cors_origins(self):
        """Should configure CORS origins."""
        from app.config import Settings

        settings = Settings()

        assert isinstance(settings.cors_origins, list)
        # Should allow local development by default
        assert "*" in settings.cors_origins or "http://localhost:3000" in settings.cors_origins

    def test_log_level_configuration(self):
        """Should configure logging level."""
        from app.config import Settings

        settings = Settings()

        assert settings.log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        # Default should be INFO
        assert settings.log_level == "INFO"

    def test_model_path_configuration(self):
        """Should configure ML model paths."""
        from app.config import Settings

        settings = Settings()

        assert hasattr(settings, "model_path")
        assert isinstance(settings.model_path, Path)
        # Should point to ml/models directory
        assert "models" in str(settings.model_path)


class TestConfigExport:
    """Test configuration export and validation."""

    def test_get_settings_singleton(self):
        """Should provide singleton settings instance."""
        from app.config import get_settings

        settings1 = get_settings()
        settings2 = get_settings()

        # Should return same instance
        assert settings1 is settings2

    def test_settings_dict_export(self):
        """Should export settings as dictionary."""
        from app.config import Settings

        settings = Settings()
        config_dict = settings.model_dump()

        assert "app_name" in config_dict
        assert "host" in config_dict
        assert "port" in config_dict
        assert "policy" in config_dict

    def test_settings_json_export(self):
        """Should export settings as JSON."""
        from app.config import Settings

        settings = Settings()
        config_json = settings.model_dump_json()

        assert isinstance(config_json, str)
        assert "app_name" in config_json
        assert "policy" in config_json
