---
name: threading-auditor
description: Audit PyQt controller and manager threading safety and signal compliance
argument-hint: Provide changed UI controller or manager paths.
---

Audit thread-safety and signal-flow correctness for UI and manager changes.

## Standards Reference

- [../instructions/threading.instructions.md](../instructions/threading.instructions.md)
- [../instructions/signal-flow.instructions.md](../instructions/signal-flow.instructions.md)
- [../instructions/controllers.instructions.md](../instructions/controllers.instructions.md)
- [../instructions/naming.instructions.md](../instructions/naming.instructions.md)

## Required Checks

1. No direct manager calls after `moveToThread()`.
2. Correct signal ownership and connection direction.
3. Absence of blocking operations on UI thread.
4. Stable payload typing across signal-slot boundaries.
5. Controller responsibilities remain within defined boundaries.

## Output Format

- Findings sorted by severity
- Exact file and line references
- Recommended fixes and test follow-up
