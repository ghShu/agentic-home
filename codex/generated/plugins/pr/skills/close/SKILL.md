---
name: pr:close
description: Close an open PR (with optional comment) or reopen a closed one. Always confirms before closing.
---

# pr:close

Close an open pull request or reopen a closed one.

## Usage

```
/pr:close [<number> | <url> | <branch>]
```

## Workflow

### Step 1 — Identify PR

If an argument is provided, use it. Otherwise resolve from the current branch:

```bash
git branch --show-current
gh pr view --json number,title,url,baseRefName,state
```

- If no PR found: stop — "No PR found for this branch."
- If state is `MERGED`: stop — "PR #N is already merged and cannot be closed."

### Step 2 — Determine action from current state

- State is `OPEN` or `DRAFT`: action is **close**
- State is `CLOSED`: action is **reopen**

### Step 3a — Close flow

**Ask for an optional comment:**
```
Add a comment explaining why this PR is being closed? (Enter to skip)
```

**Confirm:**
```
This will close PR #N: "<title>"
Proceed? [y/N]
```

Default is **NO**. Only proceed on explicit `y` / `yes`.

**Execute:**
```bash
# If comment was provided:
gh pr comment <ref> --body "<reason>"

# Close the PR:
gh pr close <ref>
```

**Report:**
```
✓ Closed PR #N: "<title>"
URL: <url>
```

### Step 3b — Reopen flow

```
This will reopen PR #N: "<title>" (closed)
Proceed? [y/N]
```

Default is **NO**.

```bash
gh pr reopen <ref>
```

**Report:**
```
✓ Reopened PR #N: "<title>"
URL: <url>
```

## Key Principles

- **Always confirm before closing** — default is NO
- **Comment before close** — offer the option; a closing comment helps collaborators understand why
- **Reopen is detected automatically** — no need to specify; the skill checks current state
- **Merged PRs cannot be closed** — stop with a clear message
