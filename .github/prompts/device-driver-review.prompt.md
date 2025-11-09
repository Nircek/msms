---
mode: ask
description: "Review a device driver change for MSMS patterns and risks"
---
Use this prompt when you need a focused code review of a device driver in `msms/connectivity/devices/`.

1. Summarize the change in two sentences max.
2. Audit the diff against the contract in [../instructions/devices.instructions.md](../instructions/devices.instructions.md) and the broader architecture in [../instructions/architecture.instructions.md](../instructions/architecture.instructions.md).
3. List issues ordered by severity. Include file names and precise line references. Highlight:
   - Incorrect or missing `@register_device` metadata
   - Violations of the VISA abstraction boundaries
   - Error handling that skips `error_cool_down_context_manager()` or loses last-known readings
   - Missing type hints or questionable return data shapes
4. Identify missing or outdated simulated responses in `msms/connectivity/sim_instruments.yml` when applicable.
5. Close with residual risks or open questions if the review cannot be fully conclusive.
