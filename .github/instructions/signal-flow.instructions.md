---
name: UI Signal Flow
description: Signal ownership and command or data flow contracts across UI and managers
scope:
  - msms/ui/**/*.py
applyTo: "msms/ui/**/*.py"
---

# Signal Flow Contract

## Ownership

- Components own the signals they emit.
- Managers own state and data publication signals.
- `ApplicationController` wires components and managers; it does not become a surrogate signal owner.

## Command and Data Direction

- Commands: UI component signal to manager slot.
- Data: manager signal to UI slot.
- Cross-manager interactions: signal-slot only.

## Payload Rules

- Keep payloads predictable and typed.
- Preserve payload shape stability when refactoring.
- Avoid in-place mutation of payload objects after emission.

## Verification

- When debugging stale UI or missing updates, trace full emission and slot path from source to sink.
