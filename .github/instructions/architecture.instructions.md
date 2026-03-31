---
name: Architecture Boundaries
description: Layer responsibilities and allowed cross-layer interactions
scope:
  - msms/**/*.py
applyTo: "msms/**/*.py"
---

# Architecture Boundaries

## Layer Responsibilities

- `msms/ui/` renders widgets, owns user interactions, and delegates domain behavior.
- `msms/ui/controllers/` coordinates UI behavior and manager signal wiring.
- `msms/ui/managers/` runs acquisition, storage, and automation work in worker threads.
- `msms/connectivity/` owns VISA discovery and device I/O.

## Allowed Interaction Paths

- UI to managers: signal-slot only after thread move.
- Managers to UI: signals carrying immutable payloads.
- Manager to manager: signals routed by controller wiring.
- Non-connectivity code to VISA: prohibited.

## Data Flow Canon

- Acquisition pipeline is `DeviceManager -> StorageManager -> UI controllers/widgets`.
- Automation commands flow through manager signals, not direct UI-triggered manager calls.
- Keep synchronous state in small controller caches only when UI needs immediate read access.
