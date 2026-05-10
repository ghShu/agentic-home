#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["pycryptodome"]
# ///
"""Jira ticket inspection and creation.

Configuration is read from environment variables, with ~/.jira.env as an
optional fallback (see plugins/jira/jira.env.example):

    JIRA_HOST           Required, e.g. https://yourtenant.atlassian.net
    JIRA_PROJECT_KEY    Default project key for `create`

Usage:
    jira_cmd jira <jira_url_or_key>              Read Jira ticket details
    jira_cmd create [summary] [--project KEY]    Create a Jira issue
"""

import os
import subprocess
import sys

_PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
_LIB = os.path.join(_PLUGIN_DIR, "lib")
_SHARED_LIB = os.path.join(_PLUGIN_DIR, "..", "_lib")
sys.path.insert(0, _LIB)
sys.path.insert(0, _SHARED_LIB)
from cli_helpers import die, load_env_file  # noqa: E402
from jira_api import JiraClient, parse_jira_url  # noqa: E402


def _config(key):
    val = os.environ.get(key)
    if val:
        return val
    return load_env_file(os.environ.get("JIRA_ENV_FILE", "~/.jira.env")).get(key)


def cmd_jira(args):
    if not args:
        die("Usage: jira_cmd jira <jira_url_or_key>")

    key = parse_jira_url(args[0]) or args[0]
    client = JiraClient()
    summary = client.get_issue_summary(key)
    custom = summary.get("custom_fields", {})

    lines = []
    lines.append(f"## Jira: [{summary['key']}]({client.host}/browse/{summary['key']})\n")
    lines.append(f"**Summary:** {summary['summary']}")
    lines.append(f"**Status:** {summary['status']} | **Priority:** {summary['priority']}")
    lines.append(f"**Assignee:** {summary['assignee']} | **Reporter:** {summary['reporter']}")
    lines.append(f"**Created:** {summary['created']} | **Updated:** {summary['updated']}")
    if summary["labels"]:
        lines.append(f"**Labels:** {', '.join(summary['labels'])}")

    # Render any custom fields configured via JIRA_CUSTOM_FIELDS_FILE, generically.
    for name, val in custom.items():
        label = name.replace("_", " ").title()
        if isinstance(val, list):
            val = ", ".join(str(v) for v in val)
        lines.append(f"**{label}:** {val}")
    lines.append("")

    if summary["description"]:
        lines.append("### Description\n")
        lines.append(summary["description"])
        lines.append("")

    if summary["comments"]:
        lines.append(f"### Comments ({len(summary['comments'])})\n")
        for c in summary["comments"]:
            lines.append(f"**{c['author']}** ({c['created']}):")
            lines.append(c["body"])
            lines.append("")

    print("\n".join(lines))


def _git_branch():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True,
        )
        branch = result.stdout.strip()
        return branch if branch and branch != "HEAD" else None
    except Exception:
        return None


def cmd_create(args):
    project = None
    summary = None
    description = None

    i = 0
    while i < len(args):
        if args[i] == "--project" and i + 1 < len(args):
            project = args[i + 1]
            i += 2
        elif args[i] == "--description" and i + 1 < len(args):
            description = args[i + 1]
            i += 2
        else:
            summary = args[i]
            i += 1

    if not project:
        project = _config("JIRA_PROJECT_KEY")
    if not project:
        die("--project required (or set JIRA_PROJECT_KEY in ~/.jira.env)")

    if not summary:
        summary = _git_branch()
    if not summary:
        die("Usage: jira_cmd create [summary] [--project KEY] [--description TEXT]")

    client = JiraClient()
    me = client.get_current_user()
    account_id = me.get("accountId")
    display_name = me.get("displayName", "you")
    result = client.create_issue(
        summary, project_key=project, description=description, assignee_account_id=account_id
    )
    print(f"Created: [{result['key']}]({result['url']})")
    print(f"URL: {result['url']}")
    print(f"Assigned to: {display_name}")


COMMANDS = {
    "jira": cmd_jira,
    "create": cmd_create,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__, file=sys.stderr)
        sys.exit(1)
    COMMANDS[sys.argv[1]](sys.argv[2:])
