---
name: Device Driver Contract
description: Registration, discovery, and update contract for instrument drivers
scope:
  - msms/connectivity/devices/**/*.py
applyTo: "msms/connectivity/devices/**/*.py"
---

# Device Driver Contract

## Required Shape

- Each driver subclasses `DeviceBase` and uses `@register_device(...)`.
- Implement:
  - `can_handle(cls, idn_parts)` for `*IDN?` matching
  - `initialize(self)` for one-time setup
  - `update(self)` for periodic readings

## Behavioral Rules

- Keep hardware-specific logic in the driver file only.
- Return stable key names in reading dictionaries.
- Maintain resilient behavior on transient communication failures.
- Keep discovery compatibility with simulated devices by updating `sim_instruments.yml` where relevant.

## Boundary Rule

- Driver code may use VISA through connectivity abstractions only.
