---
name: update-pr
description: Legacy alias for pr:update. Use the canonical pr:update skill for PR updates.
---

Generated from `claude/skills/update-pr/SKILL.md` by `bin/sync-codex-from-claude`.


# update-pr (Legacy Alias)

This skill is maintained as a compatibility alias.
Canonical implementation: `pr:update` (plugin skill).

## Behavior

When invoked, execute the `pr:update` workflow exactly, including:
- detecting current PR state
- pushing unpushed commits when needed
- regenerating title/body from full branch history
- updating the PR via `gh pr edit`

## Migration Note

Prefer invoking:

```bash
/pr:update
```

to avoid drift between duplicate skills.
