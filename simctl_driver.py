"""Safe, concurrent wrapper around Apple's xcrun simctl for lab orchestration."""

from __future__ import annotations

import json
import logging
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Sequence

logger = logging.getLogger(__name__)


class SimctlError(Exception):
    """Base error for simctl command failures."""


class SimctlTimeoutError(SimctlError):
    """Raised when a simctl subprocess exceeds its timeout (retryable)."""


@dataclass(frozen=True)
class SimulatorDevice:
    udid: str
    name: str
    state: str          # e.g., "Booted", "Shutdown"
    runtime: str        # e.g., "com.apple.CoreSimulator.SimRuntime.iOS-18-2"
    is_available: bool


@dataclass(frozen=True)
class OperationOutcome:
    udid: str
    operation: str
    success: bool
    message: str


class SimctlDriver:
    """Execute bounded, timeout-enforced simctl commands."""

    def __init__(self, developer_dir: str | None = None) -> None:
        self._env = {"DEVELOPER_DIR": developer_dir} if developer_dir else None

    def _run(self, args: Sequence[str], timeout: float = 30.0) -> str:
        cmd = ["xcrun", "simctl", *args]
        try:
            completed = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                env=self._env,
            )
        except subprocess.TimeoutExpired as exc:
            raise SimctlTimeoutError(
                f"Command timed out after {timeout}s: {' '.join(cmd)}"
            ) from exc

        if completed.returncode != 0:
            stderr = completed.stderr.strip() or "unknown error"
            raise SimctlError(
                f"Command failed (exit={completed.returncode}): {stderr}"
            )
        return completed.stdout

    def list_devices(self, only_available: bool = True) -> list[SimulatorDevice]:
        """Discover all simulators via JSON output."""
        raw = self._run(["list", "devices", "-j"], timeout=15.0)
        payload = json.loads(raw)

        devices: list[SimulatorDevice] = []
        for runtime, records in payload.get("devices", {}).items():
            for rec in records:
                is_avail = bool(rec.get("isAvailable", False))
                if only_available and not is_avail:
                    continue
                devices.append(
                    SimulatorDevice(
                        udid=rec["udid"],
                        name=rec["name"],
                        state=rec["state"],
                        runtime=runtime,
                        is_available=is_avail,
                    )
                )
        return devices

    def boot_and_wait(self, udid: str, timeout: float = 90.0) -> OperationOutcome:
        """Idempotently boot a simulator and block until CoreSimulator is ready."""
        try:
            # Check current state first so retries don't fail on "already Booted"
            current = {d.udid: d for d in self.list_devices(only_available=False)}.get(udid)
            if current is None:
                return OperationOutcome(udid, "boot", False, "Unknown simulator UDID")

            if current.state != "Booted":
                self._run(["boot", udid], timeout=30.0)

            # -b blocks until boot completes; prevents racing subsequent app installs
            self._run(["bootstatus", udid, "-b"], timeout=timeout)
            return OperationOutcome(udid, "boot", True, "Booted and ready")
        except SimctlError as exc:
            return OperationOutcome(udid, "boot", False, str(exc))

    def reset_device(self, udid: str) -> OperationOutcome:
        """Cleanly shut down and factory-erase a simulator between test runs."""
        try:
            current = {d.udid: d for d in self.list_devices(only_available=False)}.get(udid)
            if current and current.state != "Shutdown":
                self._run(["shutdown", udid], timeout=30.0)
            self._run(["erase", udid], timeout=45.0)
            return OperationOutcome(udid, "reset", True, "Shutdown and erased")
        except SimctlError as exc:
            return OperationOutcome(udid, "reset", False, str(exc))


def boot_fleet(
    driver: SimctlDriver, udids: list[str], max_workers: int = 4
) -> list[OperationOutcome]:
    """Boot multiple simulators concurrently with bounded host resource usage."""
    outcomes: list[OperationOutcome] = []
    with ThreadPoolExecutor(
        max_workers=max_workers, thread_name_prefix="sim_boot"
    ) as pool:
        future_to_udid = {
            pool.submit(driver.boot_and_wait, udid): udid for udid in udids
        }
        for future in as_completed(future_to_udid):
            udid = future_to_udid[future]
            try:
                outcomes.append(future.result())
            except Exception as exc:
                logger.exception("operation=boot udid=%s outcome=unexpected_error", udid)
                outcomes.append(OperationOutcome(udid, "boot", False, str(exc)))
    return outcomes


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(threadName)s] %(message)s")
    driver = SimctlDriver()
    inventory = driver.list_devices()
    logger.info("Discovered %d available simulators", len(inventory))

    # Boot up to 2 simulators concurrently as a smoke test
    sample_udids = [d.udid for d in inventory[:2]]
    if sample_udids:
        results = boot_fleet(driver, sample_udids, max_workers=2)
        for res in results:
            logger.info("udid=%s op=%s success=%s msg=%s", res.udid, res.operation, res.success, res.message)
