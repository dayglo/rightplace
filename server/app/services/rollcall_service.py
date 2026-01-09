"""
Roll Call service for business logic.

Handles roll call workflow management and validation.
"""
from datetime import datetime
from typing import Optional

from app.db.repositories.rollcall_repo import RollCallRepository
from app.db.repositories.verification_repo import VerificationRepository
from app.models.rollcall import (
    RollCall,
    RollCallCreate,
    RollCallStatus,
    RouteStop,
)


class RollCallService:
    """Service for roll call business logic."""

    def __init__(
        self,
        rollcall_repo: RollCallRepository,
        verification_repo: VerificationRepository,
    ):
        """
        Initialize service with repositories.

        Args:
            rollcall_repo: Roll call repository
            verification_repo: Verification repository
        """
        self.rollcall_repo = rollcall_repo
        self.verification_repo = verification_repo

    def create_roll_call(self, rollcall_data: RollCallCreate) -> RollCall:
        """
        Create a new roll call with validation.

        Args:
            rollcall_data: Roll call creation data

        Returns:
            Created roll call

        Raises:
            ValueError: If validation fails
        """
        # Validate route not empty
        if not rollcall_data.route:
            raise ValueError("Route cannot be empty")

        # Validate scheduled time not in past
        if rollcall_data.scheduled_at < datetime.now():
            raise ValueError("Scheduled time cannot be in the past")

        return self.rollcall_repo.create(rollcall_data)

    def start_roll_call(self, rollcall_id: str) -> RollCall:
        """
        Start a scheduled roll call.

        Args:
            rollcall_id: Roll call ID

        Returns:
            Updated roll call

        Raises:
            ValueError: If roll call not found or already started
        """
        rollcall = self.rollcall_repo.get_by_id(rollcall_id)
        if rollcall is None:
            raise ValueError(f"Roll call {rollcall_id} not found")

        if rollcall.status != RollCallStatus.SCHEDULED:
            raise ValueError("Roll call already in progress or completed")

        updated = self.rollcall_repo.update_status(
            rollcall_id, RollCallStatus.IN_PROGRESS
        )
        if updated is None:
            raise ValueError(f"Roll call {rollcall_id} not found")

        return updated

    def complete_roll_call(self, rollcall_id: str) -> RollCall:
        """
        Complete an in-progress roll call.

        Args:
            rollcall_id: Roll call ID

        Returns:
            Updated roll call

        Raises:
            ValueError: If roll call not found or not in progress
        """
        rollcall = self.rollcall_repo.get_by_id(rollcall_id)
        if rollcall is None:
            raise ValueError(f"Roll call {rollcall_id} not found")

        if rollcall.status != RollCallStatus.IN_PROGRESS:
            raise ValueError("Roll call not in progress")

        updated = self.rollcall_repo.update_status(
            rollcall_id, RollCallStatus.COMPLETED
        )
        if updated is None:
            raise ValueError(f"Roll call {rollcall_id} not found")

        return updated

    def cancel_roll_call(self, rollcall_id: str, reason: str) -> RollCall:
        """
        Cancel a roll call with reason.

        Args:
            rollcall_id: Roll call ID
            reason: Cancellation reason

        Returns:
            Updated roll call

        Raises:
            ValueError: If roll call not found or reason missing
        """
        if not reason or not reason.strip():
            raise ValueError("Cancellation reason required")

        rollcall = self.rollcall_repo.get_by_id(rollcall_id)
        if rollcall is None:
            raise ValueError(f"Roll call {rollcall_id} not found")

        updated = self.rollcall_repo.update_status(
            rollcall_id, RollCallStatus.CANCELLED, cancelled_reason=reason
        )
        if updated is None:
            raise ValueError(f"Roll call {rollcall_id} not found")

        return updated

    def get_current_stop(self, rollcall_id: str) -> Optional[RouteStop]:
        """
        Get the current stop in the route.

        Args:
            rollcall_id: Roll call ID

        Returns:
            Current route stop or None if all completed
        """
        rollcall = self.rollcall_repo.get_by_id(rollcall_id)
        if rollcall is None:
            return None

        # Find first non-completed stop
        for stop in rollcall.route:
            if stop.status in ["pending", "current"]:
                return stop

        return None

    def complete_current_stop(self, rollcall_id: str) -> RollCall:
        """
        Mark current stop as completed.

        Args:
            rollcall_id: Roll call ID

        Returns:
            Updated roll call

        Raises:
            ValueError: If roll call not found or no current stop
        """
        current_stop = self.get_current_stop(rollcall_id)
        if current_stop is None:
            raise ValueError("No current stop to complete")

        updated = self.rollcall_repo.update_route_stop(
            rollcall_id, current_stop.id, "completed"
        )
        if updated is None:
            raise ValueError(f"Roll call {rollcall_id} not found")

        return updated

    def skip_current_stop(self, rollcall_id: str, reason: str) -> RollCall:
        """
        Skip current stop with reason.

        Args:
            rollcall_id: Roll call ID
            reason: Skip reason

        Returns:
            Updated roll call

        Raises:
            ValueError: If roll call not found or no current stop
        """
        current_stop = self.get_current_stop(rollcall_id)
        if current_stop is None:
            raise ValueError("No current stop to skip")

        updated = self.rollcall_repo.update_route_stop(
            rollcall_id, current_stop.id, "skipped", skip_reason=reason
        )
        if updated is None:
            raise ValueError(f"Roll call {rollcall_id} not found")

        return updated

    def get_progress_stats(self, rollcall_id: str) -> dict:
        """
        Calculate roll call progress statistics.

        Args:
            rollcall_id: Roll call ID

        Returns:
            Dictionary with progress statistics

        Raises:
            ValueError: If roll call not found
        """
        rollcall = self.rollcall_repo.get_by_id(rollcall_id)
        if rollcall is None:
            raise ValueError(f"Roll call {rollcall_id} not found")

        # Count stops by status
        total_stops = len(rollcall.route)
        completed_stops = sum(1 for stop in rollcall.route if stop.status == "completed")
        skipped_stops = sum(1 for stop in rollcall.route if stop.status == "skipped")

        # Count expected inmates
        expected_inmates = sum(len(stop.expected_inmates) for stop in rollcall.route)

        # Count verified inmates
        verified_inmates = self.verification_repo.count_by_roll_call(rollcall_id)

        # Calculate progress percentage
        progress_percentage = (
            (completed_stops / total_stops * 100) if total_stops > 0 else 0.0
        )

        return {
            "total_stops": total_stops,
            "completed_stops": completed_stops,
            "skipped_stops": skipped_stops,
            "expected_inmates": expected_inmates,
            "verified_inmates": verified_inmates,
            "progress_percentage": progress_percentage,
        }