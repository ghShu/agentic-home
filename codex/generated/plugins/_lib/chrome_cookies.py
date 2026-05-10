#!/usr/bin/env python3
"""Extract cookies from Chrome on macOS. Used by multiple Claude Code skills.

Location: .claude/envs/python/lib/chrome_cookies.py

Usage as module:
    from chrome_cookies import get_slack_token
    token = get_slack_token()  # returns dict with xoxc, d_cookie, workspace

Usage as CLI:
    python3 chrome_cookies.py slack   # prints JSON token for Slack
"""

import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request

from Crypto.Cipher import AES

CHROME_COOKIES = os.path.expanduser(
    "~/Library/Application Support/Google/Chrome/Default/Cookies"
)


def _get_chrome_key():
    result = subprocess.run(
        ["security", "find-generic-password", "-w", "-s", "Chrome Safe Storage"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError("Failed to get Chrome encryption key from Keychain")
    return hashlib.pbkdf2_hmac(
        "sha1", result.stdout.strip().encode("utf-8"), b"saltysalt", 1003, dklen=16
    )


def _decrypt(encrypted_value, key):
    if encrypted_value[:3] == b"v10":
        encrypted_value = encrypted_value[3:]
        cipher = AES.new(key, AES.MODE_CBC, IV=b" " * 16)
        decrypted = cipher.decrypt(encrypted_value)
        padding_len = decrypted[-1]
        if isinstance(padding_len, int) and 1 <= padding_len <= 16:
            decrypted = decrypted[:-padding_len]
        return decrypted.decode("utf-8", errors="replace")
    return encrypted_value.decode("utf-8", errors="replace")


def get_cookies(host_pattern, cookie_names=None):
    """Extract cookies from Chrome for a given host pattern.

    Args:
        host_pattern: SQL LIKE pattern (e.g., '%slack.com%')
        cookie_names: optional list of cookie names to filter

    Returns:
        list of (host, name, value) tuples
    """
    if not os.path.exists(CHROME_COOKIES):
        raise RuntimeError("Chrome cookies database not found")

    tmp = tempfile.mktemp(suffix=".db")
    shutil.copy2(CHROME_COOKIES, tmp)

    try:
        key = _get_chrome_key()
        conn = sqlite3.connect(tmp)
        cur = conn.cursor()

        query = (
            "SELECT host_key, name, encrypted_value FROM cookies WHERE host_key LIKE ?"
        )
        params = [host_pattern]
        if cookie_names:
            placeholders = ",".join("?" for _ in cookie_names)
            query += f" AND name IN ({placeholders})"
            params.extend(cookie_names)

        cur.execute(query, params)
        results = []
        for host, name, enc_val in cur.fetchall():
            val = urllib.parse.unquote(_decrypt(enc_val, key))
            results.append((host, name, val))

        conn.close()
        return results
    finally:
        os.unlink(tmp)


def get_slack_token():
    """Extract Slack xoxc token and d cookie from Chrome.

    Returns:
        dict with keys: xoxc, d_cookie, workspace
    """
    # Single DB read: get all slack cookies at once
    all_cookies = get_cookies("%slack.com%")
    if not all_cookies:
        raise RuntimeError("No Slack cookies found. Log into Slack in Chrome first.")

    # Find d cookie with xoxd token
    d_cookie_encoded = None
    for _, name, val in all_cookies:
        if name == "d" and "xoxd-" in val:
            idx = val.find("xoxd-")
            d_cookie_encoded = urllib.parse.quote(val[idx:], safe="")
            break
    if not d_cookie_encoded:
        raise RuntimeError(
            "No Slack session cookie found. Log into Slack in Chrome first."
        )

    # Detect workspace from cookie hosts
    workspaces = set()
    for host, _, _ in all_cookies:
        host = host.lstrip(".")
        if host.endswith(".slack.com") and host not in ("slack.com", "api.slack.com"):
            workspaces.add(host.replace(".slack.com", ""))
    if not workspaces:
        raise RuntimeError("Could not detect Slack workspace")
    workspace = sorted(workspaces)[0]

    # Fetch xoxc token from web client
    req = urllib.request.Request(f"https://{workspace}.slack.com/?no_sso=1")
    req.add_header("Cookie", f"d={d_cookie_encoded}")
    with urllib.request.urlopen(req) as resp:
        body = resp.read().decode("utf-8", errors="replace")

    match = re.search(r"(xoxc-[a-zA-Z0-9_-]+)", body)
    if not match:
        raise RuntimeError(
            "Could not extract xoxc token. Session may be expired — re-login to Slack in Chrome."
        )

    return {
        "xoxc": match.group(1),
        "d_cookie": d_cookie_encoded,
        "workspace": workspace,
    }


if __name__ == "__main__":
    service = sys.argv[1] if len(sys.argv) > 1 else "slack"
    if service == "slack":
        try:
            print(json.dumps(get_slack_token()))
        except RuntimeError as e:
            print(json.dumps({"error": str(e)}))
            sys.exit(1)
    else:
        print(json.dumps({"error": f"Unknown service: {service}"}))
        sys.exit(1)
