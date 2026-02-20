"""
Test suite for VerificationRepository.

Tests CRUD operations and queries for verification records.
"""
from datetime import datetime
from uuid import uuid4

import pytest

from app.db.database import get_connection, init_db
from app.db.repositories.verification_repo import VerificationRepository
from app.db.repositories.inmate_repo import InmateRepository
from app.db.repositories.location_repo import LocationRepository
from app.db.repositories.rollcall_repo import RollCallRepository
from app.models.verification import (
    Verification,
    VerificationStatus,
    ManualOverrideReason,
)
from app.models.inmate import InmateCreate
from app.models.location import LocationCreate, LocationType
from app.models.rollcall import RollCallCreate, RouteStop
from datetime import date


@pytest.fixture
def db_conn():
    """Create an in-memory database connection for testing."""
    conn = get_connection(":memory:")
    init_db(conn)
    yield conn
    conn.close()


@pytest.fixture
def verification_repo(db_conn):
    """Create a VerificationRepository instance."""
    return VerificationRepository(db_conn)


@pytest.fixture
def inmate_repo(db_conn):
    """Create an InmateRepository instance."""
    return InmateRepository(db_conn)


@pytest.fixture
def location_repo(db_conn):
    """Create a LocationRepository instance."""
    return LocationRepository(db_conn)


@pytest.fixture
def rollcall_repo(db_conn):
    """Create a RollCallRepository instance."""
    return RollCallRepository(db_conn)


@pytest.fixture
def sample_inmate(inmate_repo):
    """Create a sample inmate for testing."""
    return inmate_repo.create(
        InmateCreate(
            inmate_number="A12345",
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            cell_block="A",
            cell_number="101",
        )
    )


@pytest.fixture
def sample_location(location_repo):
    """Create a sample location for testing."""
    return location_repo.create(
        LocationCreate(
            name="Cell Block A",
            type=LocationType.HOUSEBLOCK,
            building="Main",
        )
    )


@pytest.fixture
def sample_rollcall(rollcall_repo, sample_location):
    """Create a sample roll call for testing."""
    return rollcall_repo.create(
        RollCallCreate(
            name="Morning Roll Call",
            scheduled_at=datetime.now(),
            route=[
                RouteStop(
                    id="stop1",
                    location_id=sample_location.id,
                    order=1,
                    expected_inmates=["inmate1"],
                )
            ],
            officer_id="officer1",
        )
    )


class TestVerificationRepositoryCreate:
    """Test verification creation."""

    def test_create_verification_success(
        self,
        verification_repo,
        sample_rollcall,
        sample_inmate,
        sample_location,
    ):
        """Should create verification with all required fields."""
        verification = verification_repo.create(
            roll_call_id=sample_rollcall.id,
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            status=VerificationStatus.VERIFIED,
            confidence=0.89,
        )

        assert verification.id is not None
        assert verification.roll_call_id == sample_rollcall.id
        assert verification.inmate_id == sample_inmate.id
        assert verification.location_id == sample_location.id
        assert verification.status == VerificationStatus.VERIFIED
        assert verification.confidence == 0.89
        assert verification.is_manual_override is False
        assert verification.timestamp is not None

    def test_create_verification_with_manual_override(
        self,
        verification_repo,
        sample_rollcall,
        sample_inmate,
        sample_location,
    ):
        """Should create verification with manual override."""
        verification = verification_repo.create(
            roll_call_id=sample_rollcall.id,
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            status=VerificationStatus.MANUAL,
            confidence=0.0,
            is_manual_override=True,
            manual_override_reason=ManualOverrideReason.FACIAL_INJURY,
            notes="Inmate has bandage",
        )

        assert verification.is_manual_override is True
        assert verification.manual_override_reason == ManualOverrideReason.FACIAL_INJURY
        assert verification.notes == "Inmate has bandage"

    def test_create_verification_with_photo(
        self,
        verification_repo,
        sample_rollcall,
        sample_inmate,
        sample_location,
    ):
        """Should create verification with photo URI."""
        verification = verification_repo.create(
            roll_call_id=sample_rollcall.id,
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            status=VerificationStatus.VERIFIED,
            confidence=0.92,
            photo_uri="/photos/verification_123.jpg",
        )

        assert verification.photo_uri == "/photos/verification_123.jpg"


class TestVerificationRepositoryRead:
    """Test reading verification records."""

    def test_get_by_id_found(
        self,
        verification_repo,
        sample_rollcall,
        sample_inmate,
        sample_location,
    ):
        """Should retrieve verification by ID."""
        created = verification_repo.create(
            roll_call_id=sample_rollcall.id,
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            status=VerificationStatus.VERIFIED,
            confidence=0.89,
        )

        retrieved = verification_repo.get_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.roll_call_id == created.roll_call_id

    def test_get_by_id_not_found(self, verification_repo):
        """Should return None for non-existent ID."""
        result = verification_repo.get_by_id("non-existent-id")
        assert result is None

    def test_get_by_roll_call(
        self,
        verification_repo,
        sample_rollcall,
        sample_inmate,
        sample_location,
    ):
        """Should retrieve all verifications for a roll call."""
        verification_repo.create(
            roll_call_id=sample_rollcall.id,
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            status=VerificationStatus.VERIFIED,
            confidence=0.89,
        )
        verification_repo.create(
            roll_call_id=sample_rollcall.id,
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            status=VerificationStatus.VERIFIED,
            confidence=0.85,
        )

        verifications = verification_repo.get_by_roll_call(sample_rollcall.id)
        assert len(verifications) == 2

    def test_get_by_roll_call_before_timestamp(
        self,
        verification_repo,
        sample_rollcall,
        sample_inmate,
        sample_location,
        db_conn,
    ):
        """Should retrieve only verifications before a specific timestamp."""
        from datetime import timedelta
        import time

        # Create first verification
        v1 = verification_repo.create(
            roll_call_id=sample_rollcall.id,
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            status=VerificationStatus.VERIFIED,
            confidence=0.89,
        )

        # Wait a moment to ensure different timestamps
        time.sleep(0.1)
        cutoff_time = datetime.now()
        time.sleep(0.1)

        # Create second verification after cutoff
        v2 = verification_repo.create(
            roll_call_id=sample_rollcall.id,
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            status=VerificationStatus.NOT_FOUND,
            confidence=0.75,
        )

        # Should get only the first verification
        verifications = verification_repo.get_by_roll_call_before_timestamp(
            sample_rollcall.id, cutoff_time
        )
        assert len(verifications) == 1
        assert verifications[0].id == v1.id

        # Should get both if cutoff is in the future
        verifications_all = verification_repo.get_by_roll_call_before_timestamp(
            sample_rollcall.id, datetime.now() + timedelta(hours=1)
        )
        assert len(verifications_all) == 2

    def test_get_by_inmate(
        self,
        verification_repo,
        sample_rollcall,
        sample_inmate,
        sample_location,
    ):
        """Should retrieve all verifications for an inmate."""
        verification_repo.create(
            roll_call_id=sample_rollcall.id,
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            status=VerificationStatus.VERIFIED,
            confidence=0.89,
        )
        verification_repo.create(
            roll_call_id=sample_rollcall.id,
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            status=VerificationStatus.VERIFIED,
            confidence=0.92,
        )

        verifications = verification_repo.get_by_inmate(sample_inmate.id)
        assert len(verifications) == 2

    def test_get_by_location(
        self,
        verification_repo,
        sample_rollcall,
        sample_inmate,
        sample_location,
    ):
        """Should retrieve all verifications for a location."""
        verification_repo.create(
            roll_call_id=sample_rollcall.id,
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            status=VerificationStatus.VERIFIED,
            confidence=0.89,
        )

        verifications = verification_repo.get_by_location(sample_location.id)
        assert len(verifications) == 1

    def test_count_by_roll_call(
        self,
        verification_repo,
        sample_rollcall,
        sample_inmate,
        sample_location,
    ):
        """Should count verifications for a roll call."""
        verification_repo.create(
            roll_call_id=sample_rollcall.id,
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            status=VerificationStatus.VERIFIED,
            confidence=0.89,
        )
        verification_repo.create(
            roll_call_id=sample_rollcall.id,
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            status=VerificationStatus.NOT_FOUND,
            confidence=0.45,
        )

        count = verification_repo.count_by_roll_call(sample_rollcall.id)
        assert count == 2

    def test_count_by_status(
        self,
        verification_repo,
        sample_rollcall,
        sample_inmate,
        sample_location,
    ):
        """Should count verifications by status for a roll call."""
        verification_repo.create(
            roll_call_id=sample_rollcall.id,
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            status=VerificationStatus.VERIFIED,
            confidence=0.89,
        )
        verification_repo.create(
            roll_call_id=sample_rollcall.id,
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            status=VerificationStatus.VERIFIED,
            confidence=0.92,
        )
        verification_repo.create(
            roll_call_id=sample_rollcall.id,
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            status=VerificationStatus.NOT_FOUND,
            confidence=0.45,
        )

        verified_count = verification_repo.count_by_status(
            sample_rollcall.id, VerificationStatus.VERIFIED
        )
        not_found_count = verification_repo.count_by_status(
            sample_rollcall.id, VerificationStatus.NOT_FOUND
        )

        assert verified_count == 2
        assert not_found_count == 1

    def test_get_manual_overrides(
        self,
        verification_repo,
        sample_rollcall,
        sample_inmate,
        sample_location,
    ):
        """Should retrieve only manual override verifications."""
        verification_repo.create(
            roll_call_id=sample_rollcall.id,
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            status=VerificationStatus.VERIFIED,
            confidence=0.89,
        )
        verification_repo.create(
            roll_call_id=sample_rollcall.id,
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            status=VerificationStatus.MANUAL,
            confidence=0.0,
            is_manual_override=True,
            manual_override_reason=ManualOverrideReason.FACIAL_INJURY,
        )

        manual_overrides = verification_repo.get_manual_overrides(sample_rollcall.id)
        assert len(manual_overrides) == 1
        assert manual_overrides[0].is_manual_override is True


class TestVerificationRepositoryDelete:
    """Test deleting verification records."""

    def test_delete_success(
        self,
        verification_repo,
        sample_rollcall,
        sample_inmate,
        sample_location,
    ):
        """Should delete verification."""
        created = verification_repo.create(
            roll_call_id=sample_rollcall.id,
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            status=VerificationStatus.VERIFIED,
            confidence=0.89,
        )

        result = verification_repo.delete(created.id)

        assert result is True
        assert verification_repo.get_by_id(created.id) is None

    def test_delete_not_found(self, verification_repo):
        """Should return False when deleting non-existent verification."""
        result = verification_repo.delete("non-existent-id")
        assert result is False