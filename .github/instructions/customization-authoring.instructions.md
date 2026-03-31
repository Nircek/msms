---
name: Customization Authoring Rules
description: Standards for maintaining instructions and agents in this repository
scope:
  - .github/copilot-instructions.md
  - .github/instructions/**/*.md
  - .github/agents/**/*.md
applyTo: ".github/{copilot-instructions.md,instructions/**/*.md,agents/**/*.md}"
---

# Customization Authoring

## Structure Rules

- Keep global guidance in `.github/copilot-instructions.md` limited to immutable project truths.
- Put file-targeted guidance in `.github/instructions/*.instructions.md` with explicit scope.
- Put reusable specialist personas in `.github/agents/*.agent.md`.

## Scope Discipline

- Scope every instruction file to the narrowest relevant paths.
- Prevent overlap by assigning each file a single primary concern.
- If overlap appears, consolidate or remove duplicate guidance.

## Authoring Quality

- Keep rules concise, explicit, and testable.
- Prefer examples only when they clarify non-obvious constraints.
- Keep naming and path patterns aligned with the current repository structure.

## Maintenance Workflow

- When rules evolve, update all affected customization files in one change.
- Validate with chat customization diagnostics and repository checks.
