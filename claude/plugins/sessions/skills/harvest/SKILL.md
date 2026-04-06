---
name: sessions:harvest
description: Extract valuable insights from recent agent sessions and save them as KB raw notes for compilation into the wiki.
---

# sessions:harvest

Review agent session history and extract insights worth preserving in the knowledge base — decisions made, lessons learned, techniques discovered, research conclusions.

## Trigger

User says "harvest sessions into kb", "extract insights from sessions", "save session learnings to kb", "harvest today's work", or runs `/sessions:harvest [scope]`.

## Instructions

### Step 1 — Check availability

Verify agentsview is running:
```bash
curl -s --max-time 2 http://localhost:8080/api/v1/version
```

If unavailable, tell the user and stop.

### Step 2 — Determine scope

Identify what sessions to harvest from the user's message:

- **By recency**: "today", "this week", "recent" → fetch recent sessions list
- **By topic**: "about authentication", "re: the parser refactor" → search by topic
- **Default** (no qualifier): ask the user to clarify scope

**For recency-based scope:**
```bash
curl -s "http://localhost:8080/api/v1/sessions?limit=20"
```
Filter results to the relevant time window based on `started_at`.

**For topic-based scope:**
```bash
curl -s "http://localhost:8080/api/v1/search?q=TOPIC&limit=20&sort=recency"
```

### Step 3 — Read session messages

For each candidate session (up to 10 to avoid overload), fetch its messages:
```bash
curl -s "http://localhost:8080/api/v1/sessions/SESSION_ID/messages?limit=200"
```

The response contains messages with `role` (user/assistant), `content`, and tool call summaries.

### Step 4 — Identify harvest-worthy content

Read through the session messages and extract content worth capturing in the KB. Look for:

**Worth harvesting:**
- Architectural decisions and their rationale ("we chose X over Y because...")
- Unexpected findings or surprises ("turns out the issue was...")
- Reusable techniques or patterns discovered ("to do X, the approach is...")
- Research conclusions or summaries of external knowledge
- Workflows or procedures figured out through trial and error
- Warnings or gotchas worth remembering

**Skip:**
- Routine back-and-forth clarifications
- Debugging iterations without a meaningful conclusion
- Content already well-represented in the wiki
- Session scaffolding (file listings, status checks, etc.)

### Step 5 — Draft raw note(s)

For each meaningful cluster of insights, draft a note file. Group related insights from multiple sessions into a single note if they form a coherent topic.

File path: `~/knowledge/raw/notes/YYYY-MM-DD-harvest-<slug>.md`

Format:
```markdown
---
title: "Harvested: <topic>"
date: "YYYY-MM-DD"
tags: [tag1, tag2]
status: unprocessed
sources:
  - session:<session_id_1>
  - session:<session_id_2>
---

# <Topic Title>

<Prose capturing the insights — written clearly, not as raw transcript>

## Key Takeaways

- <Takeaway 1>
- <Takeaway 2>

## Context

Harvested from session(s): <session names>, <dates>.
```

Write the prose as distilled knowledge, not as a session transcript. Synthesize and clarify.

### Step 6 — Confirm before writing

Present the user with a summary of what will be written:

```
Ready to write N note(s):

1. ~/knowledge/raw/notes/2024-01-15-harvest-auth-middleware.md
   Topics: auth middleware decisions, session token storage approach

Proceed? (y/n)
```

Only write after confirmation. If the user wants changes, revise first.

### Step 7 — Write and suggest compilation

Write the confirmed notes. Then say:

```
Wrote N note(s) to ~/knowledge/raw/notes/.
Run /kb:compile to compile them into wiki articles.
```

## Key Rules

- **Synthesize, don't transcribe**: write distilled knowledge, not raw session excerpts
- **Confirm before writing**: always show the user what will be written and get approval
- **Small batches**: harvest at most 10 sessions at a time to keep quality high
- **Tag appropriately**: use tags that match existing wiki topic areas when possible
- **Use `status: unprocessed`**: all harvested notes go through the normal `kb:compile` pipeline
