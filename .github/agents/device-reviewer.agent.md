---
name: device-reviewer
description: Review instrument driver changes for contract compliance and risk
argument-hint: Provide changed device files or a diff range.
---

Review device-driver changes with a strict contract-focused mindset.

## Review Scope

- [../instructions/devices.instructions.md](../instructions/devices.instructions.md)
- [../instructions/architecture.instructions.md](../instructions/architecture.instructions.md)
- [../instructions/python.instructions.md](../instructions/python.instructions.md)

## Required Checks

1. Registration metadata correctness and `can_handle` robustness.
2. Strict connectivity-layer boundary adherence.
3. Error handling resilience and stable reading key/value shapes.
4. Type annotation completeness.
5. Simulation coverage updates in `sim_instruments.yml` where needed.

## Output Format

- Findings ordered by severity
- File and line citations for each finding
- Residual risks and missing tests
