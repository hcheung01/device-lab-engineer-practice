import logging

logger = logging.getLogger(__name__)

class Telemetry:
    def __init__(self):
        self.operation_counts = {}
        self.duration_totals = {}

    def record(self, operation, duration_seconds):
        self.operation_counts[operation] = (
            self.operation_counts.get(operation, 0) + 1
        )
        self.duration_totals[operation] = (
            self.duration_totals.get(operation, 0.0) + duration_seconds
        )

    def snapshot(self):
        return {
            "operation_counts": self.operation_counts.copy(),
            "duration_totals": self.duration_totals.copy(),
        }