---
applyTo: "**/*.py"
description: "Naming conventions for signals, slots, methods, and data structures"
---

# Naming Conventions

## Philosophy
Consistent naming patterns make code predictable and reduce cognitive load when navigating between layers.

## Method Naming Patterns

### Controller → Manager Command Methods
**Pattern:** `request_*` or domain-specific action verbs

Used in `ApplicationController` to expose high-level operations to UI:
```python
def request_restore_session(self, path: Path | None = None) -> None:
def request_export_to_csv(self, export_path: Path, columns: list[str] | None = None) -> None:
def update_description(self, description: str) -> None:
def start_acquisition(self) -> None:
```

**Why:** Clarifies that the controller initiates an action but doesn't perform it directly.

### Manager Slot Methods
**Pattern:** `on_*_request`

Used in `DeviceManager` and `StorageManager` to receive commands:
```python
**Pattern:** `on_{signal_name}`

Used for receiving signals from managers/controllers (not UI widgets):
```python
@QtCore.pyqtSlot()
def on_acquisition_start_request(self) -> None:

@QtCore.pyqtSlot(object)
def on_session_restore_request(self, path: Path | None) -> None:

@QtCore.pyqtSlot(object)
def on_export_request(self, request: tuple[Path, list[str] | None]) -> None:
```
```

**Why:** Slot names clearly indicate they handle incoming signals.

### UI Event Handlers
**Pattern:** `on_{widgetName}_{signalName}`

Auto-wired by PyQt6's UIC loader or manually connected:
```python
def on_actionSelectDevices_triggered(self) -> None:
def on_doActionPushButton_clicked(self) -> None:
def on_commentPlainTextEdit_textChanged(self) -> None:
```

**Why:** Matches Qt's auto-connection convention and makes signal source obvious.

### Private Event Handlers
**Pattern:** `_on_{event_description}`

Used for internal signal handling not triggered by UI widgets:
```python
def _on_description_changed(self, description: str) -> None:
def _on_restore_failed(self, message: str) -> None:
def _on_export_completed(self, path: str) -> None:
```

**Why:** Underscore prefix indicates internal/private method not called directly by UI.

## Signal Naming Patterns

### Manager State Notifications
**Pattern:** `{subject}_{past_tense_verb}`

Emitted from managers to notify of completed state changes:
```python
devices_discovered = QtCore.pyqtSignal(object)
acquisition_state_changed = QtCore.pyqtSignal(object)
columns_changed = QtCore.pyqtSignal(object)
description_changed = QtCore.pyqtSignal(object)
```

**Why:** Past tense indicates the change has already occurred.

### Manager Data Events
**Pattern:** `{action}_{subject}` or descriptive present tense

Emitted when new data is available:
```python
data_initialized = QtCore.pyqtSignal(object)
data_collected = QtCore.pyqtSignal(object)
new_data_row = QtCore.pyqtSignal(object)
```

**Why:** Present/past tense clarifies timing of the event.

### Manager Error Notifications
**Pattern:** `{operation}_failed` or `{operation}_completed`

Result signals for async operations:
```python
restore_failed = QtCore.pyqtSignal(object)
export_completed = QtCore.pyqtSignal(object)
export_failed = QtCore.pyqtSignal(object)
```

**Why:** Explicit success/failure states enable proper error handling in UI.

### Controller Command Signals
**Pattern:** `{target}_{action}_requested`

Emitted from controllers to managers:
```python
device_acquisition_start_requested = QtCore.pyqtSignal()
device_selection_requested = QtCore.pyqtSignal(object)
storage_restore_requested = QtCore.pyqtSignal(object)
storage_export_requested = QtCore.pyqtSignal(object)
```

**Why:** `_requested` suffix emphasizes asynchronous command pattern.

## Variable Naming Patterns

### Cached State
**Pattern:** `_cached_value` or `_is_state`

Used in controllers to maintain lightweight state cache:
```python
self._selected_device_addresses: list[str] = []
self._is_device_running = False
self._discovered_devices: list[DiscoveredDevice] = []
```

**Why:** Underscore prefix indicates internal cache, not public API.

### UI Widget References
**Pattern:** `camelCase` matching `.ui` file names

Loaded from Qt Designer `.ui` files:
```python
self.autoFollowCheckBox: QtWidgets.QCheckBox
self.chartConfigPushButton: QtWidgets.QPushButton
self.commentPlainTextEdit: QtWidgets.QPlainTextEdit
```

**Why:** Matches Qt Designer's automatic naming convention.

### Data Payload Variables
**Pattern:** Descriptive singular/plural nouns

Used in signal handlers and data processing:
```python
data: dict[str, float | str]
columns: list[str]
addresses: list[str]
path: Path | None
```

**Why:** Clear, Pythonic naming without unnecessary prefixes.

## Data Structure Patterns

### Widget Grouping
**Pattern:** `{Domain}Widgets` NamedTuple

Used when passing multiple related widgets to controllers:
```python
class DisplayWidgets(NamedTuple):
    time_label: QtWidgets.QLabel
    number_label: QtWidgets.QLabel
    sample_label: QtWidgets.QLabel
    variables_text: QtWidgets.QTextEdit
    status_layout: QtWidgets.QWidget
```

**Why:** Avoids parameter count limits and groups related concerns.

### Device Metadata
**Pattern:** `{Concept}Info` or descriptive domain objects

Used for device discovery and identification:
```python
@dataclass
class DiscoveredDevice:
    address: str
    display_name: str
    initials: str
```

**Why:** Clear domain modeling without generic names like "DeviceDTO".

## File Naming Patterns

### Controllers
**Pattern:** `{domain}_controller.py`

```
app_controller.py
plot_controller.py
display_controller.py
experiment_controller.py
```

**Why:** Groups all controllers in one directory with consistent naming.

### Managers
**Pattern:** `{domain}_manager.py`

```
device_manager.py
storage_manager.py
```

**Why:** Distinguishes manager pattern from simple utility classes.

### Device Drivers
**Pattern:** `{manufacturer}_{model}.py` or descriptive device type

```
lake_shore_330.py
sr_830_lock_in.py
rigol_dm3058.py
```

**Why:** Matches physical device naming for easy identification.

## Constant Naming

### Intervals and Timeouts
**Pattern:** `{CONTEXT}_MS` or `{CONTEXT}_INTERVAL_MS`

```python
DISCOVERY_INTERVAL_MS = 2000
DEFAULT_ACQUISITION_INTERVAL_MS = 500
SHUTDOWN_TIMEOUT_MS = 500
```

**Why:** Explicit units prevent confusion between seconds and milliseconds.

### Error Messages
**Pattern:** Inline strings or `{CONTEXT}_ERROR_MSG`

Generally prefer inline strings with f-string formatting:
```python
logger.error("Failed to export data to %s", export_path)
QtWidgets.QMessageBox.warning(self, "Export Failed", f"Failed to export data to {path}")
```

Only extract constants for frequently repeated messages:
```python
NO_DEVICES_SELECTED_MSG = "Select at least one device before starting acquisition."
```

**Why:** Keeps messages contextual and avoids over-engineering.

## Anti-Patterns to Avoid

### ❌ Hungarian Notation
```python
# WRONG
strDeviceName = "Multimeter"
lstAddresses = []
```
Use proper type hints instead.

### ❌ Generic Names
```python
# WRONG
def process_data(self, data: object) -> None:
def handle_event(self, event: object) -> None:
```
Be specific about what's being processed or handled.



### ❌ Abbreviations Without Context
```python
# WRONG
def upd_lbl(self, val: float) -> None:
```
Spell out names for clarity:
```python
def update_label(self, value: float) -> None:
```

### ❌ Inconsistent Signal Patterns
```python
# WRONG - mixing past/present/infinitive
data_update = QtCore.pyqtSignal(object)      # present
devices_were_discovered = QtCore.pyqtSignal(object)  # past with "were"
to_export_data = QtCore.pyqtSignal(object)   # infinitive
```
Stick to established patterns per signal type.

## Quick Reference

| Context | Pattern | Example |
|---------|---------|---------|
| Controller public method | `verb_noun` or `request_*` | `start_acquisition()`, `request_export()` |
| Manager slot | `on_*_request` | `on_acquisition_start_request()` |
| UI event handler | `on_{widget}_{signal}` | `on_doActionPushButton_clicked()` |
| State change signal | `{subject}_{past_verb}` | `acquisition_state_changed` |
| Command signal | `{target}_{action}_requested` | `storage_export_requested` |
| Widget container | `{Domain}Widgets` | `DisplayWidgets`, `ChartWidgets` |
| Cached state | `_cached_value` | `_is_device_running`, `_selected_addresses` |
| Constants | `UPPER_SNAKE_CASE` | `DEFAULT_INTERVAL_MS` |
