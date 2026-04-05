---
name: pr:sync
description: Commit any uncommitted changes (if present) then push and update the PR description. The single command to make your PR reflect current local state.
---

# pr:sync

Make the PR reflect the current local state in one step: commit any uncommitted changes, then push and refresh the PR description.

Equivalent to running `/pr:commit` (if needed) followed by `/pr:update`.

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

### Step 3 — Run the pr:update flow

1. Verify PR exists: `gh pr view --json number,title,url,baseRefName,state,body`
   - If no PR: stop — "No PR found. Run `/pr:create` to open one."
2. Push: `git push`
3. Read all commits since base and regenerate title + description:
   ```bash
   BASE=$(gh pr view --json baseRefName -q .baseRefName)
   git log ${BASE}..HEAD --oneline
   git diff ${BASE}..HEAD --stat
   ```
4. Update PR: `gh pr edit <number> --title "<title>" --body "<body>"`

### Step 4 — Print summary

```
PR #N: "<title>"
State: open|draft  |  Base: main ← <branch>
Checks: <N passing / N failing / N pending>
URL: <url>
```

## Key Principles

- **Stop at any failure** — if the commit step fails or is declined, do not push; if push fails, do not update the description
- **Thin orchestration** — all logic lives in the underlying commit and update flows; this skill only chains them
- **No-op is clean** — "Nothing to sync" is a valid, non-error outcome
