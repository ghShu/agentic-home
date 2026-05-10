---
name: jira:create
description: Create a new Jira issue assigned to the current user. Project key from $JIRA_PROJECT_KEY (or --project). Summary defaults to current git branch name.
---

Generated from `claude/plugins/jira/skills/create/SKILL.md` by `bin/sync-codex-from-claude`.


# jira:create

Create a Jira issue assigned to the current user. The project key comes from `$JIRA_PROJECT_KEY` (or `~/.jira.env`), or pass `--project KEY` explicitly. Summary defaults to the current git branch name if omitted.

## Configuration

Host and default project are read from `$JIRA_HOST` and `$JIRA_PROJECT_KEY` (or `~/.jira.env`). See `plugins/jira/jira.env.example`.

## Usage

```bash
jira_cmd create [summary] [--project KEY] [--description TEXT]
```

### Examples

```bash
# Use current git branch name as summary, default project from env
jira_cmd create

# Explicit summary
jira_cmd create "Add request timeout alerting"

# With description
jira_cmd create "Fix retry logic" --description "Retries are not respecting backoff config"

# Override project
jira_cmd create "My task" --project PROJ
```

## Output

Prints the created ticket key, clickable URL, and assignee name.
