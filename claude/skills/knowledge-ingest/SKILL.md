---
name: knowledge-ingest
description: Ingest a source document (URL, local file, or pasted text) into ~/knowledge/raw/. Saves with correct front matter and status: unprocessed. Never writes to wiki/.
---

# Knowledge Ingest

Save a source document to `~/knowledge/raw/` so it can be compiled into the wiki later.

## Trigger

User says: "ingest", "add to kb", "add to knowledge base", "clip this", or provides a URL or file path to save.

## Instructions

### Step 1 — Read conventions

Read `~/knowledge/KNOWLEDGE.md` to understand the front matter format and directory structure.

### Step 2 — Determine source type

- **URL**: fetch the page content, extract the main article body (strip nav, ads, footers, sidebars)
- **Local file path**: read the file directly
- **Pasted text**: use the text as-is

### Step 3 — Derive metadata

From the source content, extract:
- `title`: the article/document title
- `source`: the original URL or file path
- `date`: publication date if visible, otherwise today's date (YYYY-MM-DD)
- `tags`: 2–5 relevant topic tags (lowercase, hyphenated)

### Step 4 — Choose destination and filename

- Web articles and blog posts → `~/knowledge/raw/articles/`
- Research papers, technical reports → `~/knowledge/raw/papers/`
- Filename format: `YYYY-MM-DD-<slugified-title>.md`
  - Slugify: lowercase, replace spaces and special chars with hyphens, max 60 chars

### Step 5 — Write the file

Write the file with this structure:

```markdown
---
title: "Article Title"
source: "https://original-url.com"
date: "YYYY-MM-DD"
tags: [tag1, tag2]
status: unprocessed
---

<main article content in clean markdown>
```

Strip all HTML artifacts. Preserve headings, lists, code blocks, and images references.
For images: note them as `![description](image-url)` — do not download images during ingest.

**Never write anything to `~/knowledge/wiki/`** — ingest is strictly an inbox operation.

### Step 6 — Confirm

Print:
```
Saved: ~/knowledge/raw/articles/YYYY-MM-DD-slug.md
Title: "Article Title"
Tags: tag1, tag2

Run /knowledge-compile to integrate into the wiki.
```

## Edge Cases

- **Duplicate**: if a file for this source already exists (same `source:` URL), warn the user and skip rather than overwriting
- **PDF**: create a stub in `raw/papers/` with front matter and `content: "[PDF — compile manually or via Zotero2MD]"` — do not attempt to read binary PDF content
- **Private/paywalled URL**: if the fetch fails, ask the user to paste the content directly
