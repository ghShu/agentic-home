---
name: jira:read
description: Look up a Jira ticket by key or URL — shows summary, status, custom fields, and comments
---

Generated from `claude/plugins/jira/skills/read/SKILL.md` by `bin/sync-codex-from-claude`.


# jira:read

Read Jira ticket details including custom fields (matter ID, firm, incident date), description, and comments. Authenticates via Chrome cookies.

## Usage

```bash
jira_cmd jira <jira_key_or_url>
```

### Examples

```bash
jira_cmd jira "AS-21982"
jira_cmd jira "SP-4046"
jira_cmd jira "https://evenup.atlassian.net/browse/SP-4046"
```

## Output

Returns ticket summary, status, assignee, reporter, custom fields (Affected URL with matter ID, firm name, incident date), description, and recent comments.

**Tip:** The matter ID is in the **Affected URL** custom field, not in the description.
