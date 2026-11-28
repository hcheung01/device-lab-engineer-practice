"""Per-device worker functions submitted to the fleet's thread pools."""

from __future__ import annotations

import logging
import random
import time

from device_backends import DeviceBackend, SimulatedBackend
from simulator import (
    Device,
    DeviceInventory,
    HealthCheckResult,
    PermanentDeviceError,
    RetryableDeviceError,
    RetryExhaustedError,
)

logger = logging.getLogger(__name__)


def _probe_with_retries(
    backend: DeviceBackend,
    device: Device,
    max_attempts: int = 3,
    delay_seconds: float = 0.2,
) -> str:
    """Retry transient probe failures across any DeviceBackend."""
    for attempt in range(1, max_attempts + 1):
        try:
            result = backend.probe(device)
        except RetryableDeviceError as error:
            if attempt == max_attempts:
                raise RetryExhaustedError(
                    f"Probe for {device.device_id} failed after {attempt} attempts"
                ) from error

            logger.warning(
                "operation=probe device_id=%s outcome=retrying attempt=%s error=%s",
                device.device_id,
                attempt,
                error,
            )
            time.sleep(delay_seconds)
        else:
            logger.info(
                "operation=probe device_id=%s outcome=success attempts=%s",
                device.device_id,
                attempt,
            )
            return result
    raise RetryExhaustedError(f"Probe exhausted for {device.device_id}")


def check_one_device(
    device_id: str,
    inventory: DeviceInventory,
    backend: DeviceBackend | None = None,
    simulate_jitter: bool = True,
) -> tuple[str, HealthCheckResult | None, float]:
    """Run one health check using the configured backend."""
    active_backend = backend or SimulatedBackend()
    started_at = time.perf_counter()

    if simulate_jitter:
        delay_seconds = random.uniform(0.05, 1.5)
        logger.info(
            "operation=health_check device_id=%s status=started simulated_delay=%.3fs",
            device_id,
            delay_seconds,
        )
        time.sleep(delay_seconds)

    health_result = active_backend.check_health(device_id, inventory)
    duration = time.perf_counter() - started_at

    logger.info(
        "operation=health_check device_id=%s status=finished duration=%.3fs",
        device_id,
        duration,
    )
    return device_id, health_result, duration


def probe_one_device(
    device: Device,
    backend: DeviceBackend | None = None,
    simulate_jitter: bool = True,
) -> float:
    """Probe one device using the configured backend and return elapsed seconds."""
    active_backend = backend or SimulatedBackend(failures_before_success=1)
    started_at = time.perf_counter()

    if simulate_jitter:
        delay_seconds = random.uniform(0.05, 1.5)
        logger.info(
            "operation=probe device_id=%s status=started simulated_delay=%.3fs",
            device.device_id,
            delay_seconds,
        )
        time.sleep(delay_seconds)

    try:
        _probe_with_retries(active_backend, device, max_attempts=3)
    except RetryExhaustedError as error:
        logger.error(
            "operation=probe device_id=%s outcome=exhausted error=%s",
            device.device_id,
            error,
        )
    except PermanentDeviceError as error:
        logger.error(
            "operation=probe device_id=%s outcome=permanent_device_error error=%s",
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
