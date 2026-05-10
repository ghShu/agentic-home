---
name: slack:summary
description: Read and summarize Slack messages to surface follow-up items. Use when the user asks to check Slack, catch up on messages, find action items from Slack, or wants a summary of unread Slack messages.
argument-hint: "[channel-filter] [days-back]"
allowed-tools: ["Bash", "Read"]
user-invocable: true
---

# slack:summary

Read recent Slack messages and surface anything the user needs to follow up on.
Authenticates via Chrome cookies — no MCP server or bot token needed.

## Arguments

The user may optionally provide:
- A channel name filter (e.g., "pme", "ds", "prj-") — substring match
- A timeframe (e.g., "last 3 days", "today") — defaults to 3 days
- A search query (e.g., "messages I wrote today")
- Specific channel names or IDs

## CLI Reference

All commands go through a single binary, `slack_cmd`, installed in `~/bin/`
by `install.sh`:

| Command | Description |
|---------|-------------|
| `slack_cmd summary <filter> [days]` | List matching channels + fetch all messages (one shot) |
| `slack_cmd channels [filter]` | List channels (JSON), optionally filtered by name |
| `slack_cmd messages <ch_ids> [days]` | Fetch messages + threads from comma-separated channel IDs |
| `slack_cmd thread <ch_id> <thread_ts>` | Fetch a single thread by channel ID and thread timestamp |
| `slack_cmd search "<query>" [count]` | Search messages using Slack search syntax |

### Examples

```bash
slack_cmd summary pme 3                          # PME channels, last 3 days
slack_cmd summary ds 7                           # DS channels, last week
slack_cmd search "from:me on:<today>"            # my messages today (replace <today> with YYYY-MM-DD)
slack_cmd search "to:me after:<date>"            # mentions of me since date
slack_cmd search "in:#engineering <keyword>"     # search a channel for keyword
slack_cmd messages "C0A6G8CR19C,C088PMMTLPK" 3   # specific channels by ID
```

## Workflow

### Step 1: Fetch data via CLI

Pick the right command based on the user's request:
- **"check PME channels"** → `slack_cmd summary pme 3`
- **"messages I wrote today"** → `slack_cmd search "from:me on:YYYY-MM-DD"`
- **"what's happening in #engineering"** → `slack_cmd summary engineering 1`
- **"who mentioned me"** → `slack_cmd search "to:me after:YYYY-MM-DD"`

### Step 2: Analyze and present

Read the script output and identify:
- **Direct mentions** (shown with `>>>` prefix in output)
- **Action requests** — review, approve, fix, deploy
- **Unanswered threads** — threads the user started with no replies
- **Questions directed at the user**
- **Blockers** — someone blocked on the user
- **PR/code review requests**

### Step 3: Format the summary

```
## Slack Summary
**Timeframe:** [period]  |  **Channels checked:** [list]

### Action Items (requires your response/action)
- **Channel:** #name | **From:** @person | **Action needed:** ... | **Priority:** High/Medium/Low

### FYI (no action needed)
- Bullets of important updates

### Threads You're In
- Active threads you may want to reply to
```

## Priority Rules

1. **High** — blocked on you, deadline today, incident, leadership ask
2. **Medium** — PR review, direct question, decision needing input
3. **Low** — tagged in discussion, FYI mentions

## Prerequisites

- Logged into Slack workspace in Google Chrome (via `app.slack.com`)
- macOS (uses Keychain for Chrome cookie decryption)
- `brew install leveldb` (the plugin reads Chrome's localStorage via `leveldbutil` to extract the `xoxc` token, which Slack moved out of HTML during its Gantry-v2 migration)
