"""Collect simple per-operation counts and elapsed-time totals."""

import logging

logger = logging.getLogger(__name__)


class Telemetry:
    """Aggregate operation counts and durations for one simulator run."""

    def __init__(self) -> None:
        """Start with no recorded operations."""

        self.operation_counts = {}
        self.duration_totals = {}

    def record(self, operation: str, duration_seconds: float) -> None:
        """Add one operation and its elapsed duration to the aggregates."""

        self.operation_counts[operation] = (
            self.operation_counts.get(operation, 0) + 1
        )
        self.duration_totals[operation] = (
            self.duration_totals.get(operation, 0.0) + duration_seconds
        )

    def snapshot(self) -> dict[str, dict[str, int | float]]:
        """Return copies of the current aggregates for logging or reporting."""

        return {
            "operation_counts": self.operation_counts.copy(),
            "duration_totals": self.duration_totals.copy(),
        }
