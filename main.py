from simulator import Device, DeviceInventory, HealthCheckResult, provision_device
from pathlib import Path
from telemetry import Telemetry
import json
import time
import logging

logger = logging.getLogger(__name__)

def main():
    logging.basicConfig(
        filename="device_simulator.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logger.info('Simulator started')
    devices_fpath = Path.cwd() / "devices.json"
    logger.info(f'devices json file path: {devices_fpath}')
    
    telemetry = Telemetry()
    inventory = DeviceInventory()
    
    with open(devices_fpath, "r") as json_file:
        device_data = json.load(json_file)
        for record in device_data:
            device = Device(**record)
            inventory.add(device)
    

    for device in inventory.device_inventory.values():
        started_at = time.perf_counter()
        health_result = HealthCheckResult(device.device_id).check_health(
            device.device_id, inventory
        )
        telemetry.record("health_check", time.perf_counter() - started_at)

        if health_result is None:
            logger.error(
                "operation=health_check device_id=%s outcome=not_found",
                device.device_id,
            )
        else:
            logger.info(
                "operation=health_check device_id=%s healthy=%s reasons=%s",
                device.device_id,
                health_result.healthy,
                health_result.reasons,
            )
    
    provision_target = inventory.lookup("iphone-001")
    started_at = time.perf_counter()
    provision_result = provision_device(provision_target, {
        "os_version": "18.2",
        "locale": "en_US",
        "timezone": "America/Los_Angeles",
        "test_profile": "ios-smoke",
    })
    telemetry.record("provision", time.perf_counter() - started_at)
    logger.info(
        "operation=provision device_id=%s success=%s message=%s",
        provision_result.device_id,
        provision_result.success,
        provision_result.message
    )
    logger.info("telemetry=%s", telemetry.snapshot())

if __name__ == "__main__":
    main()
