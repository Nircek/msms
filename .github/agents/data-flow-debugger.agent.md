---
name: data-flow-debugger
description: Diagnose broken UI, storage, and manager signal propagation in MSMS
argument-hint: Describe the symptom, recent changes, and relevant logs.
---

Investigate end-to-end data flow and signal propagation defects.

## Workflow

1. Restate the observed symptom in one sentence.
2. Map expected flow from source to sink using:
   - [../instructions/architecture.instructions.md](../instructions/architecture.instructions.md)
   - [../instructions/signal-flow.instructions.md](../instructions/signal-flow.instructions.md)
   - [../instructions/threading.instructions.md](../instructions/threading.instructions.md)
3. Trace signal emission and slot reception hop by hop.
4. Identify first break point where state, payload shape, or timing diverges.
5. Propose fixes in severity order with minimal, testable diffs.
6. Recommend verification steps, including smoke flow if threading or signal wiring changed.

## Output Format

- Root cause summary
- Evidence with file and line references
- Patch plan
- Validation checklist
