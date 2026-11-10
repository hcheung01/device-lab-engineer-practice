"""Device lab simulator.

Implement device identity, lifecycle transitions, and inventory.
"""

AVAILABLE = "available"
IN_USE = "in_use"
MAINTENANCE = "maintenance"
RETIRED = "retired"

ALLOWED_TRANSITIONS = {
    AVAILABLE: {IN_USE, MAINTENANCE},
    IN_USE: {AVAILABLE, MAINTENANCE},
    MAINTENANCE: {AVAILABLE, RETIRED},
    RETIRED: set(),
}

DeviceConfig = dict[str, str]

class Device:
    """Represent one managed lab device."""

    def __init__(self, 
                 device_id: str,
                 device_type: str, 
                 device_state: str, 
                 os_version: str,
                 battery_level: int | None = 100,
                 is_connected: bool = True,
                 configuration: DeviceConfig | None = None
                 ):
        
        self.device_id = device_id
        self.device_type = device_type
        if device_state not in ALLOWED_TRANSITIONS:
            raise ValueError(f"Invalid device state: {device_state}")
        self.device_state = device_state
        self.os_version = os_version
        self.battery_level = battery_level
        self.is_connected = is_connected
        self.configuration = {} if configuration is None else configuration
        
    def change_state(self, new_state: str) -> None:
        allow_states = ALLOWED_TRANSITIONS[self.device_state]
        if new_state not in allow_states:
            raise ValueError(f"New device state not allowed: {new_state}")
        self.device_state = new_state

class DeviceInventory:
    """Store and query the devices managed by the simulator."""

    def __init__(self):
        self.device_inventory = {}
    
    def add(self, device: Device) -> None:
        if device.device_id in self.device_inventory:
            raise ValueError(f"Duplicate ID: {device.device_id}")
        self.device_inventory[device.device_id] = device
    
    def lookup(self, device_id: str) -> Device:
        if device_id not in self.device_inventory:
            raise KeyError(f"Device ID not in inventory: {device_id}")
        return self.device_inventory[device_id]
    
    def list_by_state(self, state: str) -> list[Device]:
        devices = []
        for device in self.device_inventory.values():
            if device.device_state == state:
                devices.append(device)
        return devices

class HealthCheckResult:
    """Check health of device"""
    
    def __init__(self,
                 device_id: str,
                 healthy: bool = True,
                 reasons: list[str] | None = None
                 ):
        self.device_id = device_id
        self.healthy = healthy
        self.reasons = [] if reasons is None else reasons
        
    def get_device_battery(self, device_id: str, inventory: DeviceInventory):
        try:
            device = inventory.lookup(device_id)
        except KeyError:
            return None            
        return device.battery_level
    
    def is_connected(self, device_id: str, inventory: DeviceInventory):
        try:
            device = inventory.lookup(device_id)
        except KeyError:
            return None
        return device.is_connected

    def check_health(self, device_id: str, inventory: DeviceInventory):
        try:
            device = inventory.lookup(device_id)
        except KeyError:
            return None
        if device.battery_level is None or not 20 <= device.battery_level <= 100:
            self.reasons.append(f"battery level: {device.battery_level}")
            self.healthy = False
        if device.is_connected is None or device.is_connected is False:
            self.reasons.append(f"device connected: {device.is_connected}")
            self.healthy = False
        return self


class ProvisioningResult:
    def __init__(self,
                 device_id: str,
                 requested_configuration: DeviceConfig,
                 success: bool,
                 message: str
                 ) -> None:
        self.device_id = device_id
        self.requested_configuration = requested_configuration
        self.success = success
        self.message = message

def provision_device(device: Device, config: DeviceConfig) -> ProvisioningResult:
    if device.device_state != AVAILABLE:
        return ProvisioningResult(
            device.device_id,
            config,
            False,
            "Device must be available"
        )

    if "os_version" not in config or not config["os_version"]:
        return ProvisioningResult(
            device.device_id,
            config,
            False,
            "Missing os version"
        )
    settings_required = ["locale", "timezone", "test_profile"]
    missed_settings = [setting for setting in settings_required if not config.get(setting)]
    if missed_settings:
        return ProvisioningResult(
            device.device_id,
            config,
            False,
            f"Missing settings: {', '.join(missed_settings)}"
        )
    device.os_version = config["os_version"]
    device.configuration = {
        key: value
        for key, value in config.items()
        if key != "os_version"
    }
    return ProvisioningResult(
        device.device_id,
        config,
        True,
        "Provisioning completed"
    )