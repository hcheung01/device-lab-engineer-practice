# Device Lab Simulator

A hands-on Python project for practicing device-lab infrastructure concepts for Lab Engineer role.

## Goal

1. Device identity, lifecycle states, and inventory
2. Device health checks
3. Provisioning and configuration
4. Structured logging and telemetry
5. Error handling, retries, and recovery
6. Bounded concurrency for fleet operations
7. Mutexes for safe concurrent device updates

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

### Considerations

1. Which data belongs on a `Device`, and which belongs in the inventory?
2. Why should the inventory reject duplicate IDs?
3. What should happen if a device is retired and someone tries to make it available again?

### Task

Implement the TODOs without adding health checks, provisioning, persistence, or concurrency yet. Try a few manual examples in a Python REPL and review design choices.

## Exercise 2: Check device health

Add a simulated health check that reports whether a device is healthy and why. Keep health separate from lifecycle state: a device can be available while unhealthy, for example.

### Requirements

- Represent health-check results with a clear status and a list of reasons or check details.
- Check at least battery level and connectivity using simulated values.
- Treat missing or out-of-range readings as unhealthy instead of silently accepting them.
- Do not change lifecycle state as a side effect of checking health.

### Task

Add health-check behavior and try healthy, unhealthy, and invalid-reading examples. Decide which data belongs to the device and which belongs in the health-check result.

## Exercise 3: Provision and configure a device

Simulate preparing an available device for use. Provisioning should be an explicit operation with a result that callers can inspect.

### Requirements

- Accept a configuration describing the desired operating-system version and required settings.
- Validate the device and configuration before applying changes.
- Only provision devices in an allowed lifecycle state; define and document the rule.
- Return a result that identifies success or failure and explains any failure.
- Keep the operation simulated: do not call real devices or external services.

### Task

Implement provisioning and try valid configuration, invalid configuration, and a device in a disallowed state. Avoid leaving the device partially updated when validation fails.

## Exercise 4: Add structured logging and telemetry

Make simulator operations observable so an operator can understand what happened without relying on ad hoc print statements.

### Requirements

- Use Python's `logging` module
- Useful context such as device ID, operation, outcome, and failure reason.
- Keep log messages structured and consistent; do not include secrets or unnecessary device data.
- Record basic operation counts or durations in a small in-memory telemetry component.

### Task

Add logging and telemetry around health checks and provisioning. Show how a caller can configure logging and inspect the collected metrics.

## Exercise 5: Handle errors, retries, and recovery

Make simulated operations resilient to temporary failures while ensuring permanent failures are reported clearly.

### Requirements

- Distinguish retryable failures from validation or other permanent failures.
- Retry only retryable failures, with a configurable maximum number of attempts.
- Use a bounded delay between retries and make the delay injectable or replaceable for fast manual demonstrations.
- Return or raise an error that includes the final outcome and attempt count.
- Do not retry an operation that could apply the same change twice unless it is made safe to repeat.

### Task

Add a simulated operation that can fail temporarily, then demonstrate eventual success, exhausted retries, and a permanent failure. Keep recovery behavior explicit and observable.

## Exercise 6: Run fleet operations with bounded concurrency

Run an operation across many devices without creating an unbounded number of workers or losing per-device results.

### Requirements

- Accept a collection of devices and a configurable maximum number of workers.
- Run a simulated operation concurrently while respecting that worker limit.
- Collect one success or failure result for every device, associated with its device ID.
- Ensure one device's failure does not prevent results from other devices from being collected.
- Avoid sharing mutable result data without a safe coordination strategy.

### Task

Apply a health check or provisioning operation to a small fleet. Try different worker limits and include a deliberate failure to confirm the other results are still returned.

## Exercise 7: Protect concurrent device updates with a mutex

After adding bounded concurrency for fleet operations, use a mutex to protect shared device state when multiple workers may update it at the same time.

### Requirements

- Use Python's `threading.Lock` to guard changes to a device's lifecycle state.
- Make each state change check the current state and apply the transition while holding the same lock.
- Keep the critical section limited to the state check and update.
- Demonstrate concurrent attempts to update a device and confirm that invalid transitions are still rejected.

## Exercise 8: Observe the device fleet with Prometheus and Grafana

The current telemetry component keeps counts and duration totals in memory and writes a snapshot to the log when the run ends. That is useful for a short local run, but Grafana needs metrics that a monitoring system can collect while the simulator is running.

Use this data flow:

`simulator → Prometheus metrics endpoint → Prometheus → Grafana dashboard`

Prometheus collects metrics from the simulator's HTTP `/metrics` endpoint. Grafana queries Prometheus and displays the results.

### Requirements

- Keep the simulator running long enough for Prometheus to scrape it repeatedly, such as by running fleet cycles on a configurable interval.
- Expose metrics in Prometheus format from the Python process.
- Track operation totals by operation and outcome, operation duration as a distribution, and current device totals by lifecycle state.
- Track simulator liveness and device heartbeat freshness as separate signals. Record when the last fleet cycle completed successfully, and track which devices have checked in within a configurable freshness window.
- Show heartbeat freshness and stale-device counts in Grafana. Keep device IDs in logs or inventory lookups; do not add one metric time series per device ID for this exercise.
- Choose a heartbeat interval and stale threshold, and account for delayed checks so one missed interval does not automatically classify hardware as dead.
- Use bounded labels such as `operation`, `outcome`, and `state`. Do not use a device ID as a metric label; a unique label per device creates high-cardinality metrics that are expensive to store and query.
- Configure Prometheus to scrape the simulator and connect Grafana to Prometheus as a data source.
- Build a dashboard showing operation rate, failures, latency percentiles, fleet size by lifecycle state, simulator liveness, and stale-device counts.
- Keep existing logs for per-device details and errors. Use metrics for fleet-wide trends; avoid putting sensitive or unbounded details in metric labels.

### Task

Before implementing, write down the name, type, labels, and meaning of each metric you plan to expose. Then add instrumentation, run the simulator and monitoring services locally, and verify that the dashboard changes when you run successful and failing operations.

### Design questions

1. Why should operation duration be a histogram instead of only a total duration?
2. What does a latency percentile tell you that an average does not?
3. How will you distinguish a failed operation from a failed device health check?
4. What should happen to the lifecycle-state gauge when the inventory changes?
5. What monitoring data belongs in logs, and what belongs in metrics?
6. Why can a reachable `/metrics` endpoint still report a stuck simulator?
7. Does a stale device heartbeat prove that the device is dead? What other signals would you check?
