---
name: pr:checkout
description: Check out a pull request locally by number, URL, or branch name. Lists recent PRs if no argument given.
---

Generated from `claude/plugins/pr/skills/checkout/SKILL.md` by `bin/sync-codex-from-claude`.


# pr:checkout

Check out a pull request as a local branch.

## Usage

```
/pr:checkout [<number> | <url> | <branch>]
```

## Workflow

### Step 1 — Resolve PR reference

If an argument was provided (number, URL, or branch name), use it directly in Step 2.

If no argument was provided, list recent open PRs so the user can choose:

```bash
gh pr list --limit 15 --json number,title,headRefName,author,isDraft,state \
  --template '{{range .}}#{{.number}} {{.title}} ({{.headRefName}}) by @{{.author.login}}{{"\n"}}{{end}}'
```

Ask: "Which PR number do you want to check out?"

### Step 2 — Check out

```bash
gh pr checkout <ref>
```

`gh pr checkout` automatically creates a local branch named after the remote branch (or `<author>/<branch>` for fork PRs). No manual naming needed.

### Step 3 — Confirm and show status

```bash
git branch --show-current
gh pr view --json number,title,url,baseRefName,state,isDraft,checks
```

Print:

```
Checked out PR #N: "<title>"
Branch: <local-branch>
State: open|draft  |  Base: main ← <branch>
URL: <url>

Run `/pr:review --summary` to get an overview of the changes.
```

## Key Principles

- **Let `gh` handle branch naming** — do not invent a local branch name
- **Note fork PRs** — if the PR is from a fork, mention that pushing will go to the fork's branch (if the user has write access)
- **Warn on closed/merged PRs** — check out is still allowed but warn: "This PR is already <state>."
