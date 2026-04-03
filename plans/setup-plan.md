# Plan: Agentic Development Home Directory Setup

## Context

The user wants to configure their home directory as a productive environment for AI-assisted agentic development, supporting Claude Code primarily (and optionally Codex). A reference setup exists at `~/dev/HomeDir` (from an Instacart engineer's config), but much of it is enterprise/company-specific. This plan extracts the portable, generally useful patterns and adapts them for personal use.

The result will be a **public shareable repo** (`~/dev/agentic-home`) that anyone can clone and run a single install script to set up their own home directory for agentic development. Think of it as a minimal, focused dotfiles repo specifically for AI coding agents — simpler and more approachable than a full-blown personal dotfiles repo.

**Current state**: Claude Code is installed and running with no custom configuration. No settings.json, no hooks, no skills, no CLAUDE.md.

**Repo name**: `agentic-home` — preferred over `agent-home` to avoid confusion with real-estate agent apps, and clearly signals "home directory setup for agentic development."

**Note on skills location**: Skills (custom slash commands) are stored in `~/.claude/skills/<skill-name>/SKILL.md`. The `~/.agents/` directory seen in the reference setup is a separate runtime registry used by the multi-agent framework — not something we create manually.

---

## What We're Creating

### 1. `~/CLAUDE.md` — Global agent instructions (Claude Code reads this in every session)
- Brief development guidelines that apply across all projects
- Reference to `~/AGENTS.md` for extended agent context
- Key rules: run lints after changes, never skip pre-commit hooks, don't commit unless asked

### 2. `~/AGENTS.md` — Multi-agent guide (read by Claude Code, Codex, Gemini CLI, and others)
- Home directory structure explanation
- Key directories, their purposes, search guidance
- Guidelines applicable to any coding agent

### 3. `~/.claude/settings.json` — Claude Code harness configuration
Key sections to configure:
- **Permissions**: sensible allow/deny rules (block `.env`, `.pem`, `.key`, SSH keys, credential files)
- **Feature flags**: `alwaysThinkingEnabled`, `ENABLE_TOOL_SEARCH`, agent teams opt-in (commented out)
- **Hooks** (4 lifecycle events): `SessionStart`, `PreToolUse`, `Stop`, `Notification`
- **Model**: default to sonnet

### 4. `~/.claude/hooks/` — Hook scripts
- `notify.sh` — macOS `osascript` notification for session stop/idle
- `session-start.sh` — lightweight context printer (date, cwd, git status)

### 5. `~/.claude/skills/` — Custom slash commands
- `resolve-conflicts/SKILL.md` — git conflict resolution guide
- `update-pr/SKILL.md` — push commits and update PR description

### 6. `~/.claude/agents/` — Custom subagent definitions
- One example subagent to demonstrate the pattern

### 7. `~/.codex/` — Codex CLI configuration
- `instructions.md` — system prompt mirroring CLAUDE.md
- `config.toml` — model and approval mode

### 8. `~/bin/` — Personal scripts directory (already in PATH)

---

## Repo Structure: `~/dev/agentic-home`

```
~/dev/agentic-home/
├── README.md                      # What this is, prerequisites, quickstart
├── install.sh                     # One-shot setup script
├── plans/                         # Planning documents (this file lives here too)
├── CLAUDE.md                      # → ~/CLAUDE.md
├── AGENTS.md                      # → ~/AGENTS.md
├── claude/
│   ├── settings.json              # → ~/.claude/settings.json
│   ├── hooks/
│   │   ├── notify.sh              # macOS notification hook
│   │   └── session-start.sh       # Session context printer
│   ├── skills/
│   │   ├── resolve-conflicts/SKILL.md
│   │   └── update-pr/SKILL.md
│   └── agents/
│       └── example-researcher.md  # Example custom subagent
└── codex/
    ├── instructions.md            # → ~/.codex/instructions.md
    └── config.toml                # → ~/.codex/config.toml
```

### `install.sh` behavior
1. Creates `~/.claude/hooks/`, `~/.claude/skills/`, `~/.claude/agents/`, `~/.codex/`, `~/bin/` if missing
2. Symlinks each config file to its target home location (backs up any existing files)
3. Makes hook scripts executable
4. Prints a summary of what was done
5. Idempotent — safe to run multiple times

Uses symlinks (not copies) so `git pull` in `~/dev/agentic-home` immediately reflects everywhere.

---

## Critical Files to Create (in `~/dev/agentic-home/`)

| Repo file | Symlinks to | Why needed | Docs |
|-----------|------------|------------|------|
| `CLAUDE.md` | `~/CLAUDE.md` | Global persistent instructions — Claude reads this at the start of every session from any project, letting you set coding rules once for all work | [Memory](https://docs.anthropic.com/en/docs/claude-code/memory) |
| `AGENTS.md` | `~/AGENTS.md` | Open standard context file read by Codex, Gemini CLI, and other agents; Claude Code also reads it. Describes home dir layout and cross-agent rules | [agents.md spec](https://agents.md/) |
| `claude/settings.json` | `~/.claude/settings.json` | Core harness config: permissions (allow/deny), hooks registration, feature flags, default model. Without this Claude has no guardrails or automation | [Settings](https://docs.anthropic.com/en/docs/claude-code/settings) |
| `claude/hooks/notify.sh` | `~/.claude/hooks/notify.sh` | macOS notification when Claude finishes or goes idle — fired by `Stop` and `Notification` hooks in settings.json | [Hooks guide](https://docs.anthropic.com/en/docs/claude-code/hooks) |
| `claude/hooks/session-start.sh` | `~/.claude/hooks/session-start.sh` | Prints date, cwd, git status at session start so Claude has immediate context — fired by `SessionStart` hook | [Hooks guide](https://docs.anthropic.com/en/docs/claude-code/hooks) |
| `claude/skills/resolve-conflicts/SKILL.md` | `~/.claude/skills/resolve-conflicts/SKILL.md` | Custom `/resolve-conflicts` slash command — injects a detailed conflict-resolution guide into context on demand | [Skills](https://docs.anthropic.com/en/docs/claude-code/skills) |
| `claude/skills/update-pr/SKILL.md` | `~/.claude/skills/update-pr/SKILL.md` | Custom `/update-pr` slash command — pushes commits and rewrites PR description from full commit history | [Skills](https://docs.anthropic.com/en/docs/claude-code/skills) |
| `claude/agents/example-researcher.md` | `~/.claude/agents/example-researcher.md` | Example custom subagent with restricted tools — demonstrates the pattern for users to create their own | [Subagents](https://docs.anthropic.com/en/docs/claude-code/sub-agents) |
| `codex/instructions.md` | `~/.codex/instructions.md` | Codex system prompt — equivalent of CLAUDE.md for OpenAI Codex CLI; same rules, different agent | [Codex CLI](https://github.com/openai/codex) |
| `codex/config.toml` | `~/.codex/config.toml` | Codex model selection and approval mode (e.g. `auto-edit`) | [Codex CLI](https://github.com/openai/codex) |
| `install.sh` | (runs directly) | Bootstrap script — idempotent, creates dirs and symlinks, makes hooks executable | — |
| `README.md` | (repo docs) | Quickstart for new users; prerequisites and what install does | — |
| `plans/` | (repo docs) | Planning documents for this repo's own development; this plan file lives here | — |

---

## Multi-Agent / Agent Teams Support

Claude Code has two distinct multi-agent mechanisms, both supported by this setup:

### 1. Custom Subagents (stable) — in scope
Custom subagents live in `~/.claude/agents/` (mapped from `claude/agents/` in the repo). Each is a Markdown file with a name, description, and system prompt. Claude invokes them via the Agent tool or explicitly by name. Built-in agents (Explore, Plan, General-purpose) are always available without any config.
- Docs: [Create custom subagents](https://docs.anthropic.com/en/docs/claude-code/sub-agents)

### 2. Agent Teams (experimental) — opt-in
Multiple Claude Code sessions work as a peer-to-peer team: one leads, others claim tasks from a shared list and communicate directly. ~7x token cost vs a single session, so off by default. We'll include `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` as a commented-out env var in `settings.json` with a cost warning.
- Docs: [Orchestrate teams of Claude Code sessions](https://docs.anthropic.com/en/docs/claude-code/agent-teams)

---

## Settings.json Key Decisions

**Keep from reference:**
- Permission deny rules for sensitive files (`.env`, `.pem`, `.key`, SSH, AWS, k8s configs)
- `alwaysThinkingEnabled: true`
- `ENABLE_TOOL_SEARCH: true`
- Hooks structure

**Remove (Instacart-specific):**
- Bedrock/AI gateway URLs and env vars
- Internal marketplace URL and plugins
- Telemetry to internal Datadog endpoint

**Set safely:**
- `skipDangerousModePermissionPrompt: false` (reference had this on — we keep it off for safety)
- `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` commented out with cost note

---

## Verification

After implementation:
1. `cd ~/dev/agentic-home && bash install.sh` — completes with no errors, lists symlinks created
2. Open a new Claude Code session — `CLAUDE.md` is loaded (Claude references it)
3. Hooks fire: session start prints context; stop/idle sends macOS notification
4. Skill works: type `/resolve-conflicts` — expands to the skill prompt
5. Codex (if installed): `codex` in any dir reads `~/.codex/instructions.md`
6. Permission block: ask Claude to read `~/.ssh/id_rsa` — denied
7. Idempotent: run `install.sh` again — no errors, no duplicate symlinks
