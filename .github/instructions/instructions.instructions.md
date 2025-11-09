---
applyTo: ".github/instructions/*.md"
description: "Guidelines for writing instruction files"
---

# Instruction File Guidelines

## Philosophy
- Clarity over cleverness; keep each rule focused, explicit, and easy to apply in isolation.

## Structure
- Make them concise to avoid spamming LLM context
- Keep each instruction short and self-contained
- Use granular files per topic with specific `applyTo` patterns
- Always add short human-readable `description` in frontmatter

## Content focus
- Big picture architecture requiring multiple files to understand
- Critical workflows (builds, tests, debugging) not obvious from inspection
- Project-specific conventions differing from common practices
- Cross-thread coordination rules (for example, managers must be driven by Qt signals once moved to their thread)
- Integration points and cross-component communication patterns

## Best practices
- Use multiple `*.instructions.md` files per topic
- Apply selectively via `applyTo` property
- Reference instruction files in prompt files to avoid duplication
- Store in version control to share with team
- Run `poetry run pre-commit run --all-files` after updating instruction files so outstanding type issues are caught early
