---
name: UI Controller Responsibilities
description: MainWindow decomposition rules and controller responsibility boundaries
scope:
  - msms/ui/controllers/**/*.py
applyTo: "msms/ui/controllers/**/*.py"
---

# Controller Responsibilities

## Primary Goal

- Keep `MainWindow` orchestration-focused by delegating domain-specific logic to controllers.

## ApplicationController

- Own manager lifecycle and signal wiring.
- Connect component-owned signals to manager slots.
- Cache minimal manager state required for synchronous UI reads.

## UI Controllers

- Own one UI domain each, such as plotting, display formatting, or automation rendering.
- Operate in UI thread context.
- Do not perform hardware I/O, persistence, or long-running operations.

## Anti-Patterns

- No direct manager method calls from UI after `moveToThread()`.
- No cross-controller tight coupling.
- No business logic that belongs to managers or connectivity.
