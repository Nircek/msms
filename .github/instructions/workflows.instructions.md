---
name: Development Workflows
description: Canonical run, test, and quality commands for MSMS
scope:
  - "**/*"
applyTo: "**/*"
---

# Development Workflows

## Run Modes

- CLI: `poetry run msms`
- UI: `poetry run ui` or `poetry run python -m msms`
- Simulation: `MSMS_SIM=y poetry run ui`

## Validation

- Smoke flow: `poetry run test`
- Quality checks: `poetry run pre-commit run --all-files`

## Change-Sensitive Retests

- Re-run smoke flow after threading, signal wiring, or storage restore/export changes.
