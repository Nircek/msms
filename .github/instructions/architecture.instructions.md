```instructions
---
applyTo: "**/*.py"
description: "MSMS three-tier architecture overview and layer boundaries"
---

# Architecture Overview

## Philosophy
Preserve strict layer boundaries and let data flow through well-defined signals and repositories. Controllers decompose MainWindow complexity by delegating domain responsibilities.

## Three-Tier Design

### 1. UI Layer (`msms/ui/`)
**Purpose:** Render widgets, handle user input, display data.

**Key components:**
- `MainWindow`: Top-level window that orchestrates controllers and connects signals
- **UI Controllers** (`ui/controllers/`):
  - `PlotController`: Chart rendering, auto-follow, theme adaptation
  - `DisplayController`: Status labels, data formatting
  - `ExperimentController`: Action menus, dialogs, interval selection
- **Dialogs** (`ui/dialogs/`): Device selection, description editing, command sending

**Communication:**
- UI → Controller: Direct method calls (same thread)
- UI → Manager: Never direct; always through `ApplicationController` signals

### 2. Controller/Manager Layer

#### Application Controller (`ui/controllers/app_controller.py`)
**Purpose:** Coordinate manager lifecycle and route commands between UI and worker threads.

**Responsibilities:**
- Own `DeviceManager` and `StorageManager` instances
- Manage QThread lifecycle (start, stop, cleanup)
- Define command signals for cross-thread communication
- Cache manager state for synchronous UI queries
- Forward UI requests as signals to managers

**Key pattern:** Synchronous API for UI, asynchronous execution in managers.

#### Managers (`ui/managers/`)
**Purpose:** Perform blocking I/O and data processing in separate threads.

- **DeviceManager**: VISA device discovery, periodic polling, initialization
- **StorageManager**: CSV persistence, in-memory data repository, session restore

**Communication:**
- Receive commands via Qt signal/slot connections
- Emit state changes and data updates as signals
- Never called directly after `moveToThread()`

### 3. Device Layer (`msms/connectivity/`)
**Purpose:** Abstract VISA hardware communication behind consistent interfaces.

**Key components:**
- `DeviceRepository`: VISA library initialization, device discovery
- **Device Drivers** (`connectivity/devices/`): Hardware-specific SCPI/GPIB commands
- `DeviceBase`: Abstract base class for driver registration

**Abstraction boundary:** Only `connectivity` module interacts with PyVISA/VISA.

## Data Flow Summary

### Acquisition Flow
```
[Timer] → DeviceManager.poll()
  → data_collected signal
  → StorageManager.append()
  → new_data_row signal
  → MainWindow updates UI + plot
```

### Command Flow
```
[User Action] → MainWindow method
  → ApplicationController.request_*()
  → *_requested signal
  → Manager executes in worker thread
  → *_completed signal
  → MainWindow shows result dialog
```

## Layer Boundaries

### ✅ Allowed
- UI → ApplicationController (direct calls, same thread)
- ApplicationController → Manager (signals only, cross-thread)
- Manager → UI (signals only, cross-thread)
- Device layer → PyVISA (exclusive access)

### ❌ Prohibited
- UI → Manager direct calls (violates thread safety)
- Manager → `DeviceRepository` bypass (must use device drivers)
- Non-device code → PyVISA (breaks abstraction)

```
