---
applyTo: "msms/ui/{controllers,managers}/**/*.py"
description: "Qt threading model and Manager pattern"
---

# Threading & Manager Design

## Philosophy
- Let threads communicate only via Qt signals so shared state stays serialized and debuggable.

## Manager pattern
- A `QObject` subclass running in its own thread
- Performs tasks on request or processes new incoming data

## Setup pattern
1. Instantiate the worker (`Manager` subclass)
2. Create a `QThread`
3. Move the worker to that thread: `worker.moveToThread(thread)`
4. Communicate only via **signal-slot** connections

## Critical rules
- Never call manager methods directly from the UI thread after `moveToThread()`
- Controllers must use signals and slots for all cross-thread interactions
- Use `@QtCore.pyqtSlot(object)` for slots accepting Qt signal payloads
- Use proper Python types (not `object`) in method signatures for non-slot parameters
- ApplicationController can cache manager state via slots for synchronous UI queries
- Examples:
  - ❌ `self.storage_manager.export_to_csv(path)` - direct call after moveToThread
  - ✅ `self.storage_export_requested.emit((path, columns))` - signal emission
  - ❌ `return self.device_manager.discover_devices()` - direct return from worker thread
  - ✅ Cache discovery results in controller slot, return cached list

## Thread Safety Rules
- All manager methods called via signals (not direct calls)
- No shared mutable state without QMutex protection
- Manager lifecycle: `moveToThread()` → `thread.start()` → `thread.quit()` → `thread.wait()`
- Cleanup uses short timeouts (500ms) to avoid hanging application shutdown

See `python.instructions.md` for Qt type annotation rules and `signal-flow.instructions.md` for complete signal catalog.
