---
name: create-pr
description: Legacy alias for pr:create. Use the canonical pr:create skill for PR creation.
---

Generated from `claude/skills/create-pr/SKILL.md` by `bin/sync-codex-from-claude`.


# create-pr (Legacy Alias)

This skill is maintained as a compatibility alias.
Canonical implementation: `pr:create` (plugin skill).

## Behavior

When invoked, execute the `pr:create` workflow exactly, including support for:
- creating a remote repository when needed
- pushing the current branch
- generating PR title/body from commit history
- opening draft PRs when requested

## Migration Note

Prefer invoking:

```bash
/pr:create
```

to avoid drift between duplicate skills.
