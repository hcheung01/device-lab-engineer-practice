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
7. Mutexes for safe concurrent device updates
8. Reliability and scale trade-offs

The simulator uses in-memory devices and simulated operations. It does not connect to or change real devices.

Interview prompts for each exercise are collected in [INTERVIEW_QUESTIONS.md](INTERVIEW_QUESTIONS.md).

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

Implement the TODOs without adding health checks, provisioning, persistence, or concurrency yet. Try a few manual examples in a Python REPL and review your design choices.

## Exercise 2: Check device health

Add a simulated health check that reports whether a device is healthy and why. Keep health separate from lifecycle state: a device can be available while unhealthy, for example.

### Requirements

- Represent health-check results with a clear status and a list of reasons or check details.
- Check at least battery level and connectivity using simulated values.
- Treat missing or out-of-range readings as unhealthy instead of silently accepting them.
- Do not change lifecycle state as a side effect of checking health.

### Your task

Add health-check behavior and try healthy, unhealthy, and invalid-reading examples. Decide which data belongs to the device and which belongs in the health-check result.

## Exercise 3: Provision and configure a device

Simulate preparing an available device for use. Provisioning should be an explicit operation with a result that callers can inspect.

### Requirements

- Accept a configuration describing the desired operating-system version and required settings.
- Validate the device and configuration before applying changes.
- Only provision devices in an allowed lifecycle state; define and document the rule.
- Return a result that identifies success or failure and explains any failure.
- Keep the operation simulated: do not call real devices or external services.

### Your task

Implement provisioning and try valid configuration, invalid configuration, and a device in a disallowed state. Avoid leaving the device partially updated when validation fails.

## Exercise 4: Add structured logging and telemetry

Make simulator operations observable so an operator can understand what happened without relying on ad hoc print statements.

### Requirements

- Use Python's `logging` module instead of printing operational messages from library code.
- Include useful context such as device ID, operation, outcome, and failure reason.
- Keep log messages structured and consistent; do not include secrets or unnecessary device data.
- Record basic operation counts or durations in a small in-memory telemetry component.

### Your task

Add logging and telemetry around health checks and provisioning. Show how a caller can configure logging and inspect the collected metrics.

## Exercise 5: Handle errors, retries, and recovery

Make simulated operations resilient to temporary failures while ensuring permanent failures are reported clearly.

### Requirements

- Distinguish retryable failures from validation or other permanent failures.
- Retry only retryable failures, with a configurable maximum number of attempts.
- Use a bounded delay between retries and make the delay injectable or replaceable for fast manual demonstrations.
- Return or raise an error that includes the final outcome and attempt count.
- Do not retry an operation that could apply the same change twice unless it is made safe to repeat.

### Your task

Add a simulated operation that can fail temporarily, then demonstrate eventual success, exhausted retries, and a permanent failure. Keep recovery behavior explicit and observable.

## Exercise 6: Run fleet operations with bounded concurrency

Run an operation across many devices without creating an unbounded number of workers or losing per-device results.

### Requirements

- Accept a collection of devices and a configurable maximum number of workers.
- Run a simulated operation concurrently while respecting that worker limit.
- Collect one success or failure result for every device, associated with its device ID.
- Ensure one device's failure does not prevent results from other devices from being collected.
- Avoid sharing mutable result data without a safe coordination strategy.

### Your task

Apply a health check or provisioning operation to a small fleet. Try different worker limits and include a deliberate failure to confirm the other results are still returned.

## Exercise 7: Protect concurrent device updates with a mutex

After adding bounded concurrency for fleet operations, use a mutex to protect shared device state when multiple workers may update it at the same time.

### Requirements

- Use Python's `threading.Lock` to guard changes to a device's lifecycle state.
- Make each state change check the current state and apply the transition while holding the same lock.
- Keep the critical section limited to the state check and update.
- Demonstrate concurrent attempts to update a device and confirm that invalid transitions are still rejected.

## Exercise 8: Consider reliability and scale trade-offs

Review the simulator as if it were the prototype for a larger device-lab service. Identify where the in-memory, single-process design stops meeting operational needs.

### Requirements

- Identify failure modes across device state, provisioning, concurrency, and observability.
- Define a small set of service-level measures, such as operation success rate and latency.
- Explain how persistence, multiple service instances, and partial failures would change the design.
- Propose one reliability improvement and describe its cost or trade-off before implementing it.

### Your task

Write a short design note with the failure scenario, proposed change, expected benefit, and trade-off. Keep this exercise focused on reasoning; do not add a database or external service to the simulator.
