---
name: create-pr
description: Create a pull request for the current branch, creating the remote repo first if it does not exist
---

# Create Pull Request

Push the current branch and open a new pull request. Handles the case where the
remote repo does not yet exist by creating it on GitHub first.

## Workflow

1. **Check remote** — does `origin` exist?
2. **Create remote repo if needed** — using `gh repo create`
3. **Determine base branch** — usually `main`; create it from the initial commit if the repo is new
4. **Push current branch** to `origin`
5. **Open PR** with a generated title and description based on all commits in the branch
6. **Return PR URL**

## Instructions

### Step 1 — Check for an existing remote

```bash
git remote get-url origin 2>/dev/null || echo "NO_REMOTE"
```

If a remote exists, skip to Step 3.

### Step 2 — Create the remote repo (no remote case)

Ask the user for visibility if not obvious (`--public` or `--private`). Default to `--private`.

```bash
# Create repo without initialising it (no README, no default branch)
gh repo create <owner>/<name> --public --description "<description>"

# Add remote
git remote add origin https://github.com/<owner>/<name>.git
```

Then set up `main` from the repository's initial commit so there is something to PR against:

```bash
# Push only the root commit as main
INITIAL=$(git rev-list --max-parents=0 HEAD)
git push origin ${INITIAL}:refs/heads/main
```

### Step 3 — Identify current branch and base

```bash
git branch --show-current        # current branch name
gh repo view --json defaultBranchRef -q .defaultBranchRef.name  # base branch
```

- If on `main`/`master` with nothing to PR against, stop and ask the user to create a feature branch.
- The base branch for the PR is the repo's default branch (usually `main`).

### Step 4 — Push current branch

```bash
git push -u origin <current-branch>
```

### Step 5 — Generate PR description and open PR

Review all commits in the branch:

```bash
git log <base-branch>..HEAD --oneline
git diff <base-branch>..HEAD --stat
```

Generate a concise PR description covering all changes. Then create the PR:

```bash
gh pr create \
  --base <base-branch> \
  --head <current-branch> \
  --title "<title>" \
  --body "$(cat <<'EOF'
## Summary
- <change 1>
- <change 2>

## What gets installed / changed
<brief description of impact>
EOF
)"
```

### Step 6 — Return PR URL

Print the PR URL from the output of `gh pr create`.

## Key Principles

- **Never push to main directly** — always work on a branch and PR
- **Default to `--private`** for new repos unless the user says otherwise
- **Root commit as main** — for new repos, seed `main` with the initial commit only so the PR shows a meaningful diff
- **Descriptive PR body** — derive it from commit messages and `git diff --stat`, not from assumptions
- **Idempotent** — if the branch is already pushed, just create the PR

## Example Output

```
No remote found. Creating GitHub repo...
✓ Created https://github.com/username/agentic-home
✓ Seeded main with initial commit
✓ Pushed branch setup to origin

Opening PR: setup → main

PR #1: "Set up agentic home directory configuration"
https://github.com/username/agentic-home/pull/1
```
