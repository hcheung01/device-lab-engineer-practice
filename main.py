from simulator import Device, DeviceInventory, HealthCheckResult, SimulatedDeviceAgent, RetryExhaustedError, PermanentDeviceError, provision_device
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from telemetry import Telemetry
import random
import json
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

def main() -> None:
    logging.basicConfig(
        filename="device_simulator.log",
        filemode="w",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(threadName)s] %(name)s %(message)s",
    )
    logger.info('Device simulator started')
    devices_fpath = Path.cwd() / "devices.json"
    logger.info(f'devices.json file path: {devices_fpath}')
    
    telemetry = Telemetry()
    inventory = DeviceInventory()
    
    with open(devices_fpath, "r") as json_file:
        device_data = json.load(json_file)
        for record in device_data:
            device = Device(**record)
            inventory.add(device)
    
    probe_target = inventory.lookup("hiphone-001")
    agent = SimulatedDeviceAgent(failures_before_success=3)    
    try:
        probe_result = agent.probe_with_retries(probe_target, max_attempts=3)
    except RetryExhaustedError as error:
        logger.error("operation=probe device_id=%s outcome=exhausted error=%s",
                    probe_target.device_id, error)
        
    probe_target2 = inventory.lookup("mypad-008")
    agent2 = SimulatedDeviceAgent(failures_before_success=3)    
    try:
        probe_result2 = agent2.probe_with_retries(probe_target2, max_attempts=3)
    except PermanentDeviceError as error:
        logger.error("operation=probe device_id=%s outcome=permanent_failure error=%s",
                    probe_target2.device_id, error)
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(check_one_device, device.device_id, inventory):
                device.device_id
            for device in inventory.device_inventory.values()
        }

        for future in as_completed(futures):
            expected_device_id = futures[future]
            try:
                device_id, health_result, duration = future.result()
                if device_id == "hiphone-001":
                    raise RuntimeError("Simulated worker failure")
            except Exception:
                logger.exception(
                    "operation=health_check device_id=%s outcome=failed",
                    expected_device_id
                )
                continue
            
            telemetry.record("health_check", duration)

            if health_result is None:
                logger.error(
                    "operation=health_check device_id=%s outcome=not_found",
                    device_id,
                )
            else:
                logger.info(
                    "operation=health_check device_id=%s healthy=%s reasons=%s healthcheck_duration=%s",
                    device_id,
                    health_result.healthy,
                    health_result.reasons,
                    duration
                )
    
    logger.info('Provisioning devices started')
    provisioning_settings_fpath = Path.cwd() / "provisioning_settings.json"
    logger.info(f'provisioning_settings.json file path: {provisioning_settings_fpath}')
    with open(provisioning_settings_fpath, "r") as file:
        provisioning_data = json.load(file)
        for data in provisioning_data:
            started_at = time.perf_counter()
            device = inventory.lookup(data["device_id"])
            provisioning_config = {
                key: value
                for key, value in data.items()
                if key != "device_id"
            }
            provision_result = provision_device(
                device, 
                provisioning_config
            )
            logger.info(
                "operation=provision device_id=%s success=%s message=%s",
                provision_result.device_id,
                provision_result.success,
                provision_result.message,
            )
            telemetry.record("provision", time.perf_counter() - started_at)
        
        # Final Telemetry snapshot
        logger.info("telemetry=%s", telemetry.snapshot())
                                     
if __name__ == "__main__":
    main()
