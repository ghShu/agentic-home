#!/usr/bin/env bash
# SessionStart hook — prints context at the beginning of each Claude Code session

echo "=== Session Start ==="
echo "Date: $(date)"
echo "Working dir: $(pwd)"

# Show git status if inside a repo
if git rev-parse --is-inside-work-tree &>/dev/null 2>&1; then
  echo "Git branch: $(git branch --show-current 2>/dev/null)"
  echo "Git status:"
  git status --short 2>/dev/null | head -20
fi

echo "===================="
