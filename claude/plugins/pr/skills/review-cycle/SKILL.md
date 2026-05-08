---
name: pr:review-cycle
description: Create PR, spawn background review agent that posts findings as PR comments, poll and fix, re-review until clean.
disable-model-invocation: true
argument-hint: [pr-reference]
---

Automate the full PR review cycle: create PR, spawn a background review agent that posts findings as PR comments, poll for and fix comments, then re-review until clean or max iterations reached.

## Step 0: Parse Arguments & Extract PR Metadata

Parse `$ARGUMENTS` for a PR reference:
- If provided (URL, number, or `owner/repo#number`), use it as the target PR. Skip Step 1.
- If empty, create a new PR in Step 1.

Once you have a PR reference, extract metadata needed for API calls:
```
gh pr view ${PR_REF} --json number,url,headRepositoryOwner,headRepository --jq '{number,url,owner:.headRepositoryOwner.login,repo:.headRepository.name}'
```
Store: `PR_NUMBER`, `PR_URL`, `OWNER`, `REPO`.

Initialize a global `SEEN_COMMENT_IDS` set (empty). This persists across all poll loops in Steps 3 and 4.

## Step 1: Create PR (skip if PR reference provided)

Use the Skill tool to invoke `pr:sync` (commits any uncommitted changes, then pushes and opens or updates the PR).

After it returns, extract the PR number and run the metadata extraction from Step 0:
```
PR_NUMBER=$(gh pr view --json number -q .number)
```

If `pr:sync` fails, stop and report the error.

## Step 2: Spawn Deep Review Agent

Use the Agent tool to spawn a **background** agent (`run_in_background: true`). Provide the following prompt (fill in the actual values for OWNER, REPO, PR_NUMBER):

```
You are reviewing PR #<PR_NUMBER> in <OWNER>/<REPO>.

Your job:
1. Understand the PR changes by running `gh pr diff <PR_NUMBER>` and reading relevant source files for context.
2. Optionally invoke `pr:review --summary` via the Skill tool for structured analysis to draw on. Do NOT submit a review through pr:review — this skill posts inline comments directly via the GitHub API instead.
3. Identify all findings worth surfacing. Do NOT do interactive triage — every finding gets reported.
4. Post findings as a GitHub PR review with inline comments. Write a JSON payload to a temp file and use `gh api --input`:

   Build a JSON object:
   {
     "body": "## Automated Deep Review\n\nPosted by review-cycle agent. Findings below as inline comments.",
     "event": "COMMENT",
     "comments": [
       {
         "path": "<relative file path>",
         "line": <line number in the new version of the file>,
         "body": "**[MUST_FIX]** <description>\n\n<suggested fix or context>"
       }
     ]
   }

   Where severity is one of: MUST_FIX, SHOULD_FIX, CONSIDER.

   Write this JSON to /tmp/review-payload.json, then run:
   gh api repos/<OWNER>/<REPO>/pulls/<PR_NUMBER>/reviews --method POST --input /tmp/review-payload.json

   If there are too many comments for one review (GitHub limits to ~30-50 inline comments per review), split into multiple review submissions.

5. If the review finds no issues at all, post a single review with body "No issues found." and event "COMMENT" with an empty comments array.

Important: Do NOT apply fixes yourself. Only post findings as PR comments.
```

Do **not** wait for the agent to finish. Proceed immediately to Step 3.

## Step 3: Poll and Address Comments

Enter a polling loop, waiting for comments from the background deep-review agent spawned in Step 2.

### 3a. Fetch new comments

Fetch PR review comments (inline):
```
gh api repos/{OWNER}/{REPO}/pulls/{PR_NUMBER}/comments --paginate
```

Parse each comment's `id`, `body`, `path`, `line` (or `original_line`), `diff_hunk`, and `user.login`.

Identify new comments: any comment whose `id` is NOT in `SEEN_COMMENT_IDS`. Add all fetched IDs to `SEEN_COMMENT_IDS`.

### 3b. Triage and address comments

If there are new inline comments:

1. **Read and understand each comment.** For each comment, read the referenced file and surrounding context — not just the `diff_hunk`. Understand what the reviewer is flagging and why.

2. **Critically evaluate each comment.** Not every finding warrants a code change. For each comment, decide one of:
   - **Fix** — the finding is valid and the suggested direction is correct. Apply the fix.
   - **Fix differently** — the finding is valid but the suggested approach is wrong or suboptimal. Fix the real issue in a better way.
   - **Dismiss** — the finding is a false positive, a stylistic preference that doesn't match the codebase, or a change that would introduce a regression or unnecessary complexity. Do not change the code.

   Reasons to dismiss: the reviewer misunderstood the code's intent, the suggestion conflicts with existing patterns in the codebase, the fix would break other callers, or the issue is purely cosmetic with no real impact.

3. **Apply fixes.** Group accepted fixes by file. Use the Edit tool to apply changes.

4. **Reply to dismissed comments.** For each dismissed comment, post a reply explaining why it was not addressed:
   ```
   gh api repos/{OWNER}/{REPO}/pulls/{PR_NUMBER}/comments/{COMMENT_ID}/replies --method POST -f body="Not addressed: <brief reason>"
   ```

5. **Commit and push.** If any files were modified:
   - Stage modified files: `git add <specific files>` (not `git add -A`)
   - Commit with a message summarizing the fixes
   - Run `git push`

If there are no new comments, skip to 3c.

### 3c. Check exit condition

Exit the poll loop and proceed to Step 4 **only when both** of these are true:
- The background review agent from Step 2 has completed (you received its completion notification)
- No new comments were found in the most recent 3a check

Otherwise: **wait 60 seconds** (`sleep 60`), then go back to 3a.

## Step 4: Re-review

Initialize: `ITERATION = 1`, `MAX_ITERATIONS = 3`

### 4a. Spawn quick review agent

Use the Agent tool to spawn a **background** agent (`run_in_background: true`). Provide the following prompt (fill in actual values):

```
You are re-reviewing PR #<PR_NUMBER> in <OWNER>/<REPO> after fixes were applied (round <ITERATION>).

Your job:
1. Review the latest state of the PR using `gh pr diff <PR_NUMBER>` and reading relevant source files.
2. Optionally invoke `pr:review --summary` via the Skill tool for a structured analysis to draw on. Do NOT submit a review through pr:review.
3. Collect findings. Post as a GitHub PR review with inline comments (same JSON + gh api --input approach as Step 2).
   Use body: "## Re-review Round <ITERATION>\n\nPosted by review-cycle agent."
   Same severity levels: MUST_FIX, SHOULD_FIX, CONSIDER.
4. If no findings, post a review with body "Re-review round <ITERATION>: No issues found." and empty comments array.

Important: Do NOT apply fixes yourself. Only post findings as PR comments.
```

### 4b. Poll and address

Re-enter the polling loop (same logic as Step 3), reusing the global `SEEN_COMMENT_IDS` so previously-addressed comments are skipped.

Exit when the re-review agent completes and no new comments were found.

### 4c. Evaluate and loop

After the poll loop exits for this round:
- If no new MUST_FIX or SHOULD_FIX comments were posted in this round: PR is clean. Go to Step 5.
- If MUST_FIX or SHOULD_FIX comments were found and fixed:
  - Increment `ITERATION`
  - If `ITERATION < MAX_ITERATIONS`: go back to 4a
  - If `ITERATION >= MAX_ITERATIONS`: go to Step 5 and report max iterations reached

## Step 5: Summary

Report a final summary:

```
## Review Cycle Complete

**PR:** <PR_URL>
**Review rounds:** <1 deep + N quick>
**Outcome:** <Clean / Max iterations reached>

### Issues resolved
- <list of all fixed issues across all rounds>

### Remaining issues (if any)
- <list of unresolved MUST_FIX / SHOULD_FIX from final round>
```
