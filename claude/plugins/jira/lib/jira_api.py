#!/usr/bin/env python3
"""Jira API client using Chrome cookies for authentication.

Location: .claude/envs/python/lib/jira_api.py

Usage:
    from jira_api import JiraClient
    client = JiraClient()
    issue = client.get_issue("SP-4046")
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


def _open_and_wait(url, service_name):
    """Open a login page in Chrome and wait for the user to re-authenticate."""
    print(
        f"\n⚠ {service_name} session expired. Opening login page in Chrome...",
        file=sys.stderr,
    )
    subprocess.run(["open", "-a", "Google Chrome", url])
    print(f"  Waiting 10s for login to complete...", file=sys.stderr)
    time.sleep(10)


JIRA_HOST = "https://evenup.atlassian.net"


def _get_jira_token():
    """Extract Jira tenant.session.token from Chrome cookies."""
    for _, _name, val in get_cookies("%atlassian.net%", ["tenant.session.token"]):
        idx = val.find("eyJ")
        if idx >= 0:
            return val[idx:]
    raise RuntimeError("No Jira session token found. Log into Jira in Chrome first.")


class JiraClient:
    def __init__(self, host=JIRA_HOST):
        self.host = host.rstrip("/")
        self.token = _get_jira_token()

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
                    _open_and_wait("https://evenup.atlassian.net", "Jira")
                    self.token = _get_jira_token()
                    continue
                raise

    def get_current_user(self):
        """Return the current authenticated user's accountId and displayName."""
        return self.api("/rest/api/3/myself")

    def create_issue(self, summary, project_key="AS", issue_type="Task", description=None, assignee_account_id=None):
        """Create a new Jira issue. Returns the created issue key and URL."""
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
        """Get a Jira issue by key (e.g., SP-4046).

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

        # Extract plain text from ADF description
        desc = _adf_to_text(fields.get("description"))

        # Get comments
        comments = []
        comment_data = fields.get("comment", {}).get("comments", [])
        for c in comment_data:
            author = c.get("author", {}).get("displayName", "?")
            body = _adf_to_text(c.get("body"))
            created = c.get("created", "?")[:19]
            comments.append({"author": author, "body": body, "created": created})

        # Extract known custom fields
        custom_fields = _extract_custom_fields(fields)

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


# Known SP-project custom field IDs (discovered from Jira API).
# To find new ones: client.get_issue("SP-XXXX") and inspect customfield_* keys.
_KNOWN_CUSTOM_FIELDS = {
    "customfield_10082": "affected_url",  # Case URL (evenup.law/cases/...)
    "customfield_10185": "firm_name",  # Firm/customer name
    "customfield_10468": "affected_area",  # Product area (list of options)
    "customfield_10183": "contact_email",  # Customer contact email
    "customfield_10187": "incident_date",  # When issue was first reported
}


def _extract_custom_fields(fields):
    """Extract known custom fields into a clean dict."""
    result = {}
    for field_id, name in _KNOWN_CUSTOM_FIELDS.items():
        val = fields.get(field_id)
        if val is None:
            continue
        # Option field: {"value": "Yes", "id": "10140"}
        if isinstance(val, dict) and "value" in val:
            result[name] = val["value"]
        # Multi-option field: [{"value": "Treatment Timeline"}, ...]
        elif isinstance(val, list):
            values = []
            for item in val:
                if isinstance(item, dict) and "value" in item:
                    values.append(item["value"])
                elif isinstance(item, str):
                    values.append(item)
            if values:
                result[name] = values
        # String field
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
