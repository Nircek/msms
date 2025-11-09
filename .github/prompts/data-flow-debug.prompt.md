---
mode: ask
description: "Diagnose data flow or signal propagation issues"
---
Use this prompt to troubleshoot when UI values are stale or device readings are not reaching storage.

1. Describe the observed symptom and latest logs.
2. Inspect the relevant tiers using:
   - [../instructions/architecture.instructions.md](../instructions/architecture.instructions.md) - Layer boundaries and data flow overview
   - [../instructions/signal-flow.instructions.md](../instructions/signal-flow.instructions.md) - Complete signal catalog and flow examples
   - [../instructions/controllers.instructions.md](../instructions/controllers.instructions.md) - Controller communication patterns
3. Trace signals through the flow examples: `DeviceManager` → `ApplicationController` → `StorageManager` → `MainWindow`. Identify where emissions stop or payloads mutate incorrectly.
4. Check naming conventions in [../instructions/naming.instructions.md](../instructions/naming.instructions.md) to verify correct signal/slot connections.
5. Recommend logging or Qt signal spy instrumentation to confirm hypotheses.
6. Outline concrete fixes, distinguishing quick patches from structural refactors.
