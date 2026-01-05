"""
Test suite for Pydantic data models.

Tests validation, serialization, and business logic for all models.
"""
from datetime import date, datetime

import pytest
from pydantic import ValidationError


class TestInmateModels:
    """Test Inmate model and related models."""

    def test_inmate_model_creation(self):
        """Should create inmate with all required fields."""
        from app.models.inmate import Inmate

        inmate = Inmate(
            id="test-id",
            inmate_number="A12345",
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            cell_block="A",
            cell_number="101",
            is_enrolled=True,
            enrolled_at=datetime.now(),
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert inmate.id == "test-id"
        assert inmate.inmate_number == "A12345"
        assert inmate.first_name == "John"
        assert inmate.last_name == "Doe"
        assert inmate.is_enrolled is True

    def test_inmate_model_defaults(self):
        """Should have correct default values."""
        from app.models.inmate import Inmate

        inmate = Inmate(
            id="test-id",
            inmate_number="A12345",
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            cell_block="A",
            cell_number="101",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert inmate.photo_uri is None
        assert inmate.is_enrolled is False
        assert inmate.enrolled_at is None
        assert inmate.is_active is True

    def test_inmate_create_model(self):
        """Should create InmateCreate with required fields only."""
        from app.models.inmate import InmateCreate

        inmate_data = InmateCreate(
            inmate_number="A12345",
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            cell_block="A",
            cell_number="101",
        )

        assert inmate_data.inmate_number == "A12345"
        assert inmate_data.first_name == "John"

    def test_inmate_update_model(self):
        """Should allow partial updates with InmateUpdate."""
        from app.models.inmate import InmateUpdate

        # All fields optional
        update = InmateUpdate(first_name="Jane")
        assert update.first_name == "Jane"
        assert update.last_name is None

        # Can update multiple fields
        update = InmateUpdate(
            first_name="Jane", last_name="Smith", cell_block="B"
        )
        assert update.first_name == "Jane"
        assert update.last_name == "Smith"

    def test_inmate_validation(self):
        """Should validate inmate fields."""
        from app.models.inmate import Inmate

        # Missing required field should fail
        with pytest.raises(ValidationError):
            Inmate(
                id="test-id",
                first_name="John",
                # Missing inmate_number
                last_name="Doe",
                date_of_birth=date(1990, 1, 1),
                cell_block="A",
                cell_number="101",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )


class TestLocationModels:
    """Test Location model and related enums."""

    def test_location_type_enum(self):
        """Should have correct location types."""
        from app.models.location import LocationType

        assert LocationType.BLOCK == "block"
        assert LocationType.CELL == "cell"
        assert LocationType.COMMON_AREA == "common_area"
        assert LocationType.YARD == "yard"
        assert LocationType.MEDICAL == "medical"
        assert LocationType.ADMIN == "admin"

    def test_location_model_creation(self):
        """Should create location with required fields."""
        from app.models.location import Location, LocationType

        location = Location(
            id="loc-1",
            name="Cell Block A",
            type=LocationType.BLOCK,
            building="Main",
        )

        assert location.id == "loc-1"
        assert location.name == "Cell Block A"
        assert location.type == LocationType.BLOCK
        assert location.building == "Main"

    def test_location_defaults(self):
        """Should have correct default values."""
        from app.models.location import Location, LocationType

        location = Location(
            id="loc-1", name="Cell", type=LocationType.CELL, building="Main"
        )

        assert location.parent_id is None
        assert location.capacity == 1
        assert location.floor == 0


class TestRollCallModels:
    """Test RollCall, RouteStop models and related enums."""

    def test_rollcall_status_enum(self):
        """Should have correct roll call statuses."""
        from app.models.rollcall import RollCallStatus

        assert RollCallStatus.SCHEDULED == "scheduled"
        assert RollCallStatus.IN_PROGRESS == "in_progress"
        assert RollCallStatus.COMPLETED == "completed"
        assert RollCallStatus.CANCELLED == "cancelled"

    def test_route_stop_model(self):
        """Should create route stop with required fields."""
        from app.models.rollcall import RouteStop

        stop = RouteStop(
            id="stop-1",
            location_id="loc-1",
            order=1,
            expected_inmates=["inmate-1", "inmate-2"],
        )

        assert stop.id == "stop-1"
        assert stop.location_id == "loc-1"
        assert stop.order == 1
        assert len(stop.expected_inmates) == 2
        assert stop.status == "pending"

    def test_rollcall_model_creation(self):
        """Should create roll call with required fields."""
        from app.models.rollcall import RollCall, RollCallStatus, RouteStop

        stop = RouteStop(
            id="stop-1",
            location_id="loc-1",
            order=1,
            expected_inmates=["inmate-1"],
        )

        rollcall = RollCall(
            id="rc-1",
            name="Morning Roll Call",
            status=RollCallStatus.SCHEDULED,
            scheduled_at=datetime.now(),
            route=[stop],
            officer_id="officer-1",
        )

        assert rollcall.id == "rc-1"
        assert rollcall.name == "Morning Roll Call"
        assert len(rollcall.route) == 1
        assert rollcall.notes == ""


class TestVerificationModels:
    """Test Verification model and related enums."""

    def test_verification_status_enum(self):
        """Should have correct verification statuses."""
        from app.models.verification import VerificationStatus

        assert VerificationStatus.VERIFIED == "verified"
        assert VerificationStatus.NOT_FOUND == "not_found"
        assert VerificationStatus.WRONG_LOCATION == "wrong_location"
        assert VerificationStatus.MANUAL == "manual"
        assert VerificationStatus.PENDING == "pending"

    def test_manual_override_reason_enum(self):
        """Should have correct manual override reasons."""
        from app.models.verification import ManualOverrideReason

        assert ManualOverrideReason.FACIAL_INJURY == "facial_injury"
        assert ManualOverrideReason.LIGHTING_CONDITIONS == "lighting_conditions"
        assert ManualOverrideReason.TECHNICAL_FAILURE == "technical_failure"
        assert ManualOverrideReason.NOT_ENROLLED == "not_enrolled"
        assert ManualOverrideReason.NETWORK_UNAVAILABLE == "network_unavailable"
        assert ManualOverrideReason.OTHER == "other"

    def test_verification_model_creation(self):
        """Should create verification with required fields."""
        from app.models.verification import Verification, VerificationStatus

        verification = Verification(
            id="ver-1",
            roll_call_id="rc-1",
            inmate_id="inmate-1",
            location_id="loc-1",
            status=VerificationStatus.VERIFIED,
            confidence=0.89,
            timestamp=datetime.now(),
        )

        assert verification.id == "ver-1"
        assert verification.confidence == 0.89
        assert verification.status == VerificationStatus.VERIFIED
        assert verification.is_manual_override is False


class TestFaceModels:
    """Test Face recognition related models."""

    def test_bounding_box_model(self):
        """Should create bounding box."""
        from app.models.face import BoundingBox

        bbox = BoundingBox(x=100, y=80, width=200, height=240)

        assert bbox.x == 100
        assert bbox.y == 80
        assert bbox.width == 200
        assert bbox.height == 240

    def test_face_landmarks_model(self):
        """Should create face landmarks."""
        from app.models.face import FaceLandmarks

        landmarks = FaceLandmarks(
            left_eye=(150, 120),
            right_eye=(250, 120),
            nose=(200, 180),
            left_mouth=(160, 220),
            right_mouth=(240, 220),
        )

        assert landmarks.left_eye == (150, 120)
        assert landmarks.nose == (200, 180)

    def test_quality_issue_enum(self):
        """Should have correct quality issues."""
        from app.models.face import QualityIssue

        assert QualityIssue.NO_FACE == "no_face"
        assert QualityIssue.MULTI_FACE == "multi_face"
        assert QualityIssue.LOW_LIGHT == "low_light"
        assert QualityIssue.BLUR == "blur"

    def test_detection_result_model(self):
        """Should create detection result."""
        from app.models.face import BoundingBox, DetectionResult, FaceLandmarks

        bbox = BoundingBox(x=100, y=80, width=200, height=240)
        landmarks = FaceLandmarks(
            left_eye=(150, 120),
            right_eye=(250, 120),
            nose=(200, 180),
            left_mouth=(160, 220),
            right_mouth=(240, 220),
        )

        detection = DetectionResult(
            detected=True,
            face_count=1,
            bounding_box=bbox,
            landmarks=landmarks,
            quality=0.87,
            quality_issues=[],
        )

        assert detection.detected is True
        assert detection.face_count == 1
        assert detection.quality == 0.87

    def test_match_recommendation_enum(self):
        """Should have correct match recommendations."""
        from app.models.face import MatchRecommendation

        assert MatchRecommendation.AUTO_ACCEPT == "auto_accept"
        assert MatchRecommendation.CONFIRM == "confirm"
        assert MatchRecommendation.REVIEW == "review"
        assert MatchRecommendation.NO_MATCH == "no_match"

    def test_match_result_model(self):
        """Should create match result."""
        from app.models.face import (
            DetectionResult,
            MatchRecommendation,
            MatchResult,
        )
        from app.models.inmate import Inmate

        inmate = Inmate(
            id="inmate-1",
            inmate_number="A12345",
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            cell_block="A",
            cell_number="101",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        detection = DetectionResult(
            detected=True,
            face_count=1,
            bounding_box=None,
            landmarks=None,
            quality=0.85,
            quality_issues=[],
        )

        match = MatchResult(
            matched=True,
            inmate_id="inmate-1",
            inmate=inmate,
            confidence=0.89,
            threshold_used=0.75,
            recommendation=MatchRecommendation.CONFIRM,
            at_expected_location=True,
            all_matches=[{"inmate_id": "inmate-1", "confidence": 0.89}],
            detection=detection,
        )

        assert match.matched is True
        assert match.confidence == 0.89
        assert match.recommendation == MatchRecommendation.CONFIRM
