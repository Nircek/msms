---
name: Python Standards
description: Python typing, docstring, logging, and error-handling conventions
scope:
  - msms/**/*.py
applyTo: "msms/**/*.py"
---

# Python Standards

## Typing

- Require type annotations for functions, methods, and class attributes.
- Prefer concrete types over generic `object` in normal Python signatures.
- For Qt signal compatibility, use `pyqtSignal(object)` and matching slot decorators where needed.

## Docstrings

- Keep docstrings shorter than the implementation body.
- Prioritize classes, public methods, abstract methods, and non-obvious functions.
- Avoid Args and Returns sections when type hints already provide the same information.

## Logging and Errors

- Use structured logging with appropriate levels.
- Log exceptions with `logger.exception(...)` in exception handlers.
- Avoid bare `except:` blocks.
- Keep recoverable device failures non-fatal and preserve last known valid state where applicable.

## General Rules

- Use US spelling.
- Remove dead comments and redundant grouping comments.
- Do not add backward-compatibility shims unless explicitly requested.
