# MSMS Copilot North Star

MSMS controls GPIB/SCPI instruments for AC magnetic susceptibility measurements using a PyQt6 UI, threaded acquisition, and CSV persistence.

## Immutable Project Truths

- Preserve strict three-tier boundaries:
  - UI layer in `msms/ui/`
  - Controller and manager layer in `msms/ui/controllers/` and `msms/ui/managers/`
  - Device layer in `msms/connectivity/`
- Only the `msms/connectivity/` layer talks to VISA or PyVISA.
- Once a manager is moved to a `QThread`, cross-thread interaction must happen through Qt signals and slots only.
- Device readings are contractually either:
  - `float` for valid numeric values
  - `str` for warning or error states (not plotted as numeric series)
- Keep type annotations complete and explicit in Python code.
- Apply non-backward-compatible updates consistently across all usages when behavior changes.

## Operational Discipline

- Prefer deterministic, reproducible workflows.
- Run `poetry run pre-commit run --all-files` before finalizing broad refactors.
- Re-run `poetry run test` after signal wiring, threading, or device integration changes.

Detailed conventions live in scoped instruction files under `.github/instructions/`.
