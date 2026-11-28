"""Tests for simulator behavior.

Run with ``python -m pytest -v tests/test_simulator.py``.
"""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from simulator import AVAILABLE, IN_USE, Device, provision_device

VALID_CONFIG = {
    "os_version": "19.0",
    "locale": "en_US",
    "timezone": "America/Los_Angeles",
    "test_profile": "smoke-test",
}


class TestProvisioning:
    """Check successful and failed device provisioning."""

    @pytest.mark.parametrize(
        "config, expected_success",
        [
            pytest.param(VALID_CONFIG, True, id="complete-config"),
            pytest.param(
                {
                    key: value
                    for key, value in VALID_CONFIG.items()
                    if key != "locale"
                },
                False,
                id="missing-locale",
            ),
            pytest.param(
                {
                    key: value
                    for key, value in VALID_CONFIG.items()
                    if key != "timezone"
                },
                False,
                id="missing-timezone",
            ),
            pytest.param(
                {
                    key: value
                    for key, value in VALID_CONFIG.items()
                    if key != "test_profile"
                },
                False,
                id="missing-test-profile",
            ),
        ],
    )
    def test_provisions_available_device(
        self,
        config: dict[str, str],
        expected_success: bool,
    ) -> None:
        """Verify provisioning success and failure behavior.

        Invalid settings must leave the device unchanged.
        """

        device = Device("test-1", "phone", AVAILABLE, "18.0")
        original_configuration = device.configuration.copy()

        result = provision_device(device, config)

        assert result.success is expected_success

        if expected_success:
            assert device.os_version == config["os_version"]
            assert device.configuration == {
                key: value for key, value in config.items()
                if key != "os_version"
            }
        else:
            assert device.os_version == "18.0"
            assert device.configuration == original_configuration


class TestDeviceLifecycle:
    """Test device lifecycle state changes."""

    def test_change_state_accepts_valid_and_rejects_invalid_transitions(
        self,
    ) -> None:
        """Accept an allowed transition and reject a disallowed one."""

        device = Device("test-1", "phone", AVAILABLE, "18.0")
        device.change_state(IN_USE)
        assert device.device_state == IN_USE

        with pytest.raises(
            ValueError,
            match="New device state not allowed: retired",
        ):
            device.change_state("retired")

    def test_concurrent_same_transition_allows_only_one(self) -> None:
        """Allow one of two simultaneous identical state changes."""

        device = Device("test-2", "phone", AVAILABLE, "18.0")
        start_barrier = Barrier(2)

        def attempt_transition() -> None:
            start_barrier.wait()
            device.change_state(IN_USE)

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(attempt_transition)
                for _ in range(2)
            ]

        outcomes = []
        for future in futures:
            try:
                future.result()
            except ValueError:
                outcomes.append("rejected")
            else:
                outcomes.append("success")

        assert outcomes.count("success") == 1
        assert outcomes.count("rejected") == 1
        assert device.device_state == IN_USE
