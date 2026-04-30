---
name: kb:ingest
description: Ingest a source document (URL, local file, or pasted text) into $KB_HOME/raw/. Downloads images locally to raw/images/ and rewrites references. Extracts outbound reference URLs into front matter. Optionally follows and ingests references when user says "ingest with references" or passes --follow-refs. Never writes to wiki/.
---

# kb:ingest

Save a source document to `$KB_HOME/raw/` so it can be compiled into the wiki later.

## Trigger

User says: "ingest", "add to kb", "add to knowledge base", "clip this", or provides a URL or file path to save.

**Follow-refs mode** is activated when the user says "ingest with references", "ingest and follow links", or passes `--follow-refs`. In this mode, references found in dedicated sections are also ingested (see Step 6b).

## Instructions

### Step 0 — Resolve KB path

Run:
```bash
KB_HOME="${KB_HOME:-$HOME/knowledge}"
echo "$KB_HOME"
[ -d "$KB_HOME" ] || echo "WARNING: $KB_HOME does not exist — run install.sh to create it"
```
Use the output as `$KB_HOME` for all file paths in this skill.

### Step 1 — Read conventions

Read `$KB_HOME/KNOWLEDGE.md` to understand the front matter format and directory structure.

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

- Web articles and blog posts → `$KB_HOME/raw/articles/`
- Research papers, technical reports → `$KB_HOME/raw/papers/`
- Filename format: `YYYY-MM-DD-<slugified-title>.md`
  - Slugify: lowercase, replace spaces and special chars with hyphens, max 60 chars

### Step 5 — Download images

For URL sources, find all image references in the fetched content (`![...](url)` or `<img src="...">`).

For each image URL:
1. Derive a local filename: `<article-slug>-<original-filename>` (e.g. `components-of-a-coding-agent-diagram.png`). If the URL has no clear filename, use `<article-slug>-img-<N>.<ext>`.
2. Download the image to `$KB_HOME/raw/images/` using:
   ```bash
   curl -sL "<image-url>" -o "$KB_HOME/raw/images/<local-filename>"
   ```
3. Rewrite the reference in the article markdown to Obsidian wikilink syntax:
   - Before: `![alt text](https://example.com/diagram.png)`
   - After: `![[components-of-a-coding-agent-diagram.png]]`

Skip images that fail to download (log them as `<!-- image download failed: <url> -->`).
Skip data URIs (`data:image/...`) — leave them as-is.

### Step 6 — Extract references

Scan the article for outbound URLs. Classify them into two buckets:

**Curated references** — URLs appearing in sections with headings like "References", "Further Reading", "Sources", "Bibliography", "Related", or "See Also". These are explicitly recommended by the author.

**In-text links** — all other hyperlinks embedded mid-paragraph. These are supporting evidence, not curated recommendations.

Do **not** include:
- Navigation links, social media links, subscription/newsletter URLs
- URLs already present in `$KB_HOME/raw/` (check `source:` front matter of existing files)
- Image URLs (already handled in Step 5)
- GitHub repo URLs (note them separately as `repos:`)

### Step 6b — Follow references (only in follow-refs mode)

If follow-refs mode is active, ingest each curated reference URL by recursively applying this skill to it — **but without follow-refs** (one level deep only, no recursive chaining).

Skip a reference if:
- It is a PDF (create a stub instead)
- It is paywalled or returns an error (log it as unresolved)
- It has already been ingested (same `source:` URL exists)

Print progress as each reference is ingested:
```
  Following reference 1/N: "Reference Title" → raw/articles/...
```

### Step 7 — Write the file

Write the file with this structure:

```markdown
---
title: "Article Title"
source: "https://original-url.com"
date: "YYYY-MM-DD"
tags: [tag1, tag2]
status: unprocessed
images:
  - raw/images/article-slug-diagram.png
references:
  curated:
    - url: "https://example.com/paper"
      title: "Paper Title"
      section: "Further Reading"
  in_text:
    - url: "https://example.com/def"
      title: "Definition of X"
repos:
  - url: "https://github.com/user/repo"
    title: "Repo Name"
---

<main article content in clean markdown, with local ![[image]] references>
```

Include `references:` always (even if empty lists). This makes unresolved references visible to lint.
Include `images:` front matter list of all successfully downloaded image paths.
Strip all HTML artifacts. Preserve headings, lists, and code blocks.

**Never write anything to `$KB_HOME/wiki/`** — ingest is strictly an inbox operation.

### Step 8 — Append to log

Append an entry to `$KB_HOME/wiki/log.md`. If the file does not exist yet, create it with a header first (see KNOWLEDGE.md for format). Append at the end:

```
## [YYYY-MM-DD] ingest | Article Title
Source: https://original-url.com
Tags: tag1, tag2
Files: raw/articles/YYYY-MM-DD-slug.md (N images)
```

If follow-refs mode ingested multiple articles, list each one:
```
## [YYYY-MM-DD] ingest | Article Title (+ N references)
Source: https://original-url.com
Tags: tag1, tag2
Files: raw/articles/YYYY-MM-DD-slug.md, raw/articles/YYYY-MM-DD-ref1.md, ...
```

### Step 9 — Confirm

Print:
```
Saved: $KB_HOME/raw/articles/YYYY-MM-DD-slug.md
Title: "Article Title"
Tags: tag1, tag2
Images: N downloaded to $KB_HOME/raw/images/
References: N curated, N in-text (run with --follow-refs to ingest curated refs)

Run /kb:compile to integrate into the wiki.
```

If follow-refs mode was active:
```
Saved: $KB_HOME/raw/articles/YYYY-MM-DD-slug.md
Title: "Article Title"
References followed: N/N ingested (M skipped — see above)

Run /kb:compile to integrate all new files into the wiki.
```

## Edge Cases

- **Duplicate**: if a file for this source already exists (same `source:` URL), warn the user and skip rather than overwriting
- **PDF**: create a stub in `raw/papers/` with front matter and `content: "[PDF — compile manually or via Zotero2MD]"` — do not attempt to read binary PDF content
- **Private/paywalled URL**: if the fetch fails, ask the user to paste the content directly
- **Image-only URL**: if the URL points directly to an image file (`.png`, `.jpg`, `.gif`, `.svg`, `.webp`), download it to `$KB_HOME/raw/images/` and create a minimal stub article in `raw/articles/` with the image embedded and `status: unprocessed`
- **Relative image URLs**: resolve relative image paths against the article's base URL before downloading
- **Duplicate images**: if an image filename already exists in `raw/images/`, append `-2`, `-3`, etc. rather than overwriting
