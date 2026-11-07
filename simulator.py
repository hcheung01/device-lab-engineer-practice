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

class Device:
    """Represent one managed lab device."""

    def __init__(self, 
                 device_id: str,
                 device_type: str, 
                 device_state: str, 
                 os_version: str,
                 battery_level: int = 100,
                 is_connected: bool = True
                 ):
        self.device_id = device_id
        self.device_type = device_type
        if device_state not in ALLOWED_TRANSITIONS:
            raise ValueError(f"Invalid device state: {device_state}")
        self.device_state = device_state
        self.os_version = os_version
        self.battery_level = battery_level
        self.is_connected = is_connected
    
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
        
    def battery_level(self, device_id: str, inventory: DeviceInventory):
        if device_id not in inventory.device_inventory:
            raise KeyError(f"Device ID not in inventory: {device_id}")
        return inventory.lookup(device_id).battery_level
    
    def is_connected(self):
        pass
    
if __name__ == "__main__":
    device_id = "iphone5g"
    device_type = "phone"
    device_state = "available"
    new_device_state = "in_use"
    os_version = "27.10b"
    device1 = Device(
        device_id,
        device_type,
        device_state,
        os_version
    )
    
    print(device1.device_id, device1.device_type, device1.device_state, device1.os_version)
    device1.change_state(new_device_state)
    print(device1.device_id, device1.device_type, device1.device_state, device1.os_version)
    # device1.change_state("bad state")
    
    device_id = "ipadprom4"
    device_type = "tablet"
    device_state = "available"
    new_device_state = "in_use"
    os_version = "28.99abc"
    device2 = Device(
        device_id,
        device_type,
        device_state,
        os_version
    )
    print(device2.device_id, device2.device_type, device2.device_state, device2.os_version)
    device2.change_state(new_device_state)
    print(device2.device_id, device2.device_type, device2.device_state, device2.os_version)
    
    dev_inventory = DeviceInventory()
    print(dev_inventory.device_inventory)
    dev_inventory.add(device1)
    print(dev_inventory.device_inventory)
    dev_inventory.add(device2)
    print(dev_inventory.device_inventory)
    
    device = dev_inventory.lookup("ipadprom4")
    print(device.device_id)
    print("LISTING BY STATE")
    devices = dev_inventory.list_by_state("in_use")
    for device in devices:
        print(device.device_id)
    
    