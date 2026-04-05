---
name: pr:create
description: Push the current branch and open a new pull request. Handles new remote repos and draft PRs.
---

# pr:create

Push the current branch and open a new pull request. Handles the case where the remote repo does not yet exist.

## Usage

```
/pr:create [--draft]
```

## Workflow

### Step 1 — Check for an existing remote

```bash
git remote get-url origin 2>/dev/null || echo "NO_REMOTE"
```

If a remote exists, skip to Step 3.

### Step 2 — Create the remote repo (no remote case)

Ask the user for visibility (`--public` or `--private`). Default to `--private`.

```bash
# Create repo without initializing it
gh repo create <owner>/<name> --private --description "<description>"

# Add remote
git remote add origin https://github.com/<owner>/<name>.git
```

Seed `main` from the repository's initial commit so there is something to PR against:

```bash
INITIAL=$(git rev-list --max-parents=0 HEAD)
git push origin ${INITIAL}:refs/heads/main
```

### Step 3 — Check current branch

```bash
git branch --show-current
gh repo view --json defaultBranchRef -q .defaultBranchRef.name
```

- If on the default branch (`main`/`master`): stop — "Create a feature branch first."
- Check if a PR already exists: `gh pr view 2>/dev/null`. If one exists: stop — "A PR already exists for this branch. Use `/pr:update` instead."

### Step 4 — Push branch

```bash
git push -u origin <current-branch>
```

### Step 5 — Generate title and description

Read all commits and diff stat since the base branch:

```bash
BASE=$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name)
git log ${BASE}..HEAD --oneline
git diff ${BASE}..HEAD --stat
```

Generate a concise title (imperative, ≤72 chars) and a PR body:

```
## Summary
- <bullet per meaningful change>

## Notes
<any deployment steps, breaking changes, or context reviewers need>
```

Omit the Notes section if there is nothing notable.

### Step 6 — Open PR

```bash
gh pr create \
  --base <base> \
  --head <branch> \
  --title "<title>" \
  --body "<body>" \
  [--draft]   # if --draft was passed
```

### Step 7 — Print summary

```
PR #N: "<title>"
State: open  |  Base: main ← <branch>
Checks: pending
URL: <url>
```

## Key Principles

- **Never push to the default branch directly**
- **Default to `--private`** for new repos
- **Seed main with the root commit only** for new repos — this keeps the PR diff meaningful
- **Redirect to `/pr:update`** if a PR already exists for the branch
- **`--draft`** is passed through when provided
