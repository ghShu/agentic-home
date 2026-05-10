---
name: handoff:read
description: Resume from a handoff file — briefs the current session on prior work state. Run at the start of a new session or after switching tools.
argument-hint: "[<name>] [--file PATH]"
allowed-tools: ["Bash", "Read"]
user-invocable: true
---

# handoff:read

Reads a handoff file and briefs the current session on prior work state. Works with files written by `/handoff:write` or authored manually.

## Resolving the file path

1. `--file <path>` → use that exact path
2. `<name>` positional arg → `.claude/<name>.md`
3. Default → `.claude/handoff.md`

Examples:
```
/handoff:read                         → .claude/handoff.md
/handoff:read jira-migration          → .claude/jira-migration.md
/handoff:read --file ~/ctx.md         → ~/ctx.md
```

## Step 1 — Resolve path and find the file

Apply the rules above. If the file does not exist, say:
"No handoff file found at `<resolved-path>`. Run `/handoff:write [<name>]` in the originating session first."

## Step 2 — Read and parse

Read the entire file and extract all sections.

## Step 3 — Brief the user

```
Resuming from handoff (<date>):

In progress: <summary>

Next steps:
  1. <step>
  2. <step>
  ...

Key decisions: <count> recorded
Caveats: <count> recorded
```

Then: "Ready to continue. Should I start with step 1 (<step description>)?"

## Step 4 — Offer to delete

After the user is oriented, offer:
> "Delete the handoff file now that it's been read? [y/N]"

If yes: `rm <resolved-path>`
