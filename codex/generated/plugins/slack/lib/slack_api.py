#!/usr/bin/env python3
"""Shared Slack API client. Used by Slack-related Claude Code skills."""

import json
import subprocess
import sys
import time
import urllib.parse
import urllib.request


class SlackClient:
    def __init__(self, xoxc, d_cookie):
        self.xoxc = xoxc
        self.d_cookie = d_cookie
        self._user_cache = {}
        self._my_id = None

    def api(self, method, params=None):
        url = f"https://slack.com/api/{method}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        for attempt in range(2):
            req = urllib.request.Request(url)
            req.add_header("Authorization", f"Bearer {self.xoxc}")
            req.add_header("Cookie", f"d={self.d_cookie}")
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read())
            if data.get("ok"):
                return data
            error = data.get("error", "unknown")
            if attempt == 0 and error in (
                "invalid_auth",
                "token_expired",
                "token_revoked",
                "not_authed",
            ):
                print(
                    "\n⚠ Slack session expired. Opening Slack in Chrome...",
                    file=sys.stderr,
                )
                subprocess.run(["open", "-a", "Google Chrome", "https://app.slack.com"])
                print("  Waiting 10s for login to complete...", file=sys.stderr)
                time.sleep(10)
                from chrome_cookies import get_slack_token

                token_data = get_slack_token()
                self.xoxc = token_data["xoxc"]
                self.d_cookie = token_data["d_cookie"]
                continue
            raise SlackAPIError(error, data)
        raise SlackAPIError("auth_retry_failed", {})

    def get_user_name(self, user_id):
        if user_id in self._user_cache:
            return self._user_cache[user_id]
        try:
            data = self.api("users.info", {"user": user_id})
            name = data["user"].get("real_name") or data["user"].get("name", user_id)
            self._user_cache[user_id] = name
            return name
        except Exception:
            self._user_cache[user_id] = user_id
            return user_id

    @property
    def my_id(self):
        if not self._my_id:
            data = self.api("auth.test")
            self._my_id = data["user_id"]
            self._user_cache[self._my_id] = data.get("user", self._my_id)
        return self._my_id

    @classmethod
    def from_token_json(cls, token_json):
        """Create client from JSON string or dict (output of get_slack_token)."""
        data = json.loads(token_json) if isinstance(token_json, str) else token_json
        if "error" in data:
            raise RuntimeError(data["error"])
        return cls(data["xoxc"], data["d_cookie"])


class SlackAPIError(Exception):
    def __init__(self, error, response):
        self.error = error
        self.response = response
        super().__init__(error)
