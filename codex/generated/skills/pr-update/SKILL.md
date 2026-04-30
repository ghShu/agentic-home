---
name: pr:update
description: Push any new commits to an existing PR and regenerate its title and description from the full branch history.
---

Generated from `claude/plugins/pr/skills/update/SKILL.md` by `bin/sync-codex-from-claude`.


# pr:update

Push unpushed commits to the current branch's PR and refresh the PR title and description based on all commits in the branch.

## Usage

```
/pr:update
```

## Workflow

### Step 1 — Identify current PR

```bash
git branch --show-current
gh pr view --json number,title,url,baseRefName,state,isDraft,body
```

- If no PR found: stop — "No PR found for this branch. Run `/pr:create` to open one."
- If state is `MERGED`: stop — "This PR is already merged."
- If state is `CLOSED`: warn — "This PR is closed. Proceeding will reopen it implicitly by pushing."
- If `isDraft: true`: note it in the output.

Store the existing title and body for use as a style guide in Step 4.

### Step 2 — Show unpushed commits

```bash
git log origin/<branch>..HEAD --oneline
```

Report how many commits are unpushed (may be zero if branch was already pushed).

### Step 3 — Push if needed

```bash
git push
```

Skip if already up to date. If push fails due to diverged history, report the error and stop — do not force-push.

### Step 4 — Regenerate title and description

Read all commits and diff stat in the branch (not just the new ones):

```bash
BASE=$(gh pr view --json baseRefName -q .baseRefName)
git log ${BASE}..HEAD --oneline
git diff ${BASE}..HEAD --stat
```

Generate a fresh title and body that accurately covers everything in the branch. Use the previous title and body as a guide for format and style — do not copy them verbatim, regenerate from the commits.

Body format:
```
## Summary
- <bullet per meaningful change>

## Notes
<context for reviewers, if any>
```

### Step 5 — Update PR

```bash
gh pr edit <number> --title "<new-title>" --body "<new-body>"
```

### Step 6 — Print summary

```
PR #N: "<title>"
State: open|draft  |  Base: main ← <branch>
Checks: <N passing / N failing / N pending>
URL: <url>
```

## Key Principles

- **Regenerate from all commits** — not just unpushed ones; the description should reflect the full branch
- **Use previous description as style guide** — match its format and level of detail
- **Never force-push** — if the branch has diverged, report the error and stop
- **Always update the description** even if there were no new commits to push (e.g., after a rebase)
