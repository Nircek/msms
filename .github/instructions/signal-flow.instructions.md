---
applyTo: "msms/ui/**/*.py"
description: "Qt signal/slot communication patterns and data flow"
---

# Signal Flow and Command Patterns

## Philosophy
Signal-slot connections establish unidirectional data flow across thread boundaries, ensuring thread-safe communication without direct method calls between threads.

## Layer Communication Pattern

### UI → Controller → Manager
Commands flow downward through signals:
1. **UI Layer** emits user actions
2. **Controller** transforms and routes signals
3. **Manager** executes in worker thread

### Manager → Controller → UI
Data flows upward through signals:
1. **Manager** emits state changes or data
2. **Controller** optionally transforms/caches
3. **UI** updates display

## Critical Rules
- Never call manager methods directly from UI thread after `moveToThread()`
- Decorators use `object`, function signatures use proper types (see `python.instructions.md`)
- No type guards in slots — trust the type checker

## Signal Catalog

### ApplicationController Signals (Outgoing to Managers)

#### Device Management
```python
device_acquisition_start_requested = QtCore.pyqtSignal()
# Payload: None
# Destination: DeviceManager.on_acquisition_start_request()
# Triggers: Device polling initialization and timer start

device_acquisition_stop_requested = QtCore.pyqtSignal()
# Payload: None
# Destination: DeviceManager.on_acquisition_stop_request()
# Triggers: Timer stop, device shutdown, VISA cleanup

device_selection_requested = QtCore.pyqtSignal(object)
# Payload: list[str] (VISA addresses)
# Destination: DeviceManager.on_device_select_request(addresses)
# Triggers: Update selected device set for next acquisition cycle

device_discovery_start_requested = QtCore.pyqtSignal(object)
# Payload: int (milliseconds) - discovery interval
# Destination: DeviceManager.on_discovery_start_request(interval_ms)
# Triggers: Start periodic VISA device scan, emits devices_discovered

device_discovery_stop_requested = QtCore.pyqtSignal()
# Payload: None
# Destination: DeviceManager.on_discovery_stop_request()
# Triggers: Stop discovery timer

device_interval_change_requested = QtCore.pyqtSignal(object)
# Payload: int (milliseconds)
# Destination: DeviceManager.on_interval_change_request(interval_ms)
# Triggers: Update QTimer interval if acquisition running

device_shutdown_requested = QtCore.pyqtSignal()
# Payload: None
# Destination: DeviceManager.on_shutdown()
# Triggers: Clean shutdown of device connections and timer
```

#### Storage Management
```python
storage_restore_requested = QtCore.pyqtSignal(object)
# Payload: Path | None (CSV file path or None for last file)
# Destination: StorageManager.on_session_restore_request(path)
# Triggers: Load historic session, emit restore_failed or new state signals

storage_export_requested = QtCore.pyqtSignal(object)
# Payload: tuple[Path, list[str] | None] (export path, optional column filter)
# Destination: StorageManager.on_export_request(request)
# Triggers: Write CSV snapshot, emit export_completed or export_failed

storage_description_change_requested = QtCore.pyqtSignal(object)
# Payload: str (experiment description)
# Destination: StorageManager.on_description_change_request(description)
# Triggers: Update persistent description, emit description_changed

storage_stop_requested = QtCore.pyqtSignal()
# Payload: None
# Destination: StorageManager.on_stop_request()
# Triggers: Close CSV persistence session

storage_session_start_requested = QtCore.pyqtSignal()
# Payload: None
# Destination: StorageManager.on_session_start_request()
# Triggers: Initialize new CSV file and data repository
```

### DeviceManager Signals (Outgoing from Manager)

```python
data_initialized = QtCore.pyqtSignal(object)
# Payload: dict[str, str] (initial device readings with column names)
# Destination: StorageManager.on_header_set_request(initial_data)
# Triggers: Configure CSV header, initialize data repository

data_collected = QtCore.pyqtSignal(object)
# Payload: dict[str, str] (device readings for one time point)
# Destination: StorageManager.on_data_append_request(data)
# Triggers: Transform data, append to repository, write CSV row

devices_discovered = QtCore.pyqtSignal(object)
# Payload: list[DiscoveredDevice]
# Destination: ApplicationController._on_devices_discovered(devices)
# Triggers: Cache discovered devices for UI selection

device_info_collected = QtCore.pyqtSignal(object)
# Payload: dict[str, str] (device metadata and status)
# Destination: UI or dialogs for device status display
# Triggers: Update device information panels

acquisition_state_changed = QtCore.pyqtSignal(object)
# Payload: bool (True = running, False = stopped)
# Destination: ApplicationController._on_acquisition_state_changed(running)
# Triggers: Update controller acquisition state cache
```

### StorageManager Signals (Outgoing from Manager)

```python
new_data_row = QtCore.pyqtSignal(object)
# Payload: dict[str, str | float] (transformed data row)
# Destination: MainWindow.on_update_data_labels(data)
# Triggers: Update UI labels, refresh plots

columns_changed = QtCore.pyqtSignal(object)
# Payload: list[str] (numeric column names)
# Destination: MainWindow.on_columns_change(columns)
# Triggers: Update chart configuration options

description_changed = QtCore.pyqtSignal(object)
# Payload: str (experiment description)
# Destination: MainWindow._on_description_changed(description)
# Triggers: Update UI comment text field (with signal blocking)

restore_failed = QtCore.pyqtSignal(object)
# Payload: str (error message)
# Destination: MainWindow._on_restore_failed(message)
# Triggers: Show error dialog

export_completed = QtCore.pyqtSignal(object)
# Payload: str (file path)
# Destination: MainWindow._on_export_completed(path)
# Triggers: Show success dialog

export_failed = QtCore.pyqtSignal(object)
# Payload: str (error message)
# Destination: MainWindow._on_export_failed(message)
# Triggers: Show error dialog
```

## Command Flow Examples

### Starting Acquisition
```
[MainWindow._start_device_manager]
  ↓ (direct call)
[ApplicationController.start_acquisition]
  ↓ device_interval_change_requested (int)
[DeviceManager.on_interval_changed]
  ↓ storage_stop_requested ()
[StorageManager.stop]
  ↓ storage_session_start_requested ()
[StorageManager.setup]
  ↓ device_selection_changed (list[str])
[DeviceManager.set_selected_addresses]
  ↓ device_start_requested ()
[DeviceManager.start_acquisition]
  ↓ data_initialized (dict[str, str])
[StorageManager.set_header]
  ↓ columns_changed (list[str])
[MainWindow.on_columns_change]
```

### Periodic Data Collection
```
[QTimer.timeout]
  ↓ (internal slot)
[DeviceManager._poll_devices]
  ↓ data_collected (dict[str, str])
[StorageManager.on_data_append]
  ↓ new_data_row (dict[str, str | float])
[MainWindow.on_update_data_labels]
  + MainWindow.refresh_plot
```

### Restoring Session
```
[MainWindow.on_actionRestoreLastFile_triggered]
  ↓ (direct call)
[ApplicationController.request_restore_session]
  ↓ storage_restore_requested (Path | None)
[StorageManager.restore_session]
  ↓ new_data_row (dict[str, str | float])
[MainWindow.on_update_data_labels]
  ↓ columns_changed (list[str])
[MainWindow.on_columns_change]
  ↓ description_changed (str)
[MainWindow._on_description_changed]
```

### Exporting Data
```
[MainWindow._export_data_to_csv]
  ↓ (direct call)
[ApplicationController.request_export_to_csv]
  ↓ storage_export_requested (tuple[Path, list[str] | None])
[StorageManager.export_to_csv]
  ↓ export_completed (str)
    OR export_failed (str)
[MainWindow._on_export_completed/_on_export_failed]
```

### Device Discovery
```
[MainWindow opens DeviceSelectionDialog]
  ↓ device_discovery_start_requested (int)
[DeviceManager periodic scan]
  ↓ devices_discovered (list[DiscoveredDevice])
[Dialog populates device list]
```

## Type Annotation Examples

See `python.instructions.md` for detailed typing rules. Key patterns:

```python
# Signal with payload
my_signal = QtCore.pyqtSignal(object)

# Slot unpacking tuple
@QtCore.pyqtSlot(object)
def on_request(self, request: tuple[Path, list[str] | None]) -> None:
    export_path, columns = request
    # Type checker validates unpacking

# Cached return values
def discover_devices(self) -> list[DiscoveredDevice]:
    self.device_discovery_requested.emit()
    return list(self._discovered_devices)  # cached from slot
```

## Common Patterns

### Bidirectional Updates (e.g., Description)
When UI and storage must stay synchronized:
1. User types → `on_commentPlainTextEdit_textChanged`
2. Controller forwards → `storage_description_requested.emit(text)`
3. Storage persists → `description_changed.emit(text)`
4. UI updates (with `blockSignals(True)`) to avoid feedback loop

### Error Reporting
Managers emit failure signals instead of raising exceptions:
```python
try:
    self.csv_persistence.export_to_csv(export_path, columns)
except Exception:
    logger.exception("Failed to export data to %s", export_path)
    self.export_failed.emit(f"Failed to export data to {export_path}")
    return
self.export_completed.emit(str(export_path))
```

### Cached State in Controller
Controller maintains lightweight caches for synchronous UI needs:
```python
self._discovered_devices: list[DiscoveredDevice] = []
self._is_device_running = False
```
Updated via slots, read via properties/methods.

## Debugging Tips

1. **Signal not received?** Check `connect()` happened after `moveToThread()`
2. **Wrong thread?** Use `QtCore.QThread.currentThread()` logging
3. **Type mismatch?** Add `isinstance()` guards in slots
4. **Feedback loop?** Use `blockSignals()` before programmatic widget updates
5. **Stale cache?** Ensure slots update cached state before returning
