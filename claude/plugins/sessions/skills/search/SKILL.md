---
name: sessions:search
description: Search past agent sessions for relevant discussions, decisions, and context using agentsview's full-text search.
---

# sessions:search

Search your indexed agent session history for past work, decisions, and context.

## Trigger

User says "search sessions for X", "what have I worked on re: X", "find past sessions about X", "did I work on Y before", or runs `/sessions:search [query]`.

## Instructions

### Step 1 — Check availability

Verify agentsview is running:
```bash
curl -s --max-time 2 http://localhost:8080/api/v1/version
```

If it fails, tell the user: "agentsview is not running. Start it with `agentsview -no-browser &` or start a new session (it auto-starts on session begin)."

### Step 2 — Search sessions

Extract the search query from the user's message. URL-encode it and call the search API:
```bash
curl -s "http://localhost:8080/api/v1/search?q=QUERY&limit=10&sort=relevance"
```

URL-encode the query (replace spaces with `%20`, special chars as needed). For multi-word queries, wrap in quotes: `q=%22word1%20word2%22`.

The response is JSON:
```json
{
  "query": "...",
  "results": [
    {
      "session_id": "...",
      "session_name": "...",
      "project": "...",
      "started_at": "2024-01-15T10:30:00Z",
      "content_snippet": "..."
    }
  ],
  "count": N
}
```

### Step 3 — Format and present results

Present results clearly:

```
Found N sessions matching "query":

1. [Session name] — project: foo  (2024-01-15)
   > "...relevant snippet from the session..."

2. [Session name] — project: bar  (2024-01-10)
   > "...relevant snippet..."
```

If count is 0: "No sessions found for that query."

If the user wants to dig into a specific session, fetch its messages:
```bash
curl -s "http://localhost:8080/api/v1/sessions/SESSION_ID/messages?limit=50"
```

## Key Rules

- Always URL-encode the query string before inserting it into the URL
- Label results clearly as session history — not authoritative knowledge, just past context
- The agentsview UI at http://localhost:8080 has richer browsing if the user wants to explore interactively
