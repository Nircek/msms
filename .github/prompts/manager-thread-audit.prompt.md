---
mode: ask
description: "Audit controller/manager threading interactions for signal compliance"
---
Run this prompt when reviewing PyQt controller or manager changes.

1. Briefly restate the purpose of the modified classes.
2. Cross-check the code against:
   - [../instructions/threading.instructions.md](../instructions/threading.instructions.md) - Threading rules and manager pattern
   - [../instructions/controllers.instructions.md](../instructions/controllers.instructions.md) - Controller responsibilities
   - [../instructions/signal-flow.instructions.md](../instructions/signal-flow.instructions.md) - Signal catalog and communication patterns
   - [../instructions/naming.instructions.md](../instructions/naming.instructions.md) - Naming conventions
   - [../instructions/python.instructions.md](../instructions/python.instructions.md) - Type hints and coding standards
3. Report findings sorted by severity with `file:line` references. Pay special attention to:
   - Direct method calls on managers after `moveToThread`
   - Missing Qt signals/slots for data or command flow
   - Shared state mutated from multiple threads without signals
   - Blocking operations on the UI thread
   - Incorrect signal/slot naming patterns
   - Controllers performing manager responsibilities
4. Note any missing unit or integration coverage and suggest concrete tests (e.g., Qt signal spy cases).
5. Conclude with recommended remediation steps or open questions.
