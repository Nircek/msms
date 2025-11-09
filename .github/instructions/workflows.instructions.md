---
applyTo: "**/*"
description: "Development workflows and commands"
---

# Development Workflows

## Philosophy
- Document repeatable commands so contributors can reproduce behavior without guesswork.

## Running the application
- CLI mode: `poetry run msms`
- UI mode: `poetry run ui` or `poetry run python -m msms`
- Simulation mode: `MSMS_SIM=y poetry run ui` (uses `msms/connectivity/sim_instruments.yml`)

## Testing
- Smoke test: `poetry run test` (discovers simulated devices → starts acquisition → exports CSV)
- Code quality: `poetry run pre-commit run --all-files` (ruff format + lint, mypy, toml-sort)
- Run `poetry run pre-commit run --all-files` before committing instruction or UI-threading changes to catch pending type issues early
- After threading or signal wiring changes, re-run the smoke test to confirm restore/export flows still work end-to-end

## Adding features

### New device
1. Create `msms/connectivity/devices/my_device.py`
2. Inherit `DeviceBase`, implement `can_handle()`, `initialize()`, `update()`
3. Add `@register_device()` decorator
4. Import in `msms/connectivity/devices/__init__.py` for auto-registration
5. Add simulated responses to `sim_instruments.yml` for testing

### New UI elements
1. Edit `msms/ui/main_window.ui` in Qt Designer
2. Add signal handler: `def on_{widget}_{signal}(self) -> None:`
3. Call `self.fix_slot_signal()` in constructor if UIC auto-wiring conflicts
