---
applyTo: "msms/ui/controllers/**/*.py"
description: "Controller design philosophy and responsibility boundaries"
---

# Controller Design Philosophy

## Purpose
Controllers exist to **decompose MainWindow complexity** by delegating domain-specific responsibilities to focused, single-purpose classes. Without controllers, MainWindow would become a monolithic file managing device selection, plot rendering, data display, experiment actions, and thread coordination all in one place.

## Benefits of Controller Pattern
1. **Separation of Concerns:** Each controller owns one logical domain (plotting, display, experiments, application coordination)
2. **Testability:** Isolated controllers can be tested independently of the full UI
3. **Maintainability:** Changes to plot logic don't require touching device management code
4. **Reusability:** Controllers can be reused across different UI layouts or dialogs
5. **Code Organization:** Related functionality stays grouped in one file instead of scattered across MainWindow methods

## Controller Types

### Application Controller (`ApplicationController`)
**Responsibility:** Coordinate manager lifecycle and route commands between UI and worker threads.

**Key characteristics:**
- Owns `DeviceManager` and `StorageManager` instances
- Manages QThread lifecycle (start, stop, cleanup)
- Defines signals for cross-thread communication
- Provides synchronous API for UI layer via cached state
- Never performs I/O or heavy computation directly

**Usage pattern:**
```python
# MainWindow owns one instance
self.app_controller = ApplicationController(interval_ms=500)

# MainWindow calls controller methods directly (same thread)
self.app_controller.start_acquisition()
self.app_controller.request_export_to_csv(path)

# Controller emits signals to managers (cross-thread)
self.storage_export_requested.emit((export_path, columns))
```

### UI Controllers (Plot, Display, Experiment)
**Responsibility:** Manage a specific UI subsystem without knowing about threads or managers.

**Key characteristics:**
- Accept widget references in constructor (often via `NamedTuple` for clarity)
- Provide high-level operations that manipulate widget state
- May cache display state internally (e.g., current plot range)
- Operate entirely on the UI thread
- Never directly interact with managers or device layer

**Usage pattern:**
```python
# MainWindow instantiates with widget references
self.plot_controller = PlotController(self.plotWidget, self.autoFollowCheckBox)

# MainWindow delegates UI logic to controller
self.plot_controller.set_column("temperature")
self.plot_controller.refresh_from_repository(data_repository)
```

## Responsibility Boundaries

### What Belongs in Controllers
- **Application Controller:**
  - Thread lifecycle management
  - Signal routing between layers
  - Caching manager state for synchronous UI queries
  - Command validation before forwarding to managers

- **UI Controllers:**
  - Widget state management (enable/disable, visibility)
  - Data formatting for display (units, precision, labels)
  - User interaction handling (menus, dialogs)
  - Plot rendering and auto-follow logic

### What Does NOT Belong in Controllers
- **Device communication:** Belongs in `DeviceManager` and device drivers
- **CSV persistence:** Belongs in `StorageManager` and `CsvPersistence`
- **Data transformation:** Belongs in `StorageManager` and `DataRepository`
- **Business logic spanning multiple domains:** Either split into multiple controllers or keep in MainWindow as orchestration

## Communication Patterns

### UI → Controller
**Pattern:** Direct method calls (same thread)
```python
# MainWindow calls controller directly
self.app_controller.start_acquisition()
self.plot_controller.set_column("temperature")
self.experiment_controller.export_data_to_csv()
```

### Controller → Manager
**Pattern:** Qt signals only (cross-thread)
```python
# ApplicationController emits signals
self.device_acquisition_start_requested.emit()
self.storage_export_requested.emit((path, columns))
```

### Manager → Controller → UI
**Pattern:** Qt signals with optional caching
```python
# Manager emits state change
self.acquisition_state_changed.emit(is_running)

# ApplicationController caches for synchronous access
@QtCore.pyqtSlot(object)
def _on_acquisition_state_changed(self, running: bool) -> None:
    self._is_device_running = running

# UI queries cached state
if self.app_controller.is_acquiring:
    # Update button text
```

## Anti-Patterns to Avoid

### ❌ Direct Manager Calls from UI Thread
```python
# WRONG: Calling manager method directly after moveToThread()
devices = self.app_controller.device_manager.discover_devices()
```
**Fix:** Emit signal and use cached result or callback slot.

### ❌ Business Logic in MainWindow
```python
# WRONG: Temperature conversion logic in MainWindow
def on_update_data_labels(self, data: dict) -> None:
    kelvin = data.get("sample", 0)
    celsius = kelvin - 273.15
    self.sampleValue.setText(f"{celsius:.2f}°C")
```
**Fix:** Move formatting to `DisplayController`.

### ❌ Controllers Knowing About Each Other
```python
# WRONG: PlotController importing ExperimentController
from msms.ui.controllers.experiment_controller import ExperimentController

class PlotController:
    def export_plot_data(self) -> None:
        self.experiment_controller.export_data_to_csv()
```
**Fix:** Both controllers should coordinate through MainWindow or ApplicationController.

### ❌ Widget References Spread Across Methods
```python
# WRONG: Passing widgets individually
def __init__(self, label1, label2, label3, text1, text2, button1) -> None:
```
**Fix:** Group related widgets in a `NamedTuple`.

## Best Practices

1. **Single Responsibility:** Each controller manages one cohesive domain
2. **Dependency Injection:** Pass widgets and managers to constructor, don't import globally
3. **Type Safety:** Use proper type hints for all method signatures
4. **Logging:** Log high-level operations (start acquisition, export data) not low-level widget updates
5. **Error Handling:** Handle UI-level errors in controllers (show dialogs), let managers handle I/O errors
6. **Immutability:** Controllers should not modify data structures passed from managers (read-only access)

## Adding a New Controller

When MainWindow gains a new complex UI section:

1. Create `msms/ui/controllers/{domain}_controller.py`
2. Define widget container using `NamedTuple` (see `naming.instructions.md`)
3. Implement controller with focused, single-responsibility methods
4. Wire in MainWindow constructor
5. Connect signals from managers/controllers
