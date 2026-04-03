#!/usr/bin/env bash
# Claude Code notification hook — sends a macOS notification
# Usage: notify.sh [stop|idle]

MODE="${1:-stop}"

case "$MODE" in
  stop)
    TITLE="Claude Code"
    MESSAGE="Session finished"
    ;;
  idle)
    TITLE="Claude Code"
    MESSAGE="Waiting for your input"
    ;;
  *)
    TITLE="Claude Code"
    MESSAGE="$MODE"
    ;;
esac

# macOS notification via osascript
if command -v osascript &>/dev/null; then
  osascript -e "display notification \"$MESSAGE\" with title \"$TITLE\" sound name \"Ping\""
fi
