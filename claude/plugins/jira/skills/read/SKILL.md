---
name: jira:read
description: Look up a Jira ticket by key or URL — shows summary, status, custom fields, and comments
argument-hint: "<jira_key_or_url>"
allowed-tools: ["Bash"]
user-invocable: true
---

# jira:read

Read Jira ticket details — summary, status, custom fields (if configured), description, and comments. Authenticates via Chrome cookies.

## Configuration

The host is read from `$JIRA_HOST` (or `~/.jira.env`). Custom fields are optional and configured via `$JIRA_CUSTOM_FIELDS_FILE` pointing to a JSON map of `customfield_NNNNN` → display name. See `plugins/jira/jira.env.example`.

## Usage

```bash
jira_cmd jira <jira_key_or_url>
```

### Examples

```bash
jira_cmd jira "PROJ-1234"
jira_cmd jira "https://yourtenant.atlassian.net/browse/PROJ-1234"
```

## Output

Returns ticket summary, status, assignee, reporter, any configured custom fields, description, and recent comments.
