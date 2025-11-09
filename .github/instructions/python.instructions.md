---
applyTo: "**/*.py"
description: "Python coding standards and conventions"
---

# Python Coding Standards

## Code Style Summary
- Prefer explicit, type-safe code that favors readability and consistent tooling feedback.

## Type hints
- Always use type annotations (enforced by mypy + ruff ANN rules)
- Use `TYPE_CHECKING` imports to avoid circular dependencies
- `Resource` from PyVISA typed as `MessageBasedResource`
- Don't cast collections unnecessarily; use correct type (`set`, `list`, `tuple`) directly

### Qt Signal and Slot Typing

**Critical Rule:** Decorators use `object`, function signatures use proper types. **NEVER use `object` in function parameter types.**

```python
# Signal declaration - use object
my_signal = QtCore.pyqtSignal(object)

# Slot: decorator uses object, signature uses proper type
@QtCore.pyqtSlot(object)
def my_slot(self, payload: dict[str, str]) -> None:
    # Trust the type checker - no isinstance() guards needed
    logger.info("Processing: %s", payload)
```

**Prohibited:**
```python
# ❌ WRONG - never use object in function parameters
def my_slot(self, payload: object) -> None:
    if isinstance(payload, dict):  # Don't do this!
        ...

# ❌ WRONG - never use object in regular functions
def process(data: object) -> None:
    ...
```

**Why:**
- `pyqtSignal(object)` and `@QtCore.pyqtSlot(object)` are Qt-specific runtime needs
- Function parameter types are for static type checking
- Using `object` defeats type safety
- Type guards (`isinstance`) in slots indicate wrong types
- Emitter ensures type correctness

## Docstrings

**Primary Rule:** Keep docstrings shorter than the function body.

### When to Add Docstrings
- **Always:** Classes, public methods, functions with non-obvious purpose
- **Abstract methods:** Must explain the contract/purpose (even with just `pass`)
- **Complex operations:** One-line summary of what it does
- **Never:** Module-level docstrings that duplicate class docstrings
- **Never:** Trivial property getters/setters
- **Never:** Methods where name + type hints are self-explanatory

### Content Guidelines
- **Remove obvious information:** Type hints make Args/Returns documentation redundant
- **Focus on *why* or *what*, not *how*:** Code shows implementation details
- **Prefer simple one-liners:** Most methods don't need multi-line explanations
- **Remove redundant words:** "Update the..." → "Update..."
- **For complex logic:** Use inline comments instead of long docstrings
- **Abstract methods with pass:** Docstring explains contract, then just docstring (no `pass`)

### Docstring linting
- DOC201, DOC402, DOC501 are disabled (Returns/Raises not required for brevity)

### Examples

**Before:**
```python
def calculate_average(numbers: list[float]) -> float:
    """Calculate the average of a list of numbers.

    Args:
        numbers: A list of floating point numbers to average

    Returns:
        The arithmetic mean of the input numbers
    """
    return sum(numbers) / len(numbers)
```

**After:**
```python
def calculate_average(numbers: list[float]) -> float:
    """Return arithmetic mean."""
    return sum(numbers) / len(numbers)
```

**Before:**
```python
@QtCore.pyqtSlot()
def on_session_start_request(self) -> None:
    """Initialize a new data acquisition session and set up the persistence layer."""
    ...
```

**After:**
```python
@QtCore.pyqtSlot()
def on_session_start_request(self) -> None:
    """Start new acquisition session."""
    ...
```

**No docstring needed (name + types are clear):**
```python
def set_interval(self, value_ms: int) -> None:
    self._interval_ms = value_ms
```

**Abstract methods (docstring required, no pass):**
```python
@abstractmethod
def can_handle(cls, idn_parts: GpibIdnParts) -> bool:
    """Check if this device class can handle the given IDN response."""
```

**Module-level docstrings (prohibited when duplicating class):**
```python
# ❌ WRONG - duplicates class docstring
"""Dialog for sending commands to devices."""

class DeviceCommandDialog(QtWidgets.QDialog):
    """Dialog for sending commands to devices."""
    ...

# ✅ CORRECT - no module docstring
class DeviceCommandDialog(QtWidgets.QDialog):
    """Dialog for sending commands to devices."""
    ...
```

## Logging conventions
**When to log:**
- **ERROR:** Unexpected failures that prevent operations from completing
- **WARNING:** Recoverable issues (device unavailable, invalid state transitions)
- **INFO:** Significant state changes (acquisition started/stopped, session restored)
- **DEBUG:** Detailed operational info (headers written, cache updates)

**Where to log:**
- **Device layer:** Hardware operations (device init, SCPI commands, VISA errors)
- **Managers:** State transitions (acquisition started, data collected, session closed)
- **Controllers:** User-initiated state changes (start acquisition, set interval)
- **UI layer:** Only exceptional conditions (dialog errors, invalid input)

**Avoid duplicating:**
- Don't log the same event at multiple layers (e.g., "starting acquisition" in both controller and manager)
- Don't log signal emissions ("sent signal X")
- Don't log dialog opens/closes unless they fail
- Don't log cached state updates

## Error handling
- `DeviceBase.error_cool_down_context_manager()` prevents spamming failed devices
- Devices log errors and return last known state during cool-down
- Log exceptions with `logger.exception()`, never bare `except:`

## Naming conventions
- UI signal/slot connections: `on_{widgetName}_{signalName}` pattern
- Use US spelling (`center`, `initialize`, etc.)

## Cleanup
- Remove `# pragma: no cover` (no coverage tools used)
- Remove redundant grouping comments; use blank lines instead
- Do not maintain backward compatibility — update all usages consistently
