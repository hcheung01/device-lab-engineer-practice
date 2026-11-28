"""Generate devices.json and provisioning_settings.json from local Xcode Simulators."""

import json
import subprocess
from pathlib import Path


def main() -> None:
    raw = subprocess.check_output(
        ["xcrun", "simctl", "list", "devices", "-j"], text=True
    )
    data = json.loads(raw)

    devices_payload = []
    provisioning_payload = []

    for runtime, records in data.get("devices", {}).items():
        # Extract readable OS version (e.g., "iOS-18-2" -> "iOS 18.2")
        os_label = runtime.rsplit(".", 1)[-1].replace("-", " ", 1).replace("-", ".")

        for rec in records:
            if not rec.get("isAvailable", False):
                continue

            udid = rec["udid"]
            devices_payload.append(
                {
                    "device_id": udid,
                    "device_type": rec["name"],
                    "device_state": "available",
                    "os_version": os_label,
                    "battery_level": 100,
                    "is_connected": True,
                }
            )
            provisioning_payload.append(
                {
                    "device_id": udid,
                    "os_version": os_label,
                    "locale": "en_US",
                    "timezone": "America/Los_Angeles",
                    "test_profile": "lab-smoke-v1",
                }
            )

            if len(devices_payload) >= 5:
                break
        if len(devices_payload) >= 5:
            break

    config_dir = Path.cwd() / "configurations"
    config_dir.mkdir(parents=True, exist_ok=True)

    (config_dir / "devices.json").write_text(
        json.dumps(devices_payload, indent=2) + "\n", encoding="utf-8"
    )
    (config_dir / "provisioning_settings.json").write_text(
        json.dumps(provisioning_payload, indent=2) + "\n", encoding="utf-8"
    )

    print(f"Wrote {len(devices_payload)} devices to {config_dir}")


if __name__ == "__main__":
    main()
