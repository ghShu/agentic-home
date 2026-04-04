#!/usr/bin/env bash
# install.sh — Set up agentic home directory configuration
#
# Creates symlinks from ~/.claude/, ~/.codex/, and ~/ to files in this repo.
# Safe to run multiple times (idempotent). Backs up any existing files before
# replacing them.
#
# Usage: bash install.sh

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$HOME/.agentic-home-backup-$(date +%Y%m%d_%H%M%S)"
BACKED_UP=()
LINKED=()
SKIPPED=()

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log()    { echo -e "${BLUE}  →${NC} $*"; }
ok()     { echo -e "${GREEN}  ✓${NC} $*"; }
warn()   { echo -e "${YELLOW}  !${NC} $*"; }

# Create a symlink, backing up any existing file/symlink first
symlink() {
  local src="$1"
  local dst="$2"

  # If already correctly symlinked, skip
  if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
    SKIPPED+=("$dst")
    return
  fi

  # Back up existing file (not a symlink to our src)
  if [ -e "$dst" ] || [ -L "$dst" ]; then
    mkdir -p "$BACKUP_DIR"
    mv "$dst" "$BACKUP_DIR/"
    BACKED_UP+=("$dst")
  fi

  # Create parent directory if needed
  mkdir -p "$(dirname "$dst")"

  ln -s "$src" "$dst"
  LINKED+=("$dst → $src")
}

echo ""
echo "Installing agentic-home configuration..."
echo "Repo: $REPO_DIR"
echo ""

# --- Create directories ---
log "Creating directories..."
mkdir -p "$HOME/.claude/hooks"
mkdir -p "$HOME/.claude/skills"
mkdir -p "$HOME/.claude/agents"
mkdir -p "$HOME/.codex"
mkdir -p "$HOME/bin"

# --- Symlink top-level files ---
log "Linking CLAUDE.md and AGENTS.md..."
symlink "$REPO_DIR/CLAUDE.md"   "$HOME/CLAUDE.md"
symlink "$REPO_DIR/AGENTS.md"   "$HOME/AGENTS.md"

# --- bin scripts ---
log "Linking bin scripts..."
for bin_file in "$REPO_DIR/bin"/*; do
  [ -f "$bin_file" ] || continue
  chmod +x "$bin_file"
  symlink "$bin_file" "$HOME/bin/$(basename "$bin_file")"
done

# --- Claude Code settings ---
log "Linking Claude Code settings..."
symlink "$REPO_DIR/claude/settings.json" "$HOME/.claude/settings.json"

# --- Hooks ---
log "Linking hooks..."
symlink "$REPO_DIR/claude/hooks/session-start.sh" "$HOME/.claude/hooks/session-start.sh"
symlink "$REPO_DIR/claude/hooks/notify.sh"         "$HOME/.claude/hooks/notify.sh"

# Make hooks executable
chmod +x "$REPO_DIR/claude/hooks/session-start.sh"
chmod +x "$REPO_DIR/claude/hooks/notify.sh"

# --- Skills ---
log "Linking skills..."
for skill_dir in "$REPO_DIR/claude/skills"/*/; do
  skill_name="$(basename "$skill_dir")"
  symlink "$skill_dir" "$HOME/.claude/skills/$skill_name"
done

# --- Agents ---
log "Linking agents..."
for agent_file in "$REPO_DIR/claude/agents"/*.md; do
  [ -e "$agent_file" ] || continue
  agent_name="$(basename "$agent_file")"
  symlink "$agent_file" "$HOME/.claude/agents/$agent_name"
done

# --- Codex (only if installed) ---
if command -v codex &>/dev/null; then
  log "Linking Codex configuration..."
  symlink "$REPO_DIR/codex/instructions.md" "$HOME/.codex/instructions.md"
  symlink "$REPO_DIR/codex/config.toml"     "$HOME/.codex/config.toml"

  # Log in with API key from ~/.openai.env if not already logged in
  if codex login status 2>&1 | grep -q "API key"; then
    ok "Codex already logged in"
  elif [ -f "$HOME/.openai.env" ]; then
    log "Logging in to Codex with API key from ~/.openai.env..."
    OPENAI_KEY=$(grep -E 'OPENAI_API_KEY=' "$HOME/.openai.env" | cut -d'"' -f2 | tr -d "'" | tr -d ' ')
    if [ -n "$OPENAI_KEY" ]; then
      echo "$OPENAI_KEY" | codex login --with-api-key && ok "Codex logged in"
    else
      warn "OPENAI_API_KEY not found in ~/.openai.env — run: printenv OPENAI_API_KEY | codex login --with-api-key"
    fi
  else
    warn "Codex found but no ~/.openai.env — run: printenv OPENAI_API_KEY | codex login --with-api-key"
  fi
else
  log "Codex not installed — skipping Codex setup"
  log "To install: https://github.com/openai/codex"
fi

# --- Knowledge base skeleton ---
log "Ensuring knowledge base skeleton..."
KB="$HOME/knowledge"
mkdir -p "$KB/raw/articles" "$KB/raw/papers" "$KB/raw/images"
mkdir -p "$KB/wiki/_meta"
mkdir -p "$KB/outputs/reports" "$KB/outputs/slides"

[ ! -f "$KB/KNOWLEDGE.md" ] && cp "$REPO_DIR/knowledge/KNOWLEDGE.md.seed" "$KB/KNOWLEDGE.md" && ok "Seeded ~/knowledge/KNOWLEDGE.md"
[ ! -f "$KB/wiki/_index.md" ] && cp "$REPO_DIR/knowledge/wiki-index.md.seed" "$KB/wiki/_index.md" && ok "Seeded ~/knowledge/wiki/_index.md"

# --- Summary ---
echo ""
echo "Done."
echo ""

if [ ${#LINKED[@]} -gt 0 ]; then
  echo -e "${GREEN}Linked:${NC}"
  for item in "${LINKED[@]}"; do
    ok "$item"
  done
  echo ""
fi

if [ ${#SKIPPED[@]} -gt 0 ]; then
  echo "Already linked (skipped): ${#SKIPPED[@]} file(s)"
fi

if [ ${#BACKED_UP[@]} -gt 0 ]; then
  warn "Backed up ${#BACKED_UP[@]} existing file(s) to: $BACKUP_DIR"
  for item in "${BACKED_UP[@]}"; do
    warn "  $item"
  done
  echo ""
fi

echo "Start a new Claude Code session to pick up the configuration."
