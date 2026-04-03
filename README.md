# agentic-home

A minimal home directory configuration for AI-assisted agentic development. Supports **Claude Code** (primary) and **Codex CLI** (optional).

Clone this repo and run the install script to get:
- Global coding rules Claude and other agents follow in every session
- macOS notifications when Claude finishes or waits for input
- Session context (date, directory, git status) printed at session start
- `/resolve-conflicts` skill — guided git conflict resolution
- `/update-pr` skill — push commits and regenerate PR descriptions
- A `researcher` subagent for read-only codebase exploration
- Sensible permission rules (blocks `.env`, SSH keys, credentials, etc.)

## Prerequisites

- [Claude Code](https://claude.ai/code) CLI installed
- macOS (hooks use `osascript` for notifications; Linux users can swap in `notify-send`)
- [Codex CLI](https://github.com/openai/codex) (optional)
- [GitHub CLI (`gh`)](https://cli.github.com/) (optional, needed for `/update-pr`)

## Install

```bash
git clone https://github.com/YOUR_USERNAME/agentic-home ~/dev/agentic-home
bash ~/dev/agentic-home/install.sh
```

Start a new Claude Code session to pick up the configuration.

## Update

```bash
cd ~/dev/agentic-home
git pull
```

Because all config files are symlinked, updates take effect immediately — no re-running the install script needed.

## What gets installed

| Repo file | Installed to | Purpose |
|-----------|-------------|---------|
| `CLAUDE.md` | `~/CLAUDE.md` | Global instructions for Claude Code ([docs](https://docs.anthropic.com/en/docs/claude-code/memory)) |
| `AGENTS.md` | `~/AGENTS.md` | Cross-agent context file ([agents.md spec](https://agents.md/)) |
| `claude/settings.json` | `~/.claude/settings.json` | Claude Code config: permissions, hooks, features ([docs](https://docs.anthropic.com/en/docs/claude-code/settings)) |
| `claude/hooks/session-start.sh` | `~/.claude/hooks/` | Prints context at session start ([hooks docs](https://docs.anthropic.com/en/docs/claude-code/hooks)) |
| `claude/hooks/notify.sh` | `~/.claude/hooks/` | macOS notification on stop/idle |
| `claude/skills/resolve-conflicts/` | `~/.claude/skills/` | `/resolve-conflicts` slash command ([skills docs](https://docs.anthropic.com/en/docs/claude-code/skills)) |
| `claude/skills/update-pr/` | `~/.claude/skills/` | `/update-pr` slash command |
| `claude/agents/researcher.md` | `~/.claude/agents/` | Read-only researcher subagent ([subagents docs](https://docs.anthropic.com/en/docs/claude-code/sub-agents)) |
| `codex/instructions.md` | `~/.codex/instructions.md` | Codex global system prompt |
| `codex/config.toml` | `~/.codex/config.toml` | Codex model and approval mode |

## Customization

**Edit `CLAUDE.md`** to change the global coding rules Claude follows.

**Add skills** by creating `claude/skills/your-skill/SKILL.md` and re-running `install.sh`.

**Add subagents** by creating `claude/agents/your-agent.md` and re-running `install.sh`.

**Enable Agent Teams** (experimental, ~7x token cost):
Add to `claude/settings.json` under `"env"`:
```json
"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
```
See [agent teams docs](https://docs.anthropic.com/en/docs/claude-code/agent-teams).

**Adjust permissions** in `claude/settings.json` under `"permissions"` → `"deny"`.

## Structure

```
agentic-home/
├── install.sh                     # Setup script
├── CLAUDE.md                      # Global Claude Code instructions
├── AGENTS.md                      # Cross-agent home directory guide
├── claude/
│   ├── settings.json              # Claude Code configuration
│   ├── hooks/
│   │   ├── session-start.sh       # Session context printer
│   │   └── notify.sh              # macOS notification hook
│   ├── skills/
│   │   ├── resolve-conflicts/     # /resolve-conflicts skill
│   │   └── update-pr/             # /update-pr skill
│   └── agents/
│       └── researcher.md          # Read-only research subagent
├── codex/
│   ├── instructions.md            # Codex system prompt
│   └── config.toml                # Codex configuration
└── plans/                         # Planning documents
```
