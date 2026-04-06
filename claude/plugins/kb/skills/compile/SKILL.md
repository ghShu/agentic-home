---
name: kb:compile
description: Compile unprocessed raw documents into wiki articles. Reads ~/knowledge/raw/, identifies new/updated sources, creates or updates wiki articles via the wiki-editor subagent, and updates _index.md.
---

# kb:compile

Process unprocessed documents from `~/knowledge/raw/` and integrate them into the wiki.

## Trigger

User says: "compile", "update wiki", "process inbox", "process raw", or runs `/kb:compile`.

## Instructions

### Step 1 — Read conventions and current state

Read both files before doing anything else:
1. `~/knowledge/KNOWLEDGE.md` — conventions, front matter format, article style
2. `~/knowledge/wiki/_index.md` — current state of the wiki (all existing articles)

### Step 2 — Find unprocessed documents

Glob `~/knowledge/raw/**/*.md` and read each file's front matter.

A file is considered **unprocessed** if any of the following are true:
- `status: unprocessed` is set explicitly
- The file has no YAML front matter at all (manually dropped file)
- The file has front matter but no `status` field

A file is **skipped** only if `status: compiled` is explicitly set.

If there are no unprocessed files, print:
```
No unprocessed documents found in ~/knowledge/raw/.
Use /kb:ingest to add new sources, or drop .md files into raw/ directly.
```
And stop.

**Manually dropped files (no front matter):** Before compiling, prepend minimal front matter so the file can be tracked:
```yaml
---
title: "<inferred from filename or first heading>"
source: "local"
date: "<file modification date or today>"
tags: []
status: unprocessed
---
```
Use Edit to add this block at the top of the file, then proceed to compile it normally.

### Step 3 — Plan the compilation

For each unprocessed document:
1. Read its full content
2. Identify which topic cluster(s) it belongs to (refer to existing topic dirs in `wiki/`)
3. Identify which concepts it covers that should become wiki articles
4. Decide: create new article(s), or update existing article(s)?

When a document spans multiple topics: assign it a primary topic, cross-link from others.

### Step 4 — Delegate writes to wiki-editor

For each document, use the **wiki-editor** subagent to:
- Write or update concept article(s) in `wiki/<topic>/<concept>.md`
- Write or update the topic `wiki/<topic>/index.md`
- Update `wiki/_index.md` with new/changed entries

Pass the wiki-editor the following context each time:
- The raw document content
- The current `_index.md`
- The current topic `index.md` (if it exists)
- The current concept article (if it exists, for updates)
- Instructions from `KNOWLEDGE.md`

### Step 5 — Mark raw files as compiled

After each raw document is successfully compiled, update its front matter:
```yaml
status: compiled
```

Use Edit to change only the `status:` line — do not modify the content.

### Step 6 — Append to log

Append an entry to `~/knowledge/wiki/log.md`. If the file does not exist yet, create it with a header first (see KNOWLEDGE.md for format). Append at the end:

```
## [YYYY-MM-DD] compile | N docs processed
  - raw/articles/YYYY-MM-DD-slug.md → wiki/topic/concept.md (new)
  - raw/articles/YYYY-MM-DD-slug2.md → wiki/topic/concept2.md (updated)
```

### Step 7 — Print summary

```
Compiled N document(s):
  ✓ raw/articles/YYYY-MM-DD-slug.md → wiki/topic/concept.md (new)
  ✓ raw/articles/YYYY-MM-DD-slug2.md → wiki/topic/concept2.md (updated)

Wiki now has X articles across Y topics.
Run /kb:lint to check for issues.
```

## Key Rules

- Never delete or truncate content in existing wiki articles — only add or update
- Never modify `raw/` content beyond updating the `status:` front matter field
- If a concept already has a wiki article, merge new information in — do not create a duplicate
- New topic directories are fine to create if no existing topic is a good fit
