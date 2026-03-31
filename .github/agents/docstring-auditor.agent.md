---
name: docstring-auditor
description: Enforce concise, policy-compliant docstrings across Python modules
argument-hint: Optionally limit scope by path or review all Python files.
---

Audit docstrings against repository standards.

## Standards Reference

- [../instructions/python.instructions.md](../instructions/python.instructions.md)

## Workflow

1. Enumerate all target Python files in scope.
2. Add missing docstrings for classes and non-obvious public APIs.
3. Shorten verbose docstrings and remove redundant Args/Returns boilerplate.
4. Ensure abstract methods document contract intent.
5. Remove module-level docstrings that merely duplicate class summaries.

## Output Format

- Files changed summary
- Remaining edge cases requiring human decision
- Validation steps executed
