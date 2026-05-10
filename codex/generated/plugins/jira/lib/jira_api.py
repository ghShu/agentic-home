#!/usr/bin/env python3
"""Jira API client using Chrome cookies for authentication.

Config is loaded from environment variables, with `~/.jira.env` as an
optional fallback (see plugins/jira/jira.env.example for the format):

    JIRA_HOST                  Required. e.g. https://yourtenant.atlassian.net
    JIRA_PROJECT_KEY           Default project key for issue creation
    JIRA_CUSTOM_FIELDS_FILE    Optional. JSON file mapping customfield_NNNNN
                               IDs to display names, e.g.
                               {"customfield_10082": "affected_url"}

Usage:
    from jira_api import JiraClient
    client = JiraClient()                 # reads JIRA_HOST from env/file
    issue = client.get_issue("PROJ-1234")
"""

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_lib"),
)
from chrome_cookies import get_cookies  # noqa: E402
from cli_helpers import load_env_file  # noqa: E402


_JIRA_ENV_FILE = os.environ.get("JIRA_ENV_FILE", "~/.jira.env")


def _config(key):
    """Read a config value from os.environ, falling back to ~/.jira.env."""
    val = os.environ.get(key)
    if val:
        return val
    return load_env_file(_JIRA_ENV_FILE).get(key)


def _open_and_wait(url, service_name):
    """Open a login page in Chrome and wait for the user to re-authenticate."""
    print(
        f"\n⚠ {service_name} session expired. Opening login page in Chrome...",
        file=sys.stderr,
    )
    subprocess.run(["open", "-a", "Google Chrome", url])
    print(f"  Waiting 10s for login to complete...", file=sys.stderr)
    time.sleep(10)


def _get_jira_token():
    """Extract Jira tenant.session.token from Chrome cookies."""
    for _, _name, val in get_cookies("%atlassian.net%", ["tenant.session.token"]):
        idx = val.find("eyJ")
        if idx >= 0:
            return val[idx:]
    raise RuntimeError("No Jira session token found. Log into Jira in Chrome first.")


def _load_custom_fields():
    """Optional map of customfield_* IDs to display names, from JIRA_CUSTOM_FIELDS_FILE."""
    path = _config("JIRA_CUSTOM_FIELDS_FILE")
    if not path:
        return {}
    expanded = os.path.expanduser(path)
    if not os.path.isfile(expanded):
        return {}
    with open(expanded) as f:
        return json.load(f)


class JiraClient:
    def __init__(self, host=None):
        host = host or _config("JIRA_HOST")
        if not host:
            raise RuntimeError(
                "JIRA_HOST not configured. Set it in your environment or in "
                f"{_JIRA_ENV_FILE} (see claude/plugins/jira/jira.env.example)."
            )
        self.host = host.rstrip("/")
        self.token = _get_jira_token()
        self._custom_fields = _load_custom_fields()

    def api(self, path, method="GET", data=None):
        """Make a Jira REST API call."""
        url = f"{self.host}{path}"
        for attempt in range(2):
            req = urllib.request.Request(url, method=method)
            req.add_header("Cookie", f"tenant.session.token={self.token}")
            req.add_header("Accept", "application/json")
            if data:
                req.add_header("Content-Type", "application/json")
                req.data = json.dumps(data).encode()
            try:
                with urllib.request.urlopen(req) as resp:
                    return json.loads(resp.read())
            except urllib.error.HTTPError as e:
                if attempt == 0 and e.code in (401, 403):
                    _open_and_wait(self.host, "Jira")
                    self.token = _get_jira_token()
                    continue
                raise

    def get_current_user(self):
        """Return the current authenticated user's accountId and displayName."""
        return self.api("/rest/api/3/myself")

    def create_issue(self, summary, project_key, issue_type="Task", description=None, assignee_account_id=None):
        """Create a new Jira issue. Returns the created issue key and URL."""
        if not project_key:
            raise RuntimeError(
                "project_key is required. Pass --project or set JIRA_PROJECT_KEY."
            )
        fields = {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
        }
        if description:
            fields["description"] = {
                "type": "doc",
                "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}],
            }
        if assignee_account_id:
            fields["assignee"] = {"accountId": assignee_account_id}
        result = self.api("/rest/api/3/issue", method="POST", data={"fields": fields})
        key = result["key"]
        url = f"{self.host}/browse/{key}"
        return {"key": key, "url": url}

    def get_issue(self, key, fields=None):
        """Get a Jira issue by key (e.g., PROJ-1234).

        Returns dict with key, summary, description, status, assignee, comments, etc.
        """
        params = ""
        if fields:
            params = f"?fields={','.join(fields)}"
        return self.api(f"/rest/api/3/issue/{key}{params}")

    def get_issue_summary(self, key):
        """Get a concise summary of a Jira issue."""
        issue = self.get_issue(key)
        fields = issue.get("fields", {})

        desc = _adf_to_text(fields.get("description"))

        comments = []
        comment_data = fields.get("comment", {}).get("comments", [])
        for c in comment_data:
            author = c.get("author", {}).get("displayName", "?")
            body = _adf_to_text(c.get("body"))
            created = c.get("created", "?")[:19]
            comments.append({"author": author, "body": body, "created": created})

        custom_fields = _extract_custom_fields(fields, self._custom_fields)

        return {
            "key": issue["key"],
            "summary": fields.get("summary", "?"),
            "status": fields.get("status", {}).get("name", "?"),
            "priority": fields.get("priority", {}).get("name", "?"),
            "assignee": (fields.get("assignee") or {}).get("displayName", "Unassigned"),
            "reporter": (fields.get("reporter") or {}).get("displayName", "?"),
            "created": fields.get("created", "?")[:19],
            "updated": fields.get("updated", "?")[:19],
            "description": desc,
            "labels": fields.get("labels", []),
            "comments": comments,
            "custom_fields": custom_fields,
        }


def _extract_custom_fields(fields, mapping):
    """Extract known custom fields into a clean dict. `mapping` is {field_id: name}."""
    result = {}
    for field_id, name in mapping.items():
        val = fields.get(field_id)
        if val is None:
            continue
        if isinstance(val, dict) and "value" in val:
            result[name] = val["value"]
        elif isinstance(val, list):
            values = []
            for item in val:
                if isinstance(item, dict) and "value" in item:
                    values.append(item["value"])
                elif isinstance(item, str):
                    values.append(item)
            if values:
                result[name] = values
        elif isinstance(val, str):
            result[name] = val
    return result


def _adf_to_text(node, depth=0):
    """Convert Atlassian Document Format (ADF) to plain text."""
    if not node:
        return ""
    if isinstance(node, str):
        return node

    text_parts = []
    node_type = node.get("type", "")

    if node_type == "text":
        return node.get("text", "")

    if node_type == "hardBreak":
        return "\n"

    if node_type == "mention":
        return f"@{node.get('attrs', {}).get('text', '?')}"

    if node_type == "inlineCard":
        url = node.get("attrs", {}).get("url", "")
        return url

    for child in node.get("content", []):
        text_parts.append(_adf_to_text(child, depth + 1))

    joined = "".join(text_parts)

    if node_type == "paragraph":
        return joined + "\n"
    if node_type == "heading":
        level = node.get("attrs", {}).get("level", 1)
        return "#" * level + " " + joined + "\n"
    if node_type == "bulletList":
        return joined
    if node_type == "orderedList":
        return joined
    if node_type == "listItem":
        return "  " * depth + "- " + joined
    if node_type == "codeBlock":
        return f"```\n{joined}\n```\n"
    if node_type == "blockquote":
        return "> " + joined
    if node_type == "table":
        return joined + "\n"
    if node_type == "tableRow":
        return (
            "| "
            + " | ".join(_adf_to_text(cell).strip() for cell in node.get("content", []))
            + " |\n"
        )

    return joined


def parse_jira_url(url):
    """Extract issue key from a Jira URL."""
    m = re.search(r"/browse/([A-Z]+-\d+)", url)
    return m.group(1) if m else None
