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

# Ensure agentsview is running, persisting the port to /tmp/agentsview.port
if command -v agentsview &>/dev/null; then
  AGENTSVIEW_PORT=""
  # Check if already running on any port in range 8080-8099
  # Use -f so curl fails on 4xx/5xx — avoids false positives from other servers
  for _port in $(seq 8080 8099); do
    if curl -sf --max-time 1 "http://localhost:${_port}/api/v1/version" >/dev/null 2>&1; then
      AGENTSVIEW_PORT=$_port
      break
    fi
  done
  if [ -z "$AGENTSVIEW_PORT" ]; then
    # Find first free port in range
    for _port in $(seq 8080 8099); do
      if ! nc -z localhost "$_port" 2>/dev/null; then
        AGENTSVIEW_PORT=$_port
        break
      fi
    done
    nohup agentsview -no-browser -port "$AGENTSVIEW_PORT" >/tmp/agentsview.log 2>&1 &
    echo "agentsview started → http://localhost:${AGENTSVIEW_PORT}"
  else
    echo "agentsview running → http://localhost:${AGENTSVIEW_PORT}"
  fi
  echo "$AGENTSVIEW_PORT" > /tmp/agentsview.port
fi
