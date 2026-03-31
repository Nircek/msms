---
name: Qt Threading Model
description: QThread worker lifecycle and thread-safe manager communication
scope:
  - msms/ui/controllers/**/*.py
  - msms/ui/managers/**/*.py
applyTo: "msms/ui/{controllers,managers}/**/*.py"
---

# Qt Threading Model

## Worker Lifecycle

1. Instantiate worker `QObject`.
2. Create `QThread`.
3. Move worker with `moveToThread()`.
4. Start thread.
5. Stop via signal-driven shutdown, then `quit()` and `wait()`.

## Communication Rules

- After thread move, manager calls are signal-driven only.
- Keep UI thread free of blocking operations.
- Avoid shared mutable state; prefer signal payload transfer.

## Shutdown Discipline

- Use bounded waits during shutdown.
- Ensure timers and periodic jobs are stopped before worker teardown.
