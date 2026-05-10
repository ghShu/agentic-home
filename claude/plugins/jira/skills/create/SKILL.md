---
name: jira:create
description: Create a new Jira Task in AI Entities (AS), assigned to the current user. Summary defaults to current git branch name.
argument-hint: "[summary]"
allowed-tools: ["Bash"]
user-invocable: true
---

# jira:create

Create a Task in the AI Entities (AS) Jira project, assigned to the current user. Summary defaults to the current git branch name if omitted.

## Usage

```bash
jira_cmd create [summary] [--project KEY] [--description TEXT]
```

### Examples

```bash
# Use current git branch name as summary
jira_cmd create

# Explicit summary
jira_cmd create "Add CLP timeout alerting"

# With description
jira_cmd create "Fix retry logic" --description "Retries are not respecting backoff config"

# Different project
jira_cmd create "My task" --project SP
```

## Output

Prints the created ticket key, clickable URL, and assignee name.
