# Device Lab Simulator

A hands-on Python project for practicing device-lab infrastructure concepts for Lab Engineer role.

## Learning path

Build this in small steps. Each exercise adds one operational capability:

1. Device identity, lifecycle states, and inventory
2. Device health checks
3. Provisioning and configuration
4. Structured logging and telemetry
5. Error handling, retries, and recovery
6. Bounded concurrency for fleet operations
7. Reliability and scale trade-offs

The simulator uses in-memory devices and simulated operations. It does not connect to or change real devices.

## Exercise 1: Model a device and its lifecycle

Implement the starter in `simulator.py`.

### Requirements

- Create a `Device` class with a stable device ID, a device type, an operating-system version, and a lifecycle state.
- Support these lifecycle states: `available`, `in_use`, `maintenance`, and `retired`.
- Create a `DeviceInventory` that can add a device, look one up by ID, and list devices by state.
- Reject duplicate IDs when adding a device.
- Allow only valid state changes. For this exercise, use these transitions:
  - `available` → `in_use` or `maintenance`
  - `in_use` → `available` or `maintenance`
  - `maintenance` → `available` or `retired`
  - `retired` → no other state
- Raise a clear exception for an unknown device or an invalid transition.

### Before coding

Write down your answers to these questions:

1. Which data belongs on a `Device`, and which belongs in the inventory?
2. Why should the inventory reject duplicate IDs?
3. What should happen if a device is retired and someone tries to make it available again?

### Your task

Implement the TODOs without adding health checks, provisioning, persistence, or concurrency yet. Try a few manual examples in a Python REPL. When ready, paste your implementation here and explain one design choice as if you were in an interview.

### Interview practice

How would you represent device lifecycle state so invalid transitions are difficult to introduce? What would you change if multiple workers could update the same device at the same time?
