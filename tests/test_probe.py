"""Tests for device probing behavior.

Run with ``python -m pytest -v tests/test_probe.py``.
"""

import pytest

from simulator import (
    AVAILABLE,
    RETIRED,
    Device,
    PermanentDeviceError,
    RetryExhaustedError,
    SimulatedDeviceAgent,
)


class TestSimulatedDeviceAgent:
    """Test probe retries and permanent failures."""

    def test_probe_retries_after_transient_failure(self) -> None:
        """Retry a transient failure and return the successful probe result."""

        device = Device(
            device_id="test-1",
            device_type="phone",
            device_state=AVAILABLE,
            os_version="18.0",
        )
        agent = SimulatedDeviceAgent(failures_before_success=1)

        result = agent.probe_with_retries(
            device=device,
            max_attempts=3,
            delay_seconds=0,
        )

        assert result == "Probe succeeded for test-1"

    def test_probe_raises_when_retries_are_exhausted(self) -> None:
        """Raise after every permitted probe attempt fails transiently."""

        device = Device(
            device_id="test-2",
            device_type="phone",
            device_state=AVAILABLE,
            os_version="18.0",
        )
        agent = SimulatedDeviceAgent(failures_before_success=3)

        with pytest.raises(
            RetryExhaustedError,
            match="failed after 3 attempts",
        ):
            agent.probe_with_retries(
                device,
                max_attempts=3,
                delay_seconds=0,
            )

    def test_probe_raises_permanent_error_for_retired_device(self) -> None:
        """Raise immediately when attempting to probe a retired device."""

        device = Device(
            device_id="test-3",
            device_type="phone",
            device_state=RETIRED,
            os_version="18.0",
        )
        agent = SimulatedDeviceAgent(failures_before_success=3)

        with pytest.raises(
            PermanentDeviceError,
            match="Cannot probe retired device test-3",
        ):
            agent.probe_with_retries(
                device,
                max_attempts=3,
                delay_seconds=0,
            )
