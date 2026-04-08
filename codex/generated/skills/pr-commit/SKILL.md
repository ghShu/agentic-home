---
name: pr:commit
description: Analyze all uncommitted changes, group them into logical commits with Conventional Commit messages, and execute after confirmation.
---

Generated from `claude/plugins/pr/skills/commit/SKILL.md` by `bin/sync-codex-from-claude`.


# pr:commit

Read all uncommitted changes, propose logical commit groupings with Conventional Commit messages, show the plan for confirmation, then execute.

## Usage

```
/pr:commit
```

## Workflow

### Step 1 — Check for uncommitted changes

```bash
git status --short
git diff          # unstaged changes
git diff --cached # staged changes
```

If the working tree is clean (no staged or unstaged changes, no untracked files relevant to the project): stop — "Nothing to commit."

### Step 2 — Read all diffs

Read the full diff output to understand the nature and scope of every change. Do not rely on filenames alone — read the actual content to understand what changed and why.

Note which files are staged vs. unstaged; this does not constrain the commit groupings (you will stage files explicitly per group in Step 5).

### Step 3 — Propose logical commit groupings

Analyze the changes and group them by concern:

- Group by: feature area, module/package boundary, change type (new code vs. tests vs. config vs. docs)
- A group that touches both implementation and its tests is fine — tests and the code they cover often belong together
- Avoid grouping unrelated changes just because they touch the same file
- Default to **multiple commits** when changes are clearly separable; a single commit is correct only when all changes are tightly coupled

Assign each group a **Conventional Commit** message:
- Prefix: `feat:`, `fix:`, `test:`, `chore:`, `docs:`, `refactor:`, `perf:`, `ci:`
- Imperative mood, no period, ≤72 chars total
- Examples: `feat: add JWT middleware`, `fix: handle null session token`, `chore: update lockfile`

### Step 4 — Show proposal and confirm

Present the proposed commits clearly:

```
Proposed commits:

  1. feat: add JWT authentication middleware
     → src/auth/jwt.ts, src/auth/middleware.ts

  2. test: add auth middleware unit tests
     → tests/auth/jwt.test.ts

  3. chore: update dependencies
     → package.json, package-lock.json

Proceed with these 3 commits? [Y/n]
```

If the user says no: ask what they'd like to change (different grouping, different message, exclude a file) and re-propose. Do not commit anything until the user confirms.

### Step 5 — Execute commits in order

For each group, stage only that group's files and commit:

```bash
git add <file1> <file2> ...
git commit -m "<conventional-commit-message>"
```

Use explicit file paths — never `git add .` or `git add -A`.

For untracked files, use `git add <file>` to include them.

### Step 6 — Report and suggest next step

```
3 commits created:
  abc1234 feat: add JWT authentication middleware
  def5678 test: add auth middleware unit tests
  789abcd chore: update dependencies
```

Then check if on a PR branch:
```bash
gh pr view 2>/dev/null
```

If a PR exists:
> "Run `/pr:update` to push and refresh the PR description."

If no PR:
> "Run `/pr:create` to open a pull request."

## Key Principles

- **Read the diffs, not just the filenames** — grouping requires understanding what changed
- **Multiple commits by default** — only collapse to one if the changes are truly inseparable
- **Confirm before committing** — never commit without explicit user approval of the plan
- **Explicit file staging** — never use `git add .`; stage each group's files by name
- **Conventional Commits** — always use a recognized prefix; `feat` and `fix` for user-facing changes, `chore`/`test`/`docs`/`refactor` for everything else
