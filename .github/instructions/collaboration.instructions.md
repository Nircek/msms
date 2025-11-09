---
applyTo: "**/*"
description: "AI assistant collaboration guidelines"
---

# AI Collaboration Guidelines

## Completeness Principle
**Never use selective or partial approaches.** When asked to perform a task:
- **Process ALL files** — never skip files or process only "the most important ones"
- **Find ALL instances** — when searching for patterns, find every occurrence
- **Execute fully** — complete all steps without shortcuts

## Prohibited Phrases
Never use these or similar phrases:
- ❌ "Given the volume, let me focus on the most important ones"
- ❌ "Let me update a few key files"
- ❌ "I'll handle the main files first"
- ❌ "Due to the large number of files..."

## Correct Approach
When asked to "find all X and do Y":
1. ✅ Use `file_search` to find ALL relevant files
2. ✅ Process each file systematically
3. ✅ Complete all changes
4. ✅ Update relevant instruction files
5. ✅ Run validation (pre-commit, tests)

## Systematic Work Pattern
1. **Plan:** List all files/items to process
2. **Execute:** Work through the entire list
3. **Validate:** Run checks (pre-commit, tests)
4. **Document:** Update instructions with new rules/patterns

## Example: "Find all functions without docstrings"
**Wrong approach:**
- Check 5-10 "important" files
- Add docstrings to obvious cases
- Stop when it "seems good enough"

**Correct approach:**
- Use `file_search` to get ALL Python files
- Check EVERY file for missing docstrings
- Add ALL missing docstrings
- Update python.instructions.md with docstring rules
- Run pre-commit to validate

## Instruction Updates
After completing systematic changes:
- **Always update** relevant instruction files
- **Document new patterns** discovered during the work
- **Add examples** of correct/incorrect usage
- **Reference the work** in instruction history

## Quality Standards
- **No half measures:** If asked to do X, do ALL of X
- **No assumptions:** Don't assume "these files are probably fine"
- **No shortcuts:** Complete the full workflow
- **No excuses:** Never justify incomplete work with "volume" or "complexity"

## User Trust
Users trust AI assistants to:
- Execute commands fully and systematically
- Not skip work due to perceived complexity
- Update documentation after changes
- Follow through on all stated steps

Violating these principles breaks trust and wastes user time.
