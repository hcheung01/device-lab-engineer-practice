"""Per-device worker functions submitted to the fleet's thread pools."""

import logging
import random
import time

from simulator import (
    Device,
    DeviceInventory,
    HealthCheckResult,
    PermanentDeviceError,
    RetryExhaustedError,
    SimulatedDeviceAgent,
)

logger = logging.getLogger(__name__)


def check_one_device(
    device_id: str, inventory: DeviceInventory
) -> tuple[str, HealthCheckResult | None, float]:
    """Run one health check and return its ID, result, and elapsed seconds.

    The elapsed time includes the randomly simulated device response delay.
    """

    started_at = time.perf_counter()

    delay_seconds = random.uniform(0.05, 1.5)
    logger.info(
        "operation=health_check device_id=%s status=started "
        "simulated_delay=%.3fs",
        device_id,
        delay_seconds,
    )

    time.sleep(delay_seconds)

    health_result = HealthCheckResult(device_id).check_health(
        device_id, inventory
    )
    duration = time.perf_counter() - started_at

    logger.info(
        "operation=health_check device_id=%s status=finished duration=%.3fs",
        device_id,
        duration,
    )
    return device_id, health_result, duration


def probe_one_device(device: Device) -> float:
    """Probe one device and return the elapsed time in seconds.

    Each worker creates its own agent. Retired devices are logged as permanent
    failures, while exhausted transient failures are logged separately.

    Returns:
        Elapsed seconds, including simulated latency and retry delays.
    """

    started_at = time.perf_counter()
    delay_seconds = random.uniform(0.05, 1.5)
    logger.info(
        "operation=probe device_id=%s status=started simulated_delay=%.3fs",
        device.device_id,
        delay_seconds,
    )
    time.sleep(delay_seconds)

    # Isolate retry state so concurrent devices do not share a failure counter.
    agent = SimulatedDeviceAgent(failures_before_success=1)
    try:
        agent.probe_with_retries(device, max_attempts=3)
    except RetryExhaustedError as error:
        logger.error(
            "operation=probe device_id=%s outcome=exhausted error=%s",
            device.device_id,
            error,
        )
    except PermanentDeviceError as error:
        logger.error(
            "operation=probe device_id=%s "
            "outcome=permanent_device_error error=%s",
            device.device_id,
            error,
        )

    duration = time.perf_counter() - started_at
    logger.info(
        "operation=probe device_id=%s status=finished duration=%.3fs",
        device.device_id,
        duration,
    )
    return duration
