from simulator import Device, DeviceInventory, HealthCheckResult, provision_device
from pathlib import Path
import logging
import json

logger = logging.getLogger(__name__)

def main():
    logging.basicConfig(filename='device_simulator.log', level=logging.INFO)
    logger.info('Started')
    devices_fpath = Path.cwd() / "devices.json"
    logger.info(f'devices json file path: {devices_fpath}')
    
    inventory = DeviceInventory()
    with open(devices_fpath, "r") as json_file:
        device_data = json.load(json_file)
        for record in device_data:
            logger.info("device record: {record}")
            device = Device(**record)
            inventory.add(device)

    logger.info("Inventory")
    logger.info(inventory.device_inventory)
    
    device = inventory.lookup("iphone-001")
    
    device_health = HealthCheckResult(device.device_id)
    logger.info(f"device_id: {device.device_id}, healthy: {device_health.healthy}, reason: {device_health.reasons}, os_version: {device.os_version}, configuration: {device.configuration}")
    
    result = provision_device(device, {
        "os_version": "18.2",
        "locale": "en_US",
        "timezone": "America/Los_Angeles",
        "test_profile": "ios-smoke",
    })
    logger.info(f"device_id: {device.device_id}, healthy: {device_health.healthy}, reason: {device_health.reasons}, os_version: {device.os_version}, configuration: {device.configuration}")
if __name__ == "__main__":
    main()