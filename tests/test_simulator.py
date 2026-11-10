"""Tests for device simulator behavior. python -m pytest -v tests/test_simulator.py"""


from simulator import AVAILABLE, Device, provision_device
import pytest

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
                {key: value for key, value in VALID_CONFIG.items() if key != "locale"},
                False,
                id="missing-locale",
            ),
            pytest.param(
                {key: value for key, value in VALID_CONFIG.items() if key != "timezone"},
                False,
                id="missing-timezone",
            ),
            pytest.param(
                {key: value for key, value in VALID_CONFIG.items() if key != "test_profile"},
                False,
                id="missing-test-profile",
            ),
        ],
    )
    def test_provisions_available_device(self, config, expected_success):
        """Apply valid config and leave the device unchanged for invalid config."""
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
