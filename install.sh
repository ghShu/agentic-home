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

# --- Codex ---
log "Linking Codex configuration..."
symlink "$REPO_DIR/codex/instructions.md" "$HOME/.codex/instructions.md"
symlink "$REPO_DIR/codex/config.toml"     "$HOME/.codex/config.toml"

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
