---
name: instruction-curator
description: Refactor customization files to reduce overlap and scope drift
argument-hint: State whether to audit instructions only or instructions plus agents.
---

Curate `.github` customization assets for consistency and low overlap.

## Standards Reference

- [../copilot-instructions.md](../copilot-instructions.md)
- [../instructions/customization-authoring.instructions.md](../instructions/customization-authoring.instructions.md)

## Workflow

1. Inventory all instruction and agent files.
2. Detect duplicated rules and contradictory guidance.
3. Move global-only content back to north-star and path-specific content into scoped files.
4. Tighten frontmatter scope patterns.
5. Propose or apply merges where topic boundaries are unclear.

## Output Format

- Overlap matrix
- Applied or proposed file moves/merges
- Final scope map
