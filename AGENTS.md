# Agentic Home Directory

This file describes the home directory setup for agentic development. It is read by Claude Code, Codex, Gemini CLI, and other coding agents that follow the [agents.md](https://agents.md/) open standard.

## About This Setup

This home directory is configured using [agentic-home](https://github.com/simonw/agentic-home), a minimal dotfiles repo for AI coding agents. Configuration lives in `~/dev/agentic-home/` and is symlinked into place by `install.sh`.

## Key Directories

| Directory | Purpose |
|-----------|---------|
| `~/dev/` | Development projects |
| `~/bin/` | Personal scripts (on PATH) |
| `~/.claude/` | Claude Code configuration (hooks, skills, agents, settings) |
| `~/.codex/` | Codex CLI configuration |
| `~/dev/agentic-home/` | Source of truth for this home directory config |
| `~/knowledge/` | Personal knowledge base (raw sources + LLM-compiled wiki) |

## File Search Guidance

- Use `~/dev/` as the root when searching for projects.
- Avoid scanning `node_modules/`, `.git/`, or build artifact directories — they are large and slow.
- Use `glob` or `grep` with targeted patterns rather than broad recursive searches from `~`.

## Agent Guidelines

- Follow the rules in `~/CLAUDE.md` (or equivalent system prompt).
- Do not read sensitive files: `.env`, `.pem`, `.key`, `~/.ssh/`, `~/.aws/`, `~/.kube/`.
- When working in a specific project, prefer that project's own `CLAUDE.md` or `AGENTS.md` for project-specific rules.
- Prefer asking the user over making assumptions about intent.
- Never mention AI tools, models, or vendors (e.g. "Claude", "Anthropic", "Co-Authored-By") in commit messages.

## Knowledge Base Skills (Claude Code)

Five slash commands manage the personal knowledge base at `~/knowledge/`:

| Skill | Trigger | What it does |
|-------|---------|--------------|
| `/kb:ingest` | "ingest", "add to kb", or a URL | Saves source to `raw/` with front matter and downloaded images |
| `/kb:compile` | "compile", "update wiki" | Processes `raw/` into wiki articles via `wiki-editor` subagent |
| `/kb:query` | "kb: \<question\>" | Answers questions grounded in wiki content, with citations; cross-references agentsview session history |
| `/kb:lint` | "lint my kb", "check my kb" | Health checks → `wiki/_meta/lint-report.md` |
| `/kb:note` | "note:", quick capture | Saves a quick note to `raw/notes/` without a source URL |

The `wiki-editor` subagent (`~/.claude/agents/wiki-editor.md`) handles all writes to `wiki/`.
The `kbsearch` CLI (`~/bin/kbsearch`) provides fast JSON-output term search over the wiki.
Conventions are documented in `~/knowledge/KNOWLEDGE.md`.

## Session History (agentsview)

[agentsview](https://github.com/wesm/agentsview) auto-starts at session begin and indexes all Claude Code sessions into a local SQLite database. Browse the UI at **http://localhost:8080**.

| Skill | Trigger | What it does |
|-------|---------|--------------|
| `/sessions:search` | "search sessions for X" | Full-text search across all past sessions via agentsview REST API |
| `/sessions:harvest` | "harvest sessions into kb" | Extracts insights from recent sessions as KB raw notes for compilation |

## Multi-Agent Features (Claude Code)

- **Custom subagents**: Defined in `~/.claude/agents/`. Each is a Markdown file with a name, description, and system prompt. Claude Code can invoke them via the Agent tool.
- **Agent teams**: Multiple Claude Code sessions can collaborate as a team. Enable with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in `~/.claude/settings.json` (note: ~7x token cost — see [docs](https://docs.anthropic.com/en/docs/claude-code/agent-teams)).

## Codex-Specific Notes

- Codex reads `~/.codex/instructions.md` as its global system prompt.
- Codex also reads `AGENTS.md` files in cascading hierarchy (project → home).
- Model and approval mode are set in `~/.codex/config.toml`.
