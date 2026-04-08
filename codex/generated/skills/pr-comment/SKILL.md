---
name: pr:comment
description: Fetch all unresolved review comments on a PR, read the relevant code, and propose fixes for each one.
---

Generated from `claude/plugins/pr/skills/comment/SKILL.md` by `bin/sync-codex-from-claude`.


# pr:comment

Fetch all open review comments on a PR, read the surrounding code for context, and propose concrete fixes. Does not apply changes — presents proposals only.

## Usage

```
/pr:comment [<number> | <url> | <branch>]
```

## Workflow

### Step 1 — Identify PR

If an argument was provided, use it. Otherwise resolve from the current branch:

```bash
git branch --show-current
gh pr view --json number,title,url,baseRefName,headRefName,state,isDraft
```

- If no PR: stop — "No PR found. Run `/pr:create` to open one."
- If state is `MERGED` or `CLOSED`: warn but allow continuing (review comments may still be useful).

### Step 2 — Fetch review comments (two sources)

**Source 1 — General review comments and review bodies:**
```bash
gh pr view <ref> --json reviews,comments
```

**Source 2 — Inline diff comments (with file path and line number):**
```bash
OWNER=$(gh repo view --json owner -q .owner.login)
REPO=$(gh repo view --json name -q .name)
gh api repos/${OWNER}/${REPO}/pulls/<number>/comments
```

The inline comments include `path`, `line`, `diff_hunk`, `body`, and `user.login`.

### Step 3 — Filter to actionable comments

Skip:
- Review bodies that are purely `APPROVED` with no substantive text
- Comments that contain only emoji reactions or "LGTM" / "looks good" / "nice"
- Comments marked as `outdated` (position is null in the diff) — note these separately at the end

Keep:
- All inline comments with a `CHANGES_REQUESTED` review
- Any inline comment that contains a question, suggestion, or critique
- General review comments with substantive feedback

If no actionable comments remain: report "No open review comments to address." and stop.

### Step 4 — Read code context for each comment

For each inline comment, use the Read tool to read the relevant file at and around the indicated line (±20 lines for context). This is essential — do not propose fixes based only on the diff hunk.

For general (non-inline) comments, read any files they reference.

### Step 5 — Generate proposals

Group comments by file, then produce a structured action plan. For each comment:

```
── Comment by @<reviewer> (<file>:<line> or general)
   "<comment text>"

   Proposed fix:
   <explanation of what to change and why>

   <diff or code snippet showing the change, if applicable>
```

Be specific. If a comment asks a question, answer it and propose a code change if one is warranted. If a comment is ambiguous or could be addressed in multiple ways, surface the ambiguity.

### Step 6 — Handle outdated comments

If any comments were skipped because they are outdated (position is null), list them at the end:

```
Outdated comments (position no longer in diff — review manually):
- @<reviewer>: "<text>" (<file>)
```

### Step 7 — Closing note

End with:
```
Apply the changes above, then run `/pr:sync` to commit and push.
```

If there were conflicting suggestions from multiple reviewers, flag each conflict explicitly before the closing note and ask the user to decide.

## Key Principles

- **Read full file context** — never propose a fix based only on the diff hunk; the surrounding code matters
- **Proposals only** — do not apply any changes to the working tree
- **Surface conflicts** — when reviewers disagree, present both positions and ask the user to decide
- **Outdated comments are not silently dropped** — list them separately so the user can decide
- **Preserve reviewer intent** — understand what the reviewer is asking for, not just the literal words
