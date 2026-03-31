---
name: Naming Conventions
description: Naming rules for signals, slots, handlers, and data objects
scope:
  - msms/**/*.py
applyTo: "msms/**/*.py"
---

# Naming Conventions

## Slots and Handlers

- UI widget handlers use `on_{widgetName}_{signalName}`.
- Manager command slots use `on_*_request`.
- Internal private handlers use `_on_{event}`.

## Signals

- Command signals use `{target}_{action}_requested`.
- State completion signals use `{subject}_{state_changed_or_past_tense}`.
- Error and result signals use `{operation}_failed` and `{operation}_completed`.

## Files and Types

- Controllers: `{domain}_controller.py`.
- Managers: `{domain}_manager.py`.
- Device drivers: hardware-identifiable names.
- Group related widgets in domain-focused containers such as `NamedTuple` structures.
