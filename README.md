# agentic-home

A minimal home directory configuration for AI-assisted agentic development. Supports **Claude Code** (primary) and **Codex CLI** (optional).

Clone this repo and run the install script to get:
- Global coding rules agents follow in every session
- Desktop notifications when a session finishes or waits for input (macOS and Linux)
- Session context (date, directory, git status) printed at session start; [agentsview](https://github.com/wesm/agentsview) auto-starts so every session is indexed
- `/resolve-conflicts` skill — guided git conflict resolution
- `/create-pr` and `/update-pr` legacy aliases — forward to canonical `pr:create` / `pr:update` workflows
- A `researcher` subagent for read-only codebase exploration
- `agent-team` script — launch a tmux agent team with one command
- Sensible permission defaults with explicit deny rules for `.env`, SSH keys, and common credential files
- `kb` plugin — personal knowledge base with ingest → compile → query → lint workflow
- `sessions` plugin — search past sessions and harvest insights into the knowledge base
- `pr` plugin — full PR lifecycle (create, review, merge, comment, sync, and more)
- Automatic Claude → Codex skill translation for minimal-overhead cross-tool reuse

## Setup

**1. Install prerequisites**

**macOS** — trigger Xcode Command Line Tools installation (a popup will appear):
```bash
xcode-select --install
```

**Linux (Ubuntu/Debian)** — ensure curl and git are available:
```bash
sudo apt-get install -y curl git
```

**2. Create API key files** so credentials are ready when needed:

```bash
echo 'export ANTHROPIC_API_KEY="sk-ant-..."' > ~/.anthropic.env && chmod 600 ~/.anthropic.env
echo 'export OPENAI_API_KEY="sk-proj-..."'   > ~/.openai.env    && chmod 600 ~/.openai.env
```

**3. Run `agentic-dev-setup.sh`:**

```bash
curl -fsSL https://raw.githubusercontent.com/ghShu/agentic-home/main/agentic-dev-setup.sh | bash
```

The script opens with a prompt:

```
Fresh install? Run full setup (package manager, terminal, dev tools, shell config) [Y/N]
```

- **Y** — installs everything from scratch: package manager (Homebrew on macOS, apt/dnf/pacman on Linux), terminal (Ghostty on macOS), oh-my-zsh, Starship, dev tools, Git config, macOS system defaults (macOS only), Node, Claude Code, then clones this repo and runs `install.sh`.
- **N** — skips straight to Node → Claude Code → clone + `install.sh`. Use this on an existing system that already has the basics.

If the script is interrupted, resume from any step:

```bash
bash ~/agentic-dev-setup.sh --from install_claude_code
```

**4. Start a new shell session** to pick up the configuration, then run `claude` to complete authentication.

## First-time login

**Claude Code** handles auth interactively on first run — no extra steps needed.

**Codex** is logged in automatically by `install.sh` if `~/.openai.env` exists. To log in manually:

```bash
printenv OPENAI_API_KEY | codex login --with-api-key
```

After login, both tools need no environment setup — just `claude` or `codex`.

## Update

```bash
cd ~/dev/agentic-home
git pull
```

Most config updates take effect immediately via symlinks. For rendered machine-local templates (`~/.claude/settings.json`, `~/.codex/config.toml`), re-run `install.sh` after template changes.

## What gets installed

| Repo file | Installed to | Purpose |
|-----------|-------------|---------|
| `CLAUDE.md` | `~/CLAUDE.md` | Global instructions for Claude Code ([docs](https://docs.anthropic.com/en/docs/claude-code/memory)) |
| `AGENTS.md` | `~/AGENTS.md` | Cross-agent context file ([agents.md spec](https://agents.md/)) |
| `claude/settings.json` | `~/.claude/settings.json` | Claude Code config template rendered at install time with machine-local paths ([docs](https://docs.anthropic.com/en/docs/claude-code/settings)) |
| `claude/hooks/session-start.sh` | `~/.claude/hooks/` | Prints context at session start ([hooks docs](https://docs.anthropic.com/en/docs/claude-code/hooks)) |
| `claude/hooks/notify.sh` | `~/.claude/hooks/` | Desktop notification on stop/idle (macOS via osascript, Linux via notify-send) |
| `claude/skills/resolve-conflicts/` | `~/.claude/skills/` | `/resolve-conflicts` slash command ([skills docs](https://docs.anthropic.com/en/docs/claude-code/skills)) |
| `claude/skills/create-pr/` | `~/.claude/skills/` | `/create-pr` slash command — create PR, creating remote repo first if needed |
| `claude/skills/update-pr/` | `~/.claude/skills/` | `/update-pr` slash command — push commits and regenerate PR description |
| `claude/agents/researcher.md` | `~/.claude/agents/` | Read-only researcher subagent ([subagents docs](https://docs.anthropic.com/en/docs/claude-code/sub-agents)) |
| `bin/agent-team` | `~/bin/agent-team` | Launch a tmux agent team session |
| `codex/instructions.md` | `~/.codex/instructions.md` | Codex global system prompt |
| `codex/config.toml` | `~/.codex/config.toml` | Codex config template rendered at install time with machine-local trust paths |
| `bin/sync-codex-from-claude` + `codex/generated/skills/` | `~/.agents/skills/*` | Generated Codex skills translated from `claude/skills/` and `claude/plugins/*/skills/` |

## Codex translation sync

To keep Codex skills in sync with Claude skills/plugins, run:

```bash
~/dev/agentic-home/bin/sync-codex-from-claude
```

This regenerates:
- `codex/generated/skills/` (Codex-ready `SKILL.md` directories)
- `codex/generated/plugins/` (translated plugin layout)
- `codex/generated/MAPPING.md` (source-to-generated mapping)

`install.sh` runs this sync automatically (when Codex is installed) and symlinks generated skills into `~/.agents/skills/`.

Validate translation coverage and generated artifacts:

```bash
~/dev/agentic-home/bin/test-codex-skill-sync
```

Validate portability/template rendering:

```bash
~/dev/agentic-home/bin/test-portable-configs
```

Validate installer idempotency in an isolated temporary HOME:

```bash
~/dev/agentic-home/bin/test-install-idempotent
```

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

If tmux isn't installed: `brew install tmux` (macOS) or `sudo apt-get install tmux` (Ubuntu/Debian)

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

## Knowledge base

The `kb` plugin manages a personal wiki at `$KB_HOME` (default `~/knowledge/`, set during `install.sh`). Source material lives in `raw/` and gets compiled into structured wiki articles in `wiki/` by an LLM.

| Skill | Trigger | What it does |
|-------|---------|--------------|
| `/kb:ingest` | "ingest", "add to kb", URL | Saves source document to `$KB_HOME/raw/` with front matter and downloaded images |
| `/kb:compile` | "compile", "update wiki" | Processes `raw/` into wiki articles via the `wiki-editor` subagent |
| `/kb:query` | "kb: \<question\>" | Answers questions grounded strictly in wiki content, with citations |
| `/kb:lint` | "lint my kb" | Health checks → `wiki/_meta/lint-report.md` |
| `/kb:note` | "note:", quick capture | Saves a quick note to `$KB_HOME/raw/notes/` without a source URL |

Conventions are documented in `$KB_HOME/KNOWLEDGE.md` (seeded from `claude/plugins/kb/seed/KNOWLEDGE.md.seed`).

## Session history with agentsview

[agentsview](https://github.com/wesm/agentsview) auto-starts at the beginning of every Claude Code session and indexes all sessions into a local SQLite database with full-text search. Browse the UI at **http://localhost:8080** or use the `sessions` plugin skills:

| Skill | Trigger | What it does |
|-------|---------|--------------|
| `/sessions:search` | "search sessions for X" | Searches past session history via agentsview's REST API and returns formatted results |
| `/sessions:harvest` | "harvest sessions into kb" | Extracts insights from recent sessions and saves them as KB raw notes for compilation |

`/kb:query` also cross-references session history automatically — if you ask the KB a question, it surfaces relevant past discussions alongside wiki articles.

## Customization

**Edit `CLAUDE.md`** to change the global coding rules Claude follows.

**Add skills** by creating `claude/skills/your-skill/SKILL.md` and re-running `install.sh`.

**Add subagents** by creating `claude/agents/your-agent.md` and re-running `install.sh`.

**Enable Agent Teams** — see the [Multi-agent](#multi-agent) section above.

**Adjust permissions** in `claude/settings.json` under `"permissions"` → `"deny"`.

## Structure

```
agentic-home/
├── agentic-dev-setup.sh                   # Bootstrap script: macOS + Linux (package manager → Claude Code → install.sh)
├── install.sh                     # Symlink config into ~/.claude/, ~/bin/, etc.
├── CLAUDE.md                      # Global Claude Code instructions
├── AGENTS.md                      # Cross-agent home directory guide
├── bin/
│   └── agent-team                 # Launch a tmux agent team session
├── claude/
│   ├── settings.json              # Claude Code configuration
│   ├── hooks/
│   │   ├── session-start.sh       # Session context printer
│   │   └── notify.sh              # Desktop notification hook (macOS + Linux)
│   ├── skills/
│   │   ├── resolve-conflicts/     # /resolve-conflicts skill
│   │   ├── create-pr/             # /create-pr skill
│   │   └── update-pr/             # /update-pr skill
│   ├── plugins/
│   │   ├── pr/                    # pr:checkout, pr:create, pr:review, …
│   │   ├── kb/                    # kb:ingest, kb:compile, kb:lint, kb:query, kb:note
│   │   └── sessions/              # sessions:search, sessions:harvest
│   └── agents/
│       └── researcher.md          # Read-only research subagent
└── codex/
    ├── instructions.md            # Codex system prompt
    └── config.toml                # Codex configuration
```
