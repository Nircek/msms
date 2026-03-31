---
name: device-onboarder
description: Implement new instrument support from driver to simulation and checks
argument-hint: Provide IDN response, required readings, and initialization commands.
---

Implement new device support end-to-end.

## Standards Reference

- [../instructions/devices.instructions.md](../instructions/devices.instructions.md)
- [../instructions/python.instructions.md](../instructions/python.instructions.md)
- [../instructions/workflows.instructions.md](../instructions/workflows.instructions.md)

## Workflow

1. Confirm `*IDN?` response and required outputs.
2. Implement driver under `msms/connectivity/devices/` with registration and contract methods.
3. Wire missing imports for auto-registration if needed.
4. Extend simulation definitions for deterministic validation.
5. Add or update targeted tests or smoke coverage.

## Output Format

- Implementation summary
- Files changed
- Validation commands and outcomes
