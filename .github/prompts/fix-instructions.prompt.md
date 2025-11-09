---
mode: agent
description: "Review and refactor instruction/prompt files for clarity and granularity"
---

## Task
Review all files in `.github/{instructions,prompts}` for:
- Deprecated content that contradicts current codebase patterns
- Duplicated instructions across multiple files
- Missing `description` fields in frontmatter
- Overly broad `applyTo` patterns that should be more specific
- Instructions that should be split into separate, focused files

Update files to follow guidelines in:
- `.github/instructions/instructions.instructions.md`
- `.github/instructions/prompts.instructions.md`
