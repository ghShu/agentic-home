---
name: kb:note
description: Capture a quick note or observation into $KB_HOME/raw/notes/ without requiring a source URL. Useful for session insights, tool discoveries, prompt patterns, and agentic workflow observations. Gets compiled into the wiki like other raw sources.
---

# kb:note

Save a quick-capture note to `$KB_HOME/raw/notes/` for later compilation into the wiki.

## Trigger

User says: "kb: note", "add a note to my kb", "save this observation", "note to kb", or runs `/kb:note <text>`.

## Instructions

### Step 0 — Resolve KB path

Run:
```bash
echo "${KB_HOME:-$HOME/knowledge}"
```
Use the output as `$KB_HOME` for all file paths in this skill.

### Step 1 — Read conventions

Read `$KB_HOME/KNOWLEDGE.md` briefly to understand the notes front matter format and directory structure.

### Step 2 — Capture the note content

The note content comes from one of:
- **Inline text**: the text following the trigger (`/kb:note <text here>`)
- **Conversation context**: if the user says "save this observation" or similar without inline text, use the most recent relevant content from the conversation
- **Interactive**: if neither is clear, ask: "What would you like to note?"

### Step 3 — Derive metadata

From the note content, derive:
- `title`: a concise descriptive title (not a sentence — a label, e.g. "kbsearch returns empty on new wiki")
- `date`: today's date (YYYY-MM-DD)
- `tags`: 2–4 relevant topic tags (lowercase, hyphenated), drawing from domain topics in KNOWLEDGE.md
  - For agentic development observations: `tool-usage`, `agent-patterns`, `prompt-engineering`, `workflow-patterns`, etc.

### Step 4 — Write the note

**Filename**: `YYYY-MM-DD-<slugified-title>.md` in `$KB_HOME/raw/notes/`
- Slugify: lowercase, replace spaces/special chars with hyphens, max 60 chars
- If a file with the same slug exists, append `-2`, `-3`, etc.

**File format**:

```markdown
---
title: "Note title"
date: "YYYY-MM-DD"
tags: [tag1, tag2]
status: unprocessed
type: note
---

<note content — clean markdown, preserve structure if multi-paragraph>
```

Keep the content as close to the original as possible. Do not paraphrase or summarize — just clean up formatting.

### Step 5 — Append to log

Append an entry to `$KB_HOME/wiki/log.md`. If the file does not exist yet, create it with a header first (see KNOWLEDGE.md for format). Append at the end:

```
## [YYYY-MM-DD] note | Note title
Filed: raw/notes/YYYY-MM-DD-slug.md
Tags: tag1, tag2
```

### Step 6 — Confirm

Print:
```
Noted: $KB_HOME/raw/notes/YYYY-MM-DD-slug.md
Title: "Note title"
Tags: tag1, tag2

Run /kb:compile to integrate into the wiki.
```

## Edge Cases

- **Multi-point note**: if the user provides several observations at once, save them as one note (not multiple files) with a clear title and bulleted list body
- **Duplicate topic**: if a note's content overlaps heavily with an existing wiki article, mention it: "This relates to [[topic/concept]] — compile will merge it in"
- **No content**: if there is genuinely nothing to note, ask the user what they want to capture
