# MSMS - Magnetic Susceptibility Measurement Station

## Project Overview

Physics lab software controlling GPIB/SCPI instruments for AC magnetic susceptibility measurements. PyQt6 UI + threaded device acquisition + CSV persistence. Supports Lake Shore 330, SR-830 Lock-In, and RSDM3055A multimeter.

## Architecture

**Three-tier design:**
- **UI Layer** (`msms/ui/`): PyQt6 main window + dialogs. `MainWindow` orchestrates UI components.
- **Controller/Manager Layer** (`msms/ui/controllers/`, `msms/ui/managers/`): `ApplicationController` coordinates `DeviceManager` (threaded polling) and `StorageManager` (CSV + in-memory repository). Both run in separate QThreads.
- **Device Layer** (`msms/connectivity/`): `DeviceRepository` discovers/manages VISA devices via PyVISA. Device drivers inherit from `DeviceBase` and register via `@register_device` decorator.

**Key data flow:**
1. `DeviceManager` polls devices on QTimer → emits `data_collected` signal
2. `StorageManager` receives data → updates in-memory repository + writes CSV
3. `MainWindow` receives `new_data_row` signal → updates UI labels + plots

## Device Driver Pattern

All devices in `msms/connectivity/devices/` follow this pattern:

```python
@register_device(initials="XX", short_display_name="Device Name")
class MyDevice(DeviceBase):
    @classmethod
    def can_handle(cls, idn_parts: GpibIdnParts) -> bool:
        # Match against *IDN? response tuple (vendor, model, serial, version)
        pass

    def initialize(self) -> None:
        # Device setup commands (called once after connection)
        pass

    def update(self) -> dict[str, str]:
        # Return latest readings (called periodically)
        return {"column_name": self.query_resource("SCPI?")}
```

**CRITICAL:** Device discovery auto-detects via `*IDN?` matching. New devices are auto-registered when imported.

## Development Workflows

**Run CLI mode (console only):**
```bash
poetry run msms
```

**Run UI mode:**
```bash
poetry run ui
# or: poetry run python -m msms
```

**Simulation mode (no hardware):**
```bash
MSMS_SIM=y poetry run ui
```
Simulated devices defined in `msms/connectivity/sim_instruments.yml` (PyVISA-sim format).

**Run smoke test:**
```bash
poetry run test
```
Automated UI test that discovers simulated devices → starts acquisition → exports CSV.

**Code quality:**
```bash
poetry run pre-commit run --all-files  # ruff format + lint, mypy, toml-sort
```

## Project Conventions

**Naming:**
- Device initials (`MM`, `LS`, `LI`) used for console logging prefixes
- UI signal/slot connections use `on_{widgetName}_{signalName}` pattern
- Thread-safe operations via Qt signals, never direct cross-thread calls

**File organization:**
- `msms/connectivity/devices/*.py` - one file per device type
- `msms/ui/*.ui` - Qt Designer files loaded with `uic.loadUi()`
- `logs/` - rotating logs + CSV exports (timestamped with UTC)

**Type hints:**
- Always use type annotations (enforced by mypy + ruff ANN rules)
- `TYPE_CHECKING` imports to avoid circular dependencies
- `Resource` from PyVISA typed as `MessageBasedResource`

**Error handling:**
- `DeviceBase.error_cool_down_context_manager()` prevents spamming failed devices
- Devices log errors and return last known state during cool-down period
- Exceptions logged with `logger.exception()`, never bare `except:`

## Key Integration Points

**VISA library selection** (`msms/connectivity/visa.py`):
- Default: system VISA (`""`)
- Simulation: `MSMS_SIM=y` → loads `sim_instruments.yml@sim`

**Logging setup** (`msms/logging_config.py`):
- Call `setup_logging()` before any device operations
- Logs to console + rotating file in `logs/msms_{timestamp}.log`

**Thread lifecycle:**
- `ApplicationController` manages QThread lifecycle for managers
- Always use `moveToThread()` before starting threads
- Signal emissions cross thread boundaries safely

## Quick Start for New Features

**Adding a new device:**
1. Create `msms/connectivity/devices/my_device.py`
2. Inherit `DeviceBase`, implement `can_handle()`, `initialize()`, `update()`
3. Add `@register_device()` decorator
4. Import in `msms/connectivity/devices/__init__.py` for auto-registration

**Adding UI elements:**
1. Edit `msms/ui/main_window.ui` in Qt Designer
2. Add signal handler in `MainWindow`: `def on_{widget}_{signal}(self) -> None:`
3. Call `self.fix_slot_signal()` in constructor if UIC auto-wiring conflicts

**Testing device code:**
1. Add simulated responses to `sim_instruments.yml`
2. Run with `MSMS_SIM=y` environment variable
3. Or extend `msms/tests/smoke.py` for automated validation


## General Coding Rules

- **Docstrings:** Keep them shorter than the function body.

- **Abstraction:**

    - Only the `connectivity` module can interact with VISA.

    - Device-specific logic belongs exclusively in that device’s file under `connectivity/devices/`.

- **DeviceRepository contract:**

    - Responsibilities:

        1. Initialize the library.

        2. Discover and select devices.

        3. Set up devices.

        4. Query devices for readings.

    - Each reading returns either:

        - `float` → valid numeric result

        - `str` → error or warning message (still logged, but never shown on plots)

- **Type handling:** Don’t cast collections unnecessarily. Functions should accept and return the correct type (`set`, `list`, or `tuple`) directly.

- **Comments:** Remove redundant grouping comments. Use blank lines for readability instead.

- **No legacy pragmas:**

    - Remove `# pragma: no cover` (no coverage tools used).

- **Language:** Use US spelling (`center`, `initialize`, etc.).

- **Compatibility:** Do not maintain backward compatibility — update all usages consistently.


---

## Application Structure

### Entry Points

- `msms/__main__.py`:

    - `ui()` → PyQt6 GUI launcher

    - `main()` → legacy CLI loop


### GUI Layout

- Main window: `msms/ui/main_window.py` (Qt Designer `.ui` file)

- Controllers: `msms/ui/controllers/`

- Managers: `msms/ui/managers/`

- Dialogs: `msms/ui/dialogs/`


### Connectivity Layer

- Central access point: `msms/connectivity/device_repository.py`

- Device drivers: `msms/connectivity/devices/`

- Each driver registers via a `DeviceBase` subclass.


---

## Threading & Manager Design

- **Manager**:

    - A `QObject` subclass running in its own thread.

    - Performs tasks on request or processes new incoming data.

- **Setup:**

    1. Instantiate the worker (`Manager` subclass).

    2. Create a `QThread`.

    3. Move the worker to that thread.

    4. Communicate only via **signal-slot** connections.

- **Rules:**

    - Never call manager methods directly from the UI thread.

    - Controllers must use signals and slots for all interactions once the object has moved to another thread.


---

## Tooling

Activate formatting, linting, and type checks using:

```bash
git add . && pre-commit run --all-files
```

Pre-commit hooks include:

- **ruff** — formatting
- **linting** — code style and structure
- **mypy** — static type checking

## Type Annotation Conventions

### Qt Signal/Slot Types
- **Signal definitions:** Use `QtCore.pyqtSignal(object)` for flexibility
- **Slot decorators:** Use `@QtCore.pyqtSlot(object)` to match signal payloads
- **Method signatures (non-slots):** Use proper Python types (`Path`, `list[str]`, etc.)
- **Slot parameters:** Accept `object` then use type guards (`isinstance`)
- **Never use `object` in regular Python type annotations** — only in Qt signal/slot contexts

See `.github/instructions/signal-flow.instructions.md` for complete signal catalog and detailed flow examples.
