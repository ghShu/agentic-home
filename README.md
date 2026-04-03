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

## First-time login

API keys are stored in provider-specific env files:

| File | Contains |
|------|---------|
| `~/.anthropic.env` | `ANTHROPIC_API_KEY` |
| `~/.openai.env` | `OPENAI_API_KEY` |

**Claude Code** handles auth interactively on first run — no extra steps needed.

**Codex** stores its API key via a one-time login. `install.sh` does this automatically if `~/.openai.env` exists:

```bash
# ~/.openai.env
export OPENAI_API_KEY="sk-proj-..."
```

If you prefer to log in manually:

```bash
printenv OPENAI_API_KEY | codex login --with-api-key
```

After login, both tools are invoked with no environment setup needed — just `claude` or `codex`.

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

## Multi-agent

Claude Code has two distinct multi-agent mechanisms with different setup requirements.

### Custom subagents — works automatically

Subagents defined in `~/.claude/agents/` are available in every session with no extra steps. This repo includes a `researcher` subagent for read-only codebase exploration. Claude invokes it automatically when a task fits.

Add your own by creating `claude/agents/your-agent.md` and re-running `install.sh`.

### Agent teams — requires multiple terminals

Agent teams let multiple Claude Code sessions collaborate: one orchestrator delegates tasks, workers claim and execute them in parallel. This requires the feature flag and intentional setup.

**Step 1 — enable the feature flag** in `claude/settings.json`:

```json
"env": {
  "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
}
```

Note: agent teams cost ~7x tokens vs a single session. Only worthwhile for genuinely parallelisable work.

**Step 2 — start a team** using one of the methods below.

---

#### Option A: tmux (recommended)

This repo includes an `agent-team` script (installed to `~/bin/`) that creates a tmux session with one orchestrator pane and N worker panes, all running `claude` in your project directory.

```bash
cd ~/your-project

agent-team        # orchestrator + 2 workers (default)
agent-team 3      # orchestrator + 3 workers
agent-team --attach  # re-attach to an existing session
```

The session layout looks like this (tiled, 3 workers shown):

```
┌─────────────────┬─────────────────┐
│  orchestrator   │    worker-1     │
│                 │                 │
├─────────────────┼─────────────────┤
│    worker-2     │    worker-3     │
│                 │                 │
└─────────────────┴─────────────────┘
```

Use `Ctrl-b` then arrow keys to move between panes. Quit with `Ctrl-b d` to detach (sessions persist) or close all panes to end the session.

If tmux isn't installed: `brew install tmux`

---

#### Option B: VS Code / Cursor split terminals

1. Open your project in VS Code or Cursor
2. Open the terminal panel (`Ctrl+`` `)
3. Click the **Split Terminal** icon (or `Cmd+Shift+5`) to create additional terminal panes
4. Run `claude` in each terminal
5. Use the terminal tabs/panes to switch between orchestrator and workers

For a cleaner layout, use the **Terminal: Split Terminal** command from the command palette and arrange panes side by side.

---

#### How the team works

Once multiple `claude` sessions are running in the same project:

1. Tell the **orchestrator** session what you want built
2. The orchestrator breaks the work into tasks and posts them to a shared queue
3. Each **worker** session picks up tasks, executes them, and reports back
4. The orchestrator synthesises the results

Workers do not need any special instructions — they self-identify and claim tasks automatically once the feature flag is on.

---

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
├── bin/
│   └── agent-team                 # Launch a tmux agent team session
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
└── codex/
    ├── instructions.md            # Codex system prompt
    └── config.toml                # Codex configuration
```
