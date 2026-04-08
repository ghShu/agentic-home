---
name: pr:review
description: Analyze a PR and optionally submit a review (approve / request-changes / comment). Use --summary to get analysis without submitting.
---

# pr:review

Read a pull request's diff and commits, generate a structured analysis, then optionally submit a review.

## Usage

```
/pr:review [<number> | <url> | <branch>] [approve | request-changes | comment] [--summary]
```

- **No args**: operate on the current branch's PR; ask for review type after analysis
- **`--summary`**: print analysis only, do not submit a review (useful for understanding someone else's PR before diving in)
- **`approve` / `request-changes` / `comment`**: skip the type prompt and go straight to that review type

## Workflow

### Step 1 — Resolve PR reference

If an arg was given (number, URL, or branch name), use it with `gh`. Otherwise, resolve from the current branch:

```bash
git branch --show-current
gh pr view --json number,title,url,baseRefName,headRefName,state,isDraft,author
```

- If no PR found: stop — "No PR found for this branch. Run `/pr:create` to open one."
- If state is `MERGED` or `CLOSED`: warn prominently before proceeding.
- If `isDraft: true`: note "This is a draft PR."

### Step 2 — Fetch diff and commits

```bash
gh pr diff <ref>
git log <baseRefName>..<headRefName> --oneline
gh pr view <ref> --json additions,deletions,changedFiles,files
```

### Step 3 — Read changed files for context

For each changed file, read the relevant sections using the Read tool to understand the full context — not just the diff lines but what surrounds them.

### Step 4 — Generate structured analysis

Produce a clear, file-organized analysis covering:

- **What this PR does** — 2–4 sentence summary of the intent and approach
- **Per-file findings** — for each changed file, note what changed and any observations (correctness, style, missing tests, potential bugs, etc.)
- **Overall assessment** — strengths, concerns, questions

Keep it concise. Flag real issues clearly; do not nitpick style unless it affects readability or correctness.

### Step 5 — Summary mode

If `--summary` flag is present: print the analysis and stop. Do not proceed to review submission.

### Step 6 — Determine review type

If a type was given as an arg (`approve`, `request-changes`, `comment`), use it directly.

Otherwise ask:
> "Submit as: [1] approve  [2] request-changes  [3] comment  [4] don't submit"

If the user picks 4 (or presses Enter with no selection): stop without submitting.

### Step 7 — Confirmation for approve

For `approve` only — confirm before submitting:

```
You are approving PR #N: "<title>" by @<author>
Proceed? [y/N]
```

Default is NO. Only proceed on explicit `y` / `yes`.

### Step 8 — Show body and allow editing

Display the generated review body. Ask: "Edit the review body before submitting? [y/N]"

If yes: show the body and wait for the user to provide an edited version.

### Step 9 — Submit review

```bash
# Approve (body optional)
gh pr review <ref> --approve [-b "<body>"]

# Request changes (body required)
gh pr review <ref> --request-changes -b "<body>"

# Comment
gh pr review <ref> --comment -b "<body>"
```

Confirm: "Review submitted: <type> on PR #N."

## Key Principles

- **Read before judging** — always read full file context, not just diff hunks
- **--summary is read-only** — never submit anything in summary mode
- **Default NO on approve** — approvals need explicit confirmation
- **Empty body on request-changes is not allowed** — always require a body explaining what needs to change
- **Surface the PR URL** at the end of every run
