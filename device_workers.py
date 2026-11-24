from simulator import Device, DeviceInventory, HealthCheckResult, SimulatedDeviceAgent, RetryExhaustedError, PermanentDeviceError, provision_device
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
import time
import logging

logger = logging.getLogger(__name__)

def check_one_device(
    device_id: str, inventory: DeviceInventory
) -> tuple[str, HealthCheckResult | None, float]:
    started_at = time.perf_counter()

    delay_seconds = random.uniform(0.05, 3.5)
    logger.info(
        "operation=health_check device_id=%s status=started simulated_delay=%.3fs",
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

def probe_one_device(device: Device) -> None:
    
    started_at = time.perf_counter()
    delay_seconds = random.uniform(0.05, 3.5)
    logger.info(
        "operation=probing device_id=%s status=started simulated_delay=%.3fs",
        device.device_id,
        delay_seconds,
    )
    time.sleep(delay_seconds)
    
    agent = SimulatedDeviceAgent(failures_before_success=1)    
    try:
        agent.probe_with_retries(device, max_attempts=3)
    except RetryExhaustedError as error:
        logger.error("operation=probe device_id=%s outcome=exhausted error=%s",
                    device.device_id, error)
    except PermanentDeviceError as error:
        logger.error("operation=probe device_id=%s outcome=permanent device error=%s",
                     device.device_id, error)
    
    duration = time.perf_counter() - started_at
    logger.info(
        "operation=probing device_id=%s status=finished duration=%.3fs",
        device.device_id,
        duration,
    )