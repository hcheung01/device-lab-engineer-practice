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
            device = Device(**record)
            inventory.add(device)
    
    device = inventory.lookup("mac-004")
    health_result = HealthCheckResult(device.device_id).check_health(
        device.device_id, inventory
    )
    
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
    

if __name__ == "__main__":
    main()