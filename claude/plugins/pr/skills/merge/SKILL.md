---
name: pr:merge
description: Merge a pull request with strategy selection (squash/merge/rebase), CI and review checks, and explicit confirmation before proceeding.
---

# pr:merge

Merge a pull request. Always confirms the exact action before proceeding.

## Usage

```
/pr:merge [<number> | <url> | <branch>] [squash | merge | rebase]
```

Default strategy: `squash`.

## Workflow

### Step 1 — Identify PR

If an argument is provided, use it. Otherwise resolve from the current branch:

```bash
git branch --show-current
gh pr view --json number,title,url,baseRefName,headRefName,state,isDraft,mergeStateStatus,mergeable
```

- If no PR found: stop.
- If state is `MERGED`: stop — "PR #N is already merged."
- If state is `CLOSED`: stop — "PR #N is closed. Reopen it before merging."
- If `isDraft: true`: stop — "PR #N is a draft. Mark it as ready before merging."

### Step 2 — Check CI status

```bash
gh pr checks <ref> 2>/dev/null || true
```

`gh pr checks` exits non-zero when no checks are configured — treat that as "no checks" and continue silently.

If any checks are **failing**: warn prominently:
```
! N check(s) are failing:
  ✗ <check-name>: <status>
```

If any checks are **pending**: warn:
```
! N check(s) are still running.
```

Do not block the merge — surface the warnings and let the user decide.

### Step 3 — Check review status

```bash
gh pr view <ref> --json latestReviews,reviewRequests
```

If there are pending **change requests**: warn:
```
! @<reviewer> has requested changes.
```

If there are outstanding **review requests** (reviews not yet submitted): note them.

Do not block — warn and continue.

### Step 4 — Determine strategy

If a strategy was given as an argument (`squash`, `merge`, or `rebase`), use it.

Otherwise ask:
```
Merge strategy:
  [1] squash  — combine all commits into one (default)
  [2] merge   — merge commit preserving all commits
  [3] rebase  — replay commits onto base branch
```

Default: squash.

### Step 5 — Ask about branch deletion

```
Delete branch after merge? [Y/n]
```

Default: YES.

### Step 6 — Confirm

State exactly what will happen:

```
This will squash-merge PR #N ("<title>") into `main`
and delete the remote branch `<head-branch>`.

Proceed? [y/N]
```

Default is **NO**. Only proceed on explicit `y` / `yes`.

### Step 7 — Merge

If `mergeStateStatus` is `BLOCKED` and requires a merge queue:
```bash
gh pr merge <ref> --squash --auto
```
Note: `--auto` enables auto-merge; the PR will merge automatically once all requirements are met. Stop here — post-merge cleanup will happen when the queue processes the PR.

Otherwise, use the GitHub API directly — **do not use `gh pr merge`**. `gh pr merge` attempts a local `git checkout` after merging, which fails when the base branch is already checked out in another worktree. This applies to any worktree setup (`claude --worktree`, `git worktree add`, etc.) — the locking is enforced by git, not by the tool that created the worktree.

```bash
OWNER=$(gh repo view --json owner -q .owner.login)
REPO=$(gh repo view --json name -q .name)

# Merge
gh api repos/${OWNER}/${REPO}/pulls/<number>/merge \
  --method PUT \
  --field merge_method=squash \
  --field commit_title="<PR title> (#<number>)"

# Delete remote branch (if requested)
gh api repos/${OWNER}/${REPO}/git/refs/heads/<head-branch> --method DELETE
```

Map strategy argument to `merge_method`: `squash` → `squash`, `merge` → `merge`, `rebase` → `rebase`.

### Step 8 — Post-merge cleanup

Try to fast-forward the local base branch without checking it out:

```bash
git fetch origin <base-branch>:<base-branch>
```

If that fails (exit non-zero — happens when the base branch is checked out in another worktree, including the primary worktree), fall back to updating only the remote tracking ref:

```bash
git fetch origin
```

Then note in the result: "local `<base-branch>` needs a `git pull` in the worktree where it is checked out."

If currently on the merged head branch and the base branch is NOT locked by another worktree, optionally switch:
```bash
git checkout <base-branch>
```

### Step 9 — Print result

```
✓ Merged PR #N: "<title>"
  Strategy: squash  |  Branch deleted: yes
  Base branch updated: main
```

## Key Principles

- **Always confirm** — never merge without explicit `y` confirmation; default is NO
- **Surface warnings, don't block** — failing checks and change requests are warnings, not hard stops; the user may have context
- **Default squash** — keeps base branch history clean for feature branches
- **Switch off the merged branch** — always land on the base branch after merging to avoid confusion
- **`--auto` for merge queues** — detect `BLOCKED` state and use auto-merge rather than failing
- **API over `gh pr merge`** — `gh pr merge` runs local git operations after merging that break in worktree setups; use the GitHub API directly instead
