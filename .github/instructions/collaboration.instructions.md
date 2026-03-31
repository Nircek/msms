---
name: Agent Collaboration Rules
description: Systematic execution, completeness, and trust-preserving behavior
scope:
  - "**/*"
applyTo: "**/*"
---

# Collaboration Rules

## Completeness

- Process all requested files and all requested instances.
- Do not use selective or partial shortcuts.

## Execution Pattern

1. Plan complete scope.
2. Execute across the full scope.
3. Validate with project checks.
4. Update instructions when conventions change.

## Direct User Markers

- Treat `TODO: Agent!` and `FIXME: Agent!` comments as explicit user directives.
- Implement requested behavior and remove resolved directive comments.

## Communication

- Avoid framing incomplete work as complete.
- Explicitly report residual risks or blockers.
