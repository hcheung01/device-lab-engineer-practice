from simulator import Device, DeviceInventory, HealthCheckResult, ProvisioningResult, provision_device


if __name__ == "__main__":
    device_id = "iphone5g"
    device_type = "phone"
    device_state = "available"
    new_device_state = "in_use"
    os_version = "27.10b"
    device_battery = 92
    is_connected = True
    device1 = Device(
        device_id,
        device_type,
        device_state,
        os_version,
        device_battery,
        is_connected
    )
    
    print(device1.device_id, device1.device_type, device1.device_state, device1.os_version)
    device1.change_state(new_device_state)
    print(device1.device_id, device1.device_type, device1.device_state, device1.os_version)
    # device1.change_state("bad state")
    print("\n")
    
    device_id = "ipadprom4"
    device_type = "tablet"
    device_state = "available"
    new_device_state = "in_use"
    os_version = "28.99abc"
    device_battery = 33
    device_is_connect = False
    device2 = Device(
        device_id,
        device_type,
        device_state,
        os_version,
        device_battery,
        device_is_connect
    )
    print(device2.device_id, device2.device_type, device2.device_state, device2.os_version)
    device2.change_state(new_device_state)
    print(device2.device_id, device2.device_type, device2.device_state, device2.os_version)
    print("\n")

    device3 = Device(
        "watchx",
        "smartwatch",
        "available",
        "5.2",
        120,
        True
    )
    print(device3.device_id, device3.device_type, device3.device_state, device3.os_version)
    print("\n")
    
    device4 = Device(
        "visionpro",
        "smartglasses",
        "available",
        "5.11",
        None,
        True
    )
    print(device4.device_id, device4.device_type, device4.device_state, device4.os_version)
    print("\n")
    
    dev_inventory = DeviceInventory()
    print(dev_inventory.device_inventory)
    dev_inventory.add(device1)
    print(dev_inventory.device_inventory)
    dev_inventory.add(device2)
    print(dev_inventory.device_inventory)
    dev_inventory.add(device3)
    print(dev_inventory.device_inventory)
    dev_inventory.add(device4)
    print(dev_inventory.device_inventory)
    
    device = dev_inventory.lookup("ipadprom4")
    print(device.device_id, "\n")
    print("LISTING BY DEVICE STATE:")
    devices = dev_inventory.list_by_state("in_use")
    for device in devices:
        print(device.device_id)
    print("\n")
    
    
    device1_health_result = HealthCheckResult(device1.device_id)
    device1_battery = device1_health_result.get_device_battery(device1.device_id, dev_inventory)
    print(f"Device1 battery: {device1_battery}")
    device1_isconnected = device1_health_result.is_connected(device1.device_id, dev_inventory)
    print(f"Device1 is connected: {device1_isconnected}")
    device1_health_result.check_health(device1.device_id, dev_inventory)
    print(f"health status: {device1_health_result.healthy}")
    print(f"reasons: {device1_health_result.reasons}")
    print("\n")
    
    device2_health_result = HealthCheckResult(device2.device_id)
    device2_battery = device2_health_result.get_device_battery(device2.device_id, dev_inventory)
    print(f"Device2 battery: {device2_battery}")
    device2_isconnected = device2_health_result.is_connected(device2.device_id, dev_inventory)
    print(f"Device2 is connected: {device2_isconnected}")
    device2_health_result.check_health(device2.device_id, dev_inventory)
    print(f"health status: {device2_health_result.healthy}")
    print(f"reasons: {device2_health_result.reasons}")
    print("\n")

    device3_health_result = HealthCheckResult(device3.device_id)
    device3_battery = device3_health_result.get_device_battery(device3.device_id, dev_inventory)
    print(f"Device3 battery: {device3_battery}")
    device3_isconnected = device3_health_result.is_connected(device3.device_id, dev_inventory)
    print(f"Device3 is connected: {device3_isconnected}")
    device3_health_result.check_health(device3.device_id, dev_inventory)
    print(f"health status: {device3_health_result.healthy}")
    print(f"reasons: {device3_health_result.reasons}")
    print("\n")

    device4_health_result = HealthCheckResult(device4.device_id)
    device4_battery = device4_health_result.get_device_battery(device4.device_id, dev_inventory)
    print(f"Device4 battery: {device4_battery}")
    device4_isconnected = device4_health_result.is_connected(device4.device_id, dev_inventory)
    print(f"Device4 is connected: {device4_isconnected}")
    device4_health_result.check_health(device4.device_id, dev_inventory)
    print(f"health status: {device4_health_result.healthy}")
    print(f"reasons: {device4_health_result.reasons}")
    print(f"device state: {device4.device_state}")
    print("\n")
    

    current_configuration = {
        "locale": "cn_CHINA",
        "timezone": "somewhere/China",
        "test_profile": "no-test",
    }
    device5 = Device(
        "imac001",
        "personal computer",
        "available",
        "18.01",
        100,
        True,
        current_configuration
    )
    dev_inventory.add(device5)
    device5_health_result = HealthCheckResult(device5.device_id)
    
    # requested_configuration = {
    #     "os_version": "27.11b",
    #     "locale": "en_US",
    #     "timezone": "America/Los_Angeles",
    #     "test_profile": "smoke-test",
    # }
    requested_configuration = {
        "os_version": "27.11b",
        # "locale": "en_US",
        # "timezone": "America/Los_Angeles",
        # "test_profile": "smoke-test",
    }
    print(device5.device_id, device5.device_type, device5.device_state, device5.os_version)
    print(f"Device5 current configuration: {device5.configuration}")
    print(f"health status: {device5_health_result.healthy}")
    print(f"reasons: {device5_health_result.reasons}")
    print(f"device state: {device5.device_state}")
    
    provisioned_device5 = provision_device(device5, requested_configuration)
    print("provisioned results:\n", 
          "device_id:", provisioned_device5.device_id, 
          "\nrequested config:", provisioned_device5.requested_configuration, 
          "\nsuccess/fail:", provisioned_device5.success, 
          "\nmessage:", provisioned_device5.message)
    
    print(f"device5 os version: ", device5.os_version)
    print(f"device5 configuration", device5.configuration)
    