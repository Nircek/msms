---
mode: agent
description: "Implement a new MSMS device driver end-to-end"
---
When adding support for a new instrument, use this prompt to generate code, tests, and simulation data.

1. Ask for and confirm the device's `*IDN?` response, required readings, and initialization steps.
2. Implement the driver in `msms/connectivity/devices/` following [../instructions/devices.instructions.md](../instructions/devices.instructions.md) and [../instructions/python.instructions.md](../instructions/python.instructions.md).
3. Update `msms/connectivity/devices/__init__.py` if an import is missing and add simulated responses to `msms/connectivity/sim_instruments.yml`.
4. Generate targeted tests or smoke steps that exercise the new readings, referencing [../instructions/workflows.instructions.md](../instructions/workflows.instructions.md) for commands.
5. Summarize manual validation guidance (e.g., required benchtop setup, expected values).
