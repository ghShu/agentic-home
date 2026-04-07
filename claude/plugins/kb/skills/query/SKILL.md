---
name: kb:query
description: Answer a question grounded strictly in the compiled wiki. Reads _index.md, uses kbsearch for targeted lookup, reads relevant articles, and responds with citations. Can save output as a report or Marp slideshow.
---

# kb:query

Answer questions using only the content in `$KB_HOME/wiki/`.

## Trigger

User asks a question prefixed with "kb:" or "ask my kb", uses `/kb:query`, or asks something that should be answered from the personal knowledge base rather than general knowledge.

## Usage

```
/kb:query <question>
/kb:query <question> --report     # save answer as a report file
/kb:query <question> --slides     # save answer as a Marp slideshow
/kb:query <question> --file-wiki  # file answer directly into the wiki
```

## Instructions

### Step 0 — Resolve KB path

Run:
```bash
echo "${KB_HOME:-$HOME/knowledge}"
```
Use the output as `$KB_HOME` for all file paths in this skill.
When delegating to wiki-editor, pass `KB_HOME: <resolved-path>` in the context.

### Step 1 — Read conventions

Read `$KB_HOME/KNOWLEDGE.md` briefly to understand the wiki structure.

### Step 2 — Map the wiki

Read `$KB_HOME/wiki/_index.md` in full. This is your map — it lists every article with a one-sentence summary. Do not skip this step.

### Step 3 — Find relevant articles

From the index, identify which topic directories and articles are relevant to the question.

Optionally run `kbsearch <key terms>` to find additional matches:
```bash
kbsearch "term1 term2"
```
The tool returns JSON: `[{"file": "...", "line": N, "snippet": "..."}]`

Read the 5–15 most relevant articles. Do not read the entire wiki unless the question is very broad.

### Step 3b — Cross-reference sessions (optional)

If agentsview is available, search past sessions for relevant discussions:

```bash
AGENTSVIEW_PORT=$(cat /tmp/agentsview.port 2>/dev/null || echo "8080")
curl -s --max-time 2 "http://localhost:${AGENTSVIEW_PORT}/api/v1/search?q=KEY%20TERMS&limit=5"
```

URL-encode the key terms from the query (spaces → `%20`). If the server is unreachable or returns no results, skip this step silently.

If relevant session results exist, include them in the answer as a **"Related session discussions"** section — clearly distinct from wiki content. These capture lived experience (past decisions, debugging context, prior research) that complements the formal wiki.

### Step 4 — Answer

Answer the question grounded strictly in wiki content:
- Cite the specific wiki file for each claim: `(wiki/topic/concept.md)`
- If the answer is not in the wiki, say so explicitly: "This is not covered in the knowledge base."
- Do not supplement with general knowledge unless the user explicitly asks for it
- Do not speculate or extrapolate beyond what the wiki says

### Step 5 — Output format

Default: answer inline in the conversation.

If the user asks to "save", "write a report", or "make slides":

**Report** — write to `$KB_HOME/outputs/reports/YYYY-MM-DD-<slug>.md`:
```markdown
---
title: "Query: <question>"
date: "YYYY-MM-DD"
query: "<original question>"
sources:
  - wiki/topic/concept.md
---

# <Question as title>

<Answer with citations>

## Sources
- [[topic/concept]] — brief note on what was used from this article
```

**Marp slideshow** — write to `$KB_HOME/outputs/slides/YYYY-MM-DD-<slug>.md`:
```markdown
---
marp: true
title: "<title>"
---

# <Title>

---

## <Slide title>

<Content>

---
```

### Step 5b — Offer to file synthesis into the wiki

After generating a non-trivial answer (more than 2–3 sentences, contains useful synthesis), ask the user:

```
File this answer as a wiki article? (y/n)
Suggested location: wiki/<topic>/<concept>.md
```

If the user confirms (or explicitly asked to "file to wiki" / passes `--file-wiki`):
- Use the **wiki-editor** subagent to write the article to `wiki/<topic>/<concept>.md`
- Use `sources: [synthesized]` in the front matter (no raw source backing this article)
- Add an entry in `_index.md` under `## Syntheses`
- These articles compound knowledge the same way ingested sources do

Do **not** suggest kb:ingest for these — synthesized articles go directly to wiki, skipping raw/.

### Step 5c — Append to log

Append an entry to `$KB_HOME/wiki/log.md`:

```
## [YYYY-MM-DD] query | "Question text"
Output: inline
```

Or, if output was saved:
```
## [YYYY-MM-DD] query | "Question text"
Output: report: outputs/reports/YYYY-MM-DD-slug.md
```

Or, if filed to wiki:
```
## [YYYY-MM-DD] query | "Question text"
Output: wiki: wiki/topic/concept.md
```

## Key Rules

- **No hallucination**: if information is not in the wiki, say so. The wiki is the sole source of truth for this skill.
- **Always cite**: every factual claim should reference a specific wiki article
- **Lean on the index**: read `_index.md` before reading individual articles — it tells you what exists
- **Use kbsearch**: for specific term lookups it is faster than reading every article
