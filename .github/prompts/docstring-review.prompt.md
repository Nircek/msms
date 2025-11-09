---
mode: agent
description: "Review and improve docstrings for clarity and conciseness"
---

## Task
Systematically review ALL Python files and ensure:
- **All classes have docstrings**
- **All public methods have docstrings** (unless name + types are self-explanatory)
- **All abstract methods have docstrings** (explaining the contract)
- **All functions with non-obvious purpose have docstrings**
- **No module-level docstrings** that duplicate class docstrings
- **All docstrings are shorter than the function body**

## Approach
1. Find ALL Python files in the codebase
2. Check each file systematically (no skipping files)
3. Add missing docstrings where needed
4. Shorten verbose docstrings
5. Remove module-level docstrings that duplicate class docstrings
6. Remove `pass` statements after abstract method docstrings

## Guidelines
Follow ALL docstring rules from `.github/instructions/python.instructions.md`:
- **Primary rule:** Keep docstrings shorter than function body
- **Add docstrings to:** Classes, public methods, abstract methods, non-obvious functions
- **Never add to:** Trivial getters/setters, self-explanatory methods, modules with single class
- **Abstract methods:** Docstring + no `pass` statement
- **Remove obvious info:** Type hints make Args/Returns redundant
- **Focus on *why* or *what*, not *how***
- **Remove redundant words:** "Update the..." → "Update..."

## Examples

**Verbose Args/Returns (Before):**
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

**Concise (After):**
```python
def calculate_average(numbers: list[float]) -> float:
    """Return arithmetic mean."""
    return sum(numbers) / len(numbers)
```

**Abstract method (must have docstring, no pass):**
```python
@abstractmethod
def can_handle(cls, idn_parts: GpibIdnParts) -> bool:
    """Check if this device class can handle the given IDN response."""
```

**Module docstring duplication (prohibited):**
```python
# ❌ WRONG
"""Dialog for sending commands to devices."""

class DeviceCommandDialog(QtWidgets.QDialog):
    """Dialog for sending commands to devices."""
```

**Correct (no module docstring):**
```python
# ✅ CORRECT
class DeviceCommandDialog(QtWidgets.QDialog):
    """Dialog for sending commands to devices."""
```

## Execution Requirements
- **Process ALL Python files** — no selective processing
- **No phrases like "Given the volume, let me focus on..."** — complete all work
- **Update instructions** after completing systematic changes
- Apply changes immediately, don't just list them

## Success Criteria
- All classes have docstrings
- All public methods have appropriate docstrings
- All abstract methods have docstrings (no `pass`)
- No module-level docstrings duplicating class docstrings
- All docstrings shorter than function bodies
- No Args/Returns sections when type hints suffice
