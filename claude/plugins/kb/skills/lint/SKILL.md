---
name: kb:lint
description: Run health checks over ~/knowledge/. Detects orphaned articles, broken links, unprocessed/malformed raw files, unreferenced images, unresolved curated references, stubs, islands (no backlinks), and duplicate concepts. Writes a report to wiki/_meta/lint-report.md.
---

# kb:lint

Run structural and content health checks over the wiki and produce a lint report.

## Trigger

User says: "lint", "check my kb", "health check", "check the wiki", or runs `/kb:lint`.

## Instructions

### Step 1 — Read conventions and index

1. Read `~/knowledge/KNOWLEDGE.md`
2. Read `~/knowledge/wiki/_index.md` — this is the authoritative list of all expected articles

### Step 2 — Structural checks

**A. Index completeness**
- Glob `~/knowledge/wiki/**/*.md` (excluding `_index.md`, `_meta/`, and topic `index.md` files)
- For each wiki article found on disk: verify it has an entry in `_index.md`
- For each entry in `_index.md`: verify the linked file exists on disk
- Flag: articles on disk not in index (orphans), and index entries with no file (dead links)

**B. Topic index completeness**
- For each topic directory in `wiki/`: verify a `index.md` exists
- Flag: topic directories missing their `index.md`

**C. Front matter validity**
- For each wiki article: verify required front matter fields exist (`title`, `status`, `sources`)
- Flag: articles missing required fields

### Step 3 — Content health checks

**D. Stubs and incomplete articles**
- Flag: articles with `status: stub` or `status: draft`
- Flag: articles containing "TODO" or "[to compile]" in their body

**E. Islands (no backlinks)**
- For each wiki article: check if any other wiki file contains `[[topic/concept]]` linking to it
- Flag: articles with zero inbound wikilinks (islands — disconnected from the graph)

**F. Unprocessed inbox**
- Glob `~/knowledge/raw/**/*.md`
- Flag: any raw file with `status: unprocessed` (sitting in inbox, not yet compiled)
- Flag: any raw `.md` file with no YAML front matter (manually dropped — needs front matter before compiling)
- Flag: any raw `.md` file with front matter but missing the `status` field (will be treated as unprocessed by compile, but should be explicit)

**G-img. Unreferenced images**
- Glob `~/knowledge/raw/images/**/*` for all image files (`.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`, `.webp`)
- For each image: search `~/knowledge/wiki/**/*.md` for any reference to that filename
- Flag: images in `raw/images/` not referenced by any wiki article (orphaned assets)

**H. Unresolved curated references**
- Glob `~/knowledge/raw/**/*.md` and read each file's `references.curated` front matter list
- For each curated reference URL: check if a raw file with that `source:` URL already exists
- Flag: curated references not yet ingested (known-valuable sources sitting uningestd)
- Skip `in_text` references — only curated ones are flagged

**G. Potential duplicates**
- Look for pairs of articles with very similar titles or overlapping content summaries in `_index.md`
- Flag: likely duplicates as candidates for merging (do not auto-merge)

### Step 4 — Generate investigation suggestions

Before writing the report, derive forward-looking suggestions:

**Dead wikilinks → research candidates**
- Collect all `[[topic/concept]]` patterns across wiki articles
- Cross-reference against existing files — any link with no target is a knowledge gap
- For each dead wikilink: suggest "Consider researching `concept` — referenced in wiki/topic/source.md"

**Stubs → quick wins**
- Articles with `status: stub` that have at least one inbound link are high-value targets
- Suggest ingesting more sources to fill them out

**Domain gaps**
- Read `KNOWLEDGE.md` "Domain Topics" section — compare expected topic clusters against what exists in `wiki/`
- Flag expected topics that have no articles yet

**Unresolved curated references → ready-to-run commands**
- For each curated reference not yet ingested, generate a ready-to-run command:
  `/kb:ingest <url>  # "<title>" — curated in raw/articles/slug.md`

### Step 4b — Write lint report

Write to `~/knowledge/wiki/_meta/lint-report.md`:

```markdown
---
date: "YYYY-MM-DD"
articles_checked: N
issues_found: M
---

# Wiki Lint Report — YYYY-MM-DD

## Summary
- Articles checked: N
- Issues found: M (X critical, Y warnings)

## Critical Issues
### Orphaned articles (on disk, not in _index.md)
- wiki/topic/concept.md

### Dead index entries (in _index.md, file missing)
- [[topic/missing-concept]]

### Missing topic indexes
- wiki/topic/ has no index.md

## Warnings
### Unprocessed inbox items
- raw/articles/YYYY-MM-DD-slug.md (status: unprocessed)

### Raw files missing front matter (manually dropped)
- raw/articles/some-file.md (no front matter — run /kb:compile to auto-add)

### Raw files missing status field
- raw/articles/some-file.md (has front matter but no status field)

### Unreferenced images
- raw/images/diagram.png (not referenced by any wiki article)

### Unresolved curated references
- "Paper Title" (https://example.com/paper) — curated in raw/articles/YYYY-MM-DD-slug.md, not yet ingested
  → run: /kb:ingest https://example.com/paper

### Stubs / incomplete articles
- wiki/topic/concept.md (status: stub)

### Islands (no inbound links)
- wiki/topic/concept.md

### Missing front matter fields
- wiki/topic/concept.md (missing: sources)

## Suggestions
### Potential duplicates (review for merging)
- wiki/topic/concept-a.md ↔ wiki/topic/concept-b.md

### Articles with no See Also section
- wiki/topic/concept.md

## Suggested Next Actions
### Research candidates (dead wikilinks)
- `concept-name` — referenced in wiki/topic/article.md but has no article yet
  → /kb:ingest <search-query or URL if known>

### Sources to ingest (unresolved curated references)
- /kb:ingest https://example.com/paper  # "Paper Title" — curated in raw/articles/YYYY-MM-DD-slug.md

### Domain gaps (expected topics with no articles)
- `agentic-development/context-management` — expected per domain schema, no articles yet
  → ingest sources or run /kb:note to capture what you know

### Stubs worth expanding
- wiki/topic/concept.md — has N inbound links, worth fleshing out
```

### Step 5 — Append to log

Append an entry to `~/knowledge/wiki/log.md`:

```
## [YYYY-MM-DD] lint | N articles, X critical, Y warnings
Report: wiki/_meta/lint-report.md
```

### Step 6 — Print summary

Print a short summary to the user:
```
Wiki lint complete.
  Articles checked: N
  Critical issues: X
  Warnings: Y
  Suggested actions: Z

Full report: ~/knowledge/wiki/_meta/lint-report.md
```

If there are zero issues: say so clearly — a clean wiki is the goal.
