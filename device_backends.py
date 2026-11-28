"""Pluggable execution backends for Simulated, Xcode Simulator, and Physical iOS devices."""

from __future__ import annotations

import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Protocol, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed


from simulator import (
    RETIRED,
    Device,
    DeviceInventory,
    HealthCheckResult,
    PermanentDeviceError,
    RetryableDeviceError,
    SimulatedDeviceAgent,
)

logger = logging.getLogger(__name__)


class DeviceBackend(Protocol):
    """Unified interface for probing and health-checking devices."""

    def probe(self, device: Device) -> str:
        """Verify reachability; raise RetryableDeviceError or PermanentDeviceError."""
        ...

    def check_health(
        self, device_id: str, inventory: DeviceInventory
    ) -> HealthCheckResult | None:
        """Return structured health findings without mutating lifecycle state."""
        ...


def _run_xcrun(args: Sequence[str], timeout: float = 20.0) -> str:
    """Execute an xcrun command with strict timeout and error classification."""
    cmd = ["xcrun", *args]
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise RetryableDeviceError(
            f"Command timed out after {timeout}s: {' '.join(cmd)}"
        ) from exc

    if completed.returncode != 0:
        stderr = (completed.stderr or completed.stdout).strip()
        lower = stderr.lower()
        # Classify permanent hardware/config errors vs transient daemon hiccups
        permanent_markers = (
            "invalid device",
            "unable to lookup",
            "locked",
            "untrusted",
            "not paired",
            "developer mode",
        )
        if any(marker in lower for marker in permanent_markers):
            raise PermanentDeviceError(f"Permanent xcrun error: {stderr}")
        raise RetryableDeviceError(
            f"Transient xcrun error (exit={completed.returncode}): {stderr}"
        )

    return completed.stdout


# ---------------------------------------------------------------------------
# 1. Existing In-Memory Simulated Backend
# ---------------------------------------------------------------------------
class SimulatedBackend:
    """Wraps your original SimulatedDeviceAgent and HealthCheckResult."""

    def __init__(self, failures_before_success: int = 1) -> None:
        self.failures_before_success = failures_before_success

    def probe(self, device: Device) -> str:
        agent = SimulatedDeviceAgent(
            failures_before_success=self.failures_before_success
        )
        return agent.probe(device)

    def check_health(
        self, device_id: str, inventory: DeviceInventory
    ) -> HealthCheckResult | None:
        return HealthCheckResult(device_id).check_health(device_id, inventory)


# ---------------------------------------------------------------------------
# 2. Real Local Xcode Simulator Backend (xcrun simctl)
# ---------------------------------------------------------------------------
class SimctlBackend:
    """Executes real probes and health checks against local Xcode Simulators."""

    def _get_sim_record(self, udid: str) -> dict | None:
        raw = _run_xcrun(["simctl", "list", "devices", "-j"], timeout=15.0)
        payload = json.loads(raw)
        for records in payload.get("devices", {}).values():
            for rec in records:
                if rec.get("udid") == udid:
                    return rec
        return None

    def probe(self, device: Device) -> str:
        if device.device_state == RETIRED:
            raise PermanentDeviceError(f"Cannot probe retired device {device.device_id}")

        record = self._get_sim_record(device.device_id)
        if record is None:
            raise PermanentDeviceError(f"Simulator UDID not found: {device.device_id}")
        if not record.get("isAvailable", False):
            raise PermanentDeviceError(
                f"Simulator runtime unavailable for {device.device_id}"
            )

        # Boot idempotently if not already booted, then verify CoreSimulator readiness
        if record.get("state") != "Booted":
            _run_xcrun(["simctl", "boot", device.device_id], timeout=30.0)
        _run_xcrun(["simctl", "bootstatus", device.device_id, "-b"], timeout=60.0)
        return f"Simulator {device.device_id} booted and responsive"

    def check_health(
        self, device_id: str, inventory: DeviceInventory
    ) -> HealthCheckResult | None:
        try:
            inventory.lookup(device_id)
        except KeyError:
            return None

        reasons: list[str] = []
        try:
            record = self._get_sim_record(device_id)
        except (RetryableDeviceError, PermanentDeviceError) as exc:
            return HealthCheckResult(device_id, healthy=False, reasons=[str(exc)])

        if record is None:
            reasons.append("Simulator UDID missing from CoreSimulator")
        else:
            if not record.get("isAvailable", False):
                reasons.append("Simulator runtime unavailable")
            if record.get("state") != "Booted":
                reasons.append(f"Simulator state is {record.get('state')} (expected Booted)")

        return HealthCheckResult(
            device_id=device_id,
            healthy=len(reasons) == 0,
            reasons=reasons,
        )

    def shutdown_all(self) -> str:
        """Shut down all currently booted Xcode Simulators."""
        _run_xcrun(["simctl", "shutdown", "all"], timeout=30.0)
        logger.info("operation=shutdown_all backend=simctl outcome=success")
        return "All Xcode Simulators shut down"



# ---------------------------------------------------------------------------
# 3. Real Physical Hardware Backend (xcrun devicectl)
# ---------------------------------------------------------------------------
class DevicectlBackend:
    """Executes real probes and health checks against physical iOS/iPadOS devices."""

    def _list_physical_devices(self) -> dict[str, dict]:
        """Run devicectl with --json-output and index devices by UDID / identifier."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=True) as tmp:
            _run_xcrun(
                ["devicectl", "list", "devices", "--json-output", tmp.name],
                timeout=20.0,
            )
            data = json.loads(Path(tmp.name).read_text(encoding="utf-8"))

        indexed: dict[str, dict] = {}
        for dev in data.get("result", {}).get("devices", []):
            identifier = dev.get("identifier")
            udid = dev.get("hardwareProperties", {}).get("udid")
            if identifier:
                indexed[identifier] = dev
            if udid:
                indexed[udid] = dev
        return indexed

    def probe(self, device: Device) -> str:
        if device.device_state == RETIRED:
            raise PermanentDeviceError(f"Cannot probe retired device {device.device_id}")

        devices = self._list_physical_devices()
        record = devices.get(device.device_id)
        if record is None:
            raise RetryableDeviceError(
                f"Physical device {device.device_id} not currently enumerated"
            )

        conn_props = record.get("connectionProperties", {})
        pairing_state = conn_props.get("pairingState")
        tunnel_state = conn_props.get("tunnelState")

        if pairing_state != "paired":
            raise PermanentDeviceError(
                f"Device {device.device_id} pairingState={pairing_state}"
            )
        if tunnel_state not in ("connected", "available"):
            raise RetryableDeviceError(
                f"Device {device.device_id} tunnelState={tunnel_state}"
            )

        return f"Physical device {device.device_id} paired and tunnel connected"

    def check_health(
        self, device_id: str, inventory: DeviceInventory
    ) -> HealthCheckResult | None:
        try:
            inventory.lookup(device_id)
        except KeyError:
            return None

        reasons: list[str] = []
        try:
            devices = self._list_physical_devices()
        except (RetryableDeviceError, PermanentDeviceError) as exc:
            return HealthCheckResult(device_id, healthy=False, reasons=[str(exc)])

        record = devices.get(device_id)
        if record is None:
            reasons.append("Device not visible to CoreDevice / usbmuxd")
        else:
            conn = record.get("connectionProperties", {})
            dev_props = record.get("deviceProperties", {})
            if conn.get("pairingState") != "paired":
                reasons.append(f"Unpaired device: {conn.get('pairingState')}")
            if not dev_props.get("developerModeStatus") == "enabled":
                reasons.append("Developer Mode is disabled")

        return HealthCheckResult(
            device_id=device_id,
            healthy=len(reasons) == 0,
            reasons=reasons,
        )

    def reboot_device(self, device_id: str) -> tuple[str, bool, str]:
        """Reboot a single physical device via devicectl."""
        try:
            _run_xcrun(
                ["devicectl", "device", "reboot", "--device", device_id],
                timeout=30.0,
            )
            return device_id, True, "Reboot triggered"
        except (RetryableDeviceError, PermanentDeviceError) as exc:
            return device_id, False, str(exc)

    def shutdown_all(self, max_workers: int = 4) -> dict[str, tuple[bool, str]]:
        """Reboot all connected physical devices (devicectl has no power-off command)."""
        devices = self._list_physical_devices()
        # Deduplicate by CoreDevice identifier so each physical device reboots once
        unique_ids = list({
            dev["identifier"]
            for dev in devices.values()
            if "identifier" in dev
        })

        results: dict[str, tuple[bool, str]] = {}
        with ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="devicectl_reboot"
        ) as pool:
            futures = {
                pool.submit(self.reboot_device, dev_id): dev_id
                for dev_id in unique_ids
            }
            for future in as_completed(futures):
                dev_id, ok, msg = future.result()
                results[dev_id] = (ok, msg)
                logger.info(
                    "operation=reboot device_id=%s success=%s message=%s",
                    dev_id,
                    ok,
                    msg,
                )
        return results
