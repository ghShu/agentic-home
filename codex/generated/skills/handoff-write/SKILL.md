---
name: handoff:write
description: Capture current session state into a handoff file readable by any AI tool (Claude, Codex, Cursor). Run before switching sessions or tools.
---

Generated from `claude/plugins/handoff/skills/write/SKILL.md` by `bin/sync-codex-from-claude`.


# handoff:write

Captures the current session state into a plain markdown file. The file can be read by any AI tool or editor.

## Resolving the file path

1. `--file <path>` → use that exact path
2. `<name>` positional arg → `.claude/<name>.md`
3. Default → `.claude/handoff.md`

Examples:
```
/handoff:write                        → .claude/handoff.md
/handoff:write jira-migration         → .claude/jira-migration.md
/handoff:write --file ~/ctx.md        → ~/ctx.md
```

## Step 1 — Resolve path

Apply the rules above. Remember the resolved path for Steps 3 and 4.

## Step 2 — Gather git state

Run in parallel:

```bash
git status --short
git diff --stat HEAD
git log --oneline -10
git branch --show-current
```

## Step 3 — Identify context

From the conversation history and git state, extract:

- **What's in progress** — the specific task being worked on right now (incomplete)
- **What was completed** — work finished this session
- **Next steps** — ordered, concrete actions for the next session
- **Key decisions** — non-obvious choices made, with reasoning
- **Caveats / gotchas** — surprises, constraints, workarounds in place
- **Changed files** — from `git status` and `git diff --stat`

## Step 4 — Write the file

```markdown
# Handoff: <project-name> — <YYYY-MM-DD HH:MM>

## In Progress
<one paragraph — what was being worked on, incomplete>

## Completed This Session
- 

## Next Steps
1. 

## Key Decisions
- 

## Caveats & Gotchas
- 

## Changed Files
- 

## Context & Links
- 
```

Fill every section. Leave a section as `-` only if truly nothing to record.

## Step 5 — Confirm

```
Handoff written to <resolved-path>
  In progress: <one-line summary>
  Next steps: <count> items
  Changed files: <count> files
```
