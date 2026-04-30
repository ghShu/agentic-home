---
name: pr:sync
description: Commit any uncommitted changes (if present) then push and open or update the PR. Works for both new and existing PRs — the single command to publish local work.
---

Generated from `claude/plugins/pr/skills/sync/SKILL.md` by `bin/sync-codex-from-claude`.


# pr:sync

Make the PR reflect the current local state in one step: commit any uncommitted changes, then push and open or refresh the PR.

- **Existing PR:** equivalent to `/pr:commit` (if needed) followed by `/pr:update`
- **No PR yet:** equivalent to `/pr:commit` (if needed) followed by `/pr:create`

## Usage

```
/pr:sync
```

## Workflow

### Step 1 — Check for uncommitted changes

```bash
git status --short
```

**If uncommitted changes exist:** run the full `pr:commit` flow:
1. Read all diffs (`git diff`, `git diff --cached`)
2. Propose logical commit groupings with Conventional Commit messages
3. Show the plan and ask for confirmation
4. Execute commits on approval

If the user declines the commit step: stop here. Do not push partial work.

**If working tree is clean:** skip straight to Step 2.

### Step 2 — Check for unpushed commits

```bash
git log origin/<branch>..HEAD --oneline
```

**If nothing to push and no commits were just created:** stop — "Nothing to sync — PR is already up to date."

### Step 3 — Check whether a PR exists

```bash
gh pr view --json number,title,url,baseRefName,state,body 2>/dev/null
```

**If a PR exists:** run the `pr:update` flow:
1. Push: `git push`
2. Read all commits since base and regenerate title + description:
   ```bash
   BASE=$(gh pr view --json baseRefName -q .baseRefName)
   git log ${BASE}..HEAD --oneline
   git diff ${BASE}..HEAD --stat
   ```
3. Update PR: `gh pr edit <number> --title "<title>" --body "<body>"`

**If no PR exists:** run the full `pr:create` flow (push + generate title/body + open PR).

### Step 4 — Print summary

```
PR #N: "<title>"
State: open|draft  |  Base: main ← <branch>
Checks: <N passing / N failing / N pending>
URL: <url>
```

## Key Principles

- **Stop at any failure** — if the commit step fails or is declined, do not push; if push fails, do not open/update the PR
- **Thin orchestration** — all logic lives in the underlying commit, update, and create flows; this skill only chains them
- **No-op is clean** — "Nothing to sync" is a valid, non-error outcome
