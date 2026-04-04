---
name: knowledge-query
description: Answer a question grounded strictly in the compiled wiki. Reads _index.md, uses kbsearch for targeted lookup, reads relevant articles, and responds with citations. Can save output as a report or Marp slideshow.
---

# Knowledge Query

Answer questions using only the content in `~/knowledge/wiki/`.

## Trigger

User asks a question prefixed with "kb:" or "ask my kb", uses `/knowledge-query`, or asks something that should be answered from the personal knowledge base rather than general knowledge.

## Instructions

### Step 1 — Read conventions

Read `~/knowledge/KNOWLEDGE.md` briefly to understand the wiki structure.

### Step 2 — Map the wiki

Read `~/knowledge/wiki/_index.md` in full. This is your map — it lists every article with a one-sentence summary. Do not skip this step.

### Step 3 — Find relevant articles

From the index, identify which topic directories and articles are relevant to the question.

Optionally run `kbsearch <key terms>` to find additional matches:
```bash
kbsearch "term1 term2"
```
The tool returns JSON: `[{"file": "...", "line": N, "snippet": "..."}]`

Read the 5–15 most relevant articles. Do not read the entire wiki unless the question is very broad.

### Step 4 — Answer

Answer the question grounded strictly in wiki content:
- Cite the specific wiki file for each claim: `(wiki/topic/concept.md)`
- If the answer is not in the wiki, say so explicitly: "This is not covered in the knowledge base."
- Do not supplement with general knowledge unless the user explicitly asks for it
- Do not speculate or extrapolate beyond what the wiki says

### Step 5 — Output format

Default: answer inline in the conversation.

If the user asks to "save", "write a report", or "make slides":

**Report** — write to `~/knowledge/outputs/reports/YYYY-MM-DD-<slug>.md`:
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

**Marp slideshow** — write to `~/knowledge/outputs/slides/YYYY-MM-DD-<slug>.md`:
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

After saving, print the file path and suggest filing it back into the wiki with `/knowledge-ingest`.

## Key Rules

- **No hallucination**: if information is not in the wiki, say so. The wiki is the sole source of truth for this skill.
- **Always cite**: every factual claim should reference a specific wiki article
- **Lean on the index**: read `_index.md` before reading individual articles — it tells you what exists
- **Use kbsearch**: for specific term lookups it is faster than reading every article
