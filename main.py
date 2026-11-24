"""Coordinate simulated probes, health checks, and device provisioning."""

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from device_workers import check_one_device, probe_one_device
from simulator import Device, DeviceInventory, provision_device
from telemetry import Telemetry

logger = logging.getLogger(__name__)


def main() -> None:
    """Run the simulator and log operation results and telemetry."""

    logging.basicConfig(
        filename="device_simulator.log",
        filemode="w",
        level=logging.INFO,
        format=(
            "%(asctime)s %(levelname)s [%(threadName)s] "
            "%(name)s %(message)s"
        ),
    )
    logger.info("Device simulator started")
    devices_fpath = Path.cwd() / "devices.json"
    logger.info("devices.json file path: %s", devices_fpath)

    telemetry = Telemetry()
    inventory = DeviceInventory()

    # Load the full inventory before submitting work for individual devices.
    with open(devices_fpath, "r") as json_file:
        device_data = json.load(json_file)
        for record in device_data:
            device = Device(**record)
            inventory.add(device)

    # Probe tasks run concurrently; each worker creates an independent agent.
    with ThreadPoolExecutor(
        max_workers=3, thread_name_prefix="probe"
    ) as executor:
        futures = {
            executor.submit(probe_one_device, device): device.device_id
            for device in inventory.device_inventory.values()
        }

        for future in as_completed(futures):
            device_id = futures[future]
            try:
                duration = future.result()
            except Exception:
                logger.exception(
                    "operation=probe device_id=%s outcome=failed",
                    device_id,
                )
            else:
                telemetry.record("probe", duration)

    # Health checks use the same bounded-concurrency pattern as probes.
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
            except Exception:
                logger.exception(
                    "operation=health_check device_id=%s outcome=failed",
                    expected_device_id,
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
                    "operation=health_check device_id=%s healthy=%s "
                    "reasons=%s healthcheck_duration=%s",
                    device_id,
                    health_result.healthy,
                    health_result.reasons,
                    duration,
                )

    # Apply the settings record that matches each device ID.
    logger.info("Provisioning devices started")
    provisioning_settings_fpath = Path.cwd() / "provisioning_settings.json"
    logger.info(
        "provisioning_settings.json file path: %s",
        provisioning_settings_fpath,
    )
    with open(provisioning_settings_fpath, "r") as settings_file:
        provisioning_data = json.load(settings_file)
        for data in provisioning_data:
            started_at = time.perf_counter()
            device = inventory.lookup(data["device_id"])
            provisioning_config = {
                key: value
                for key, value in data.items()
                if key != "device_id"
            }
            provision_result = provision_device(device, provisioning_config)
            logger.info(
                "operation=provision device_id=%s success=%s message=%s",
                provision_result.device_id,
                provision_result.success,
                provision_result.message,
            )
            telemetry.record(
                "provision", time.perf_counter() - started_at
            )

    # Report accumulated counts and durations once all operations are complete.
    logger.info("telemetry=%s", telemetry.snapshot())

if __name__ == "__main__":
    start = time.perf_counter()
    main()
    end = time.perf_counter()
    logger.info("Final time: %.3fs", end - start)
