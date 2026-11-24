"""Device models and simulated operations for the device lab."""

from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)

AVAILABLE = "available"
IN_USE = "in_use"
MAINTENANCE = "maintenance"
RETIRED = "retired"

ALLOWED_TRANSITIONS = {
    AVAILABLE: {IN_USE, MAINTENANCE},
    IN_USE: {AVAILABLE, MAINTENANCE},
    MAINTENANCE: {AVAILABLE, RETIRED},
    RETIRED: set(),
}

DeviceConfig = dict[str, str]


class Device:
    """Represent one managed lab device."""

    def __init__(
        self,
        device_id: str,
        device_type: str,
        device_state: str,
        os_version: str,
        battery_level: int | None = 100,
        is_connected: bool = True,
        configuration: DeviceConfig | None = None,
    ) -> None:
        """Create a device with identity, lifecycle, OS, and status data.

        Raises:
            ValueError: The lifecycle state is not recognized.
        """

        self.device_id = device_id
        self.device_type = device_type
        if device_state not in ALLOWED_TRANSITIONS:
            raise ValueError(f"Invalid device state: {device_state}")
        self.device_state = device_state
        self.os_version = os_version
        self.battery_level = battery_level
        self.is_connected = is_connected
        self.configuration = {} if configuration is None else configuration

    def change_state(self, new_state: str) -> None:
        """Move to an allowed lifecycle state or raise ``ValueError``."""

        allow_states = ALLOWED_TRANSITIONS[self.device_state]
        if new_state not in allow_states:
            raise ValueError(f"New device state not allowed: {new_state}")
        old_state = self.device_state
        self.device_state = new_state
        logger.info(
            "operation=state_change device_id=%s old_state=%s new_state=%s",
            self.device_id,
            old_state,
            new_state,
        )


class DeviceInventory:
    """Store and query the devices managed by the simulator."""

    def __init__(self) -> None:
        """Create an empty inventory keyed by device ID."""

        self.device_inventory: dict[str, Device] = {}

    def add(self, device: Device) -> None:
        """Add a device; raise ``ValueError`` if its ID is already present."""

        if device.device_id in self.device_inventory:
            raise ValueError(f"Duplicate ID: {device.device_id}")
        self.device_inventory[device.device_id] = device
        logger.debug(
            "operation=inventory_add device_id=%s device_type=%s "
            "inventory_size=%s",
            device.device_id,
            device.device_type,
            len(self.device_inventory),
        )

    def lookup(self, device_id: str) -> Device:
        """Return the device with this ID or raise ``KeyError`` if absent."""

        if device_id not in self.device_inventory:
            raise KeyError(f"Device ID not in inventory: {device_id}")
        return self.device_inventory[device_id]

    def list_by_state(self, state: str) -> list[Device]:
        """Return all inventory devices currently in ``state``."""

        devices = []
        for device in self.device_inventory.values():
            if device.device_state == state:
                devices.append(device)
        return devices


class HealthCheckResult:
    """Store a device's health status and reasons it failed a check."""

    def __init__(
        self,
        device_id: str,
        healthy: bool = True,
        reasons: list[str] | None = None,
    ) -> None:
        """Initialize a healthy result, optionally with existing findings."""

        self.device_id = device_id
        self.healthy = healthy
        self.reasons = [] if reasons is None else reasons

    def get_device_battery(
        self, device_id: str, inventory: DeviceInventory
    ) -> int | None:
        """Return battery level, or ``None`` when the device is not found."""

        try:
            device = inventory.lookup(device_id)
        except KeyError:
            return None
        return device.battery_level

    def is_connected(
        self, device_id: str, inventory: DeviceInventory
    ) -> bool | None:
        """Return connection status, or ``None`` when the device is absent."""

        try:
            device = inventory.lookup(device_id)
        except KeyError:
            return None
        return device.is_connected

    def check_health(
        self, device_id: str, inventory: DeviceInventory
    ) -> HealthCheckResult | None:
        """Check battery and connection; return ``None`` for unknown IDs."""

        try:
            device = inventory.lookup(device_id)
        except KeyError:
            logger.debug(
                "operation=health_check device_id=%s outcome=not_found",
                device_id,
            )
            return None
        if (
            device.battery_level is None
            or not 20 <= device.battery_level <= 100
        ):
            self.reasons.append(f"battery level: {device.battery_level}")
            self.healthy = False
        if device.is_connected is None or device.is_connected is False:
            self.reasons.append(f"device connected: {device.is_connected}")
            self.healthy = False
        logger.debug(
            "operation=health_check device_id=%s healthy=%s reasons=%s",
            device_id,
            self.healthy,
            self.reasons,
        )
        return self


class ProvisioningResult:
    """Describe whether provisioning succeeded and what was requested."""

    def __init__(
        self,
        device_id: str,
        requested_configuration: DeviceConfig,
        success: bool,
        message: str,
    ) -> None:
        """Store the requested configuration and operation outcome."""

        self.device_id = device_id
        self.requested_configuration = requested_configuration
        self.success = success
        self.message = message


def provision_device(
    device: Device, config: DeviceConfig
) -> ProvisioningResult:
    """Apply configuration to an available device and return the outcome.

    Args:
        device: Device to configure.
        config: Requested OS version, locale, timezone, and test profile.

    Returns:
        A result indicating success or why provisioning was rejected. The
        device is unchanged when unavailable or configuration is incomplete.
    """

    if device.device_state != AVAILABLE:
        logger.debug(
            "operation=provision device_id=%s outcome=rejected "
            "reason=device_not_available state=%s",
            device.device_id,
            device.device_state,
        )
        return ProvisioningResult(
            device.device_id,
            config,
            False,
            "Device must be available"
        )

    if "os_version" not in config or not config["os_version"]:
        logger.debug(
            "operation=provision device_id=%s outcome=rejected "
            "reason=missing_os_version",
            device.device_id,
        )
        return ProvisioningResult(
            device.device_id,
            config,
            False,
            "Missing os version"
        )
    settings_required = ["locale", "timezone", "test_profile"]
    missed_settings = [
        setting for setting in settings_required if not config.get(setting)
    ]
    if missed_settings:
        logger.debug(
            "operation=provision device_id=%s outcome=rejected "
            "missing_settings=%s",
            device.device_id,
            missed_settings,
        )
        return ProvisioningResult(
            device.device_id,
            config,
            False,
            f"Missing settings: {', '.join(missed_settings)}",
        )
    device.os_version = config["os_version"]
    device.configuration = {
        key: value
        for key, value in config.items()
        if key != "os_version"
    }
    logger.debug(
        "operation=provision device_id=%s outcome=success os_version=%s",
        device.device_id,
        device.os_version,
    )
    return ProvisioningResult(
        device.device_id,
        config,
        True,
        "Provisioning completed",
    )


class RetryableDeviceError(Exception):
    """Signal a temporary probe failure that may succeed on retry."""

    pass


class PermanentDeviceError(Exception):
    """Signal a probe failure that retrying cannot resolve."""

    pass


class RetryExhaustedError(Exception):
    """Signal that all permitted probe attempts failed transiently."""

    pass


class SimulatedDeviceAgent:
    """Simulate probes with configurable transient failures."""

    def __init__(self, failures_before_success: int = 0) -> None:
        """Create an agent; reject a negative transient-failure count."""

        if failures_before_success < 0:
            raise ValueError("failures_before_success cannot be negative")
        self.failures_remaining = failures_before_success

    def probe(self, device: Device) -> str:
        """Probe once, raising permanent or retryable errors as appropriate."""

        if device.device_state == RETIRED:
            raise PermanentDeviceError(
                f"Cannot probe retired device {device.device_id}"
            )
        if self.failures_remaining > 0:
            self.failures_remaining -= 1
            raise RetryableDeviceError(
                f"Temporary probe failure for {device.device_id}"
            )

        return f"Probe succeeded for {device.device_id}"

    def probe_with_retries(
        self, device: Device, max_attempts: int, delay_seconds: float = 0.1
    ) -> str | None:
        """Probe until success or a permanent or exhausted failure.

        Args:
            device: Device to probe.
            max_attempts: Maximum number of attempts; use at least one.
            delay_seconds: Wait time between retryable attempts.

        Returns:
            The success message, or ``None`` if no attempts are made.

        Raises:
            PermanentDeviceError: The device is retired.
            RetryExhaustedError: Every allowed attempt failed transiently.
        """

        for attempt in range(1, max_attempts + 1):
            try:
                result = self.probe(device)
            except RetryableDeviceError as error:
                if attempt == max_attempts:
                    raise RetryExhaustedError(
                        f"Probe for {device.device_id} failed after "
                        f"{attempt} attempts"
                    ) from error

                logger.warning(
                    "operation=probe device_id=%s outcome=retrying attempt=%s",
                    device.device_id,
                    attempt,
                )
                time.sleep(delay_seconds)
            else:
                logger.info(
                    "operation=probe device_id=%s outcome=success attempts=%s",
                    device.device_id,
                    attempt,
                )
                return result
