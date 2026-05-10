#!/usr/bin/env python3
"""Extract Chrome cookies (and Slack tokens) on macOS.

Usage as module:
    from chrome_cookies import get_slack_token
    token = get_slack_token()  # returns dict with xoxc, d_cookie, workspace

Usage as CLI:
    python3 chrome_cookies.py slack   # prints JSON token for Slack

Slack token extraction depends on Homebrew's `leveldb` package (provides
`leveldbutil`, used to read Chrome's localStorage). Install with:
    brew install leveldb
"""

import glob
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
CHROME_LOCALSTORAGE = os.path.expanduser(
    "~/Library/Application Support/Google/Chrome/Default/Local Storage/leveldb"
)
LEVELDBUTIL = "/opt/homebrew/opt/leveldb/bin/leveldbutil"


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


def _dump_chrome_localstorage():
    """Yield (filename, bytes) tuples from a snapshot of Chrome's localStorage.

    Chrome holds an exclusive lock on the running profile's leveldb, so we
    copy the *.ldb/*.log files to a temp dir before invoking leveldbutil.
    """
    if not os.path.isfile(LEVELDBUTIL):
        raise RuntimeError(
            f"leveldbutil not found at {LEVELDBUTIL}. Install with: brew install leveldb"
        )
    if not os.path.isdir(CHROME_LOCALSTORAGE):
        raise RuntimeError(
            f"Chrome localStorage dir not found at {CHROME_LOCALSTORAGE}"
        )

    tmp = tempfile.mkdtemp(prefix="chrome-ls-")
    try:
        for fn in os.listdir(CHROME_LOCALSTORAGE):
            if fn == "LOCK":
                continue
            src = os.path.join(CHROME_LOCALSTORAGE, fn)
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(tmp, fn))

        for sst in sorted(glob.glob(f"{tmp}/*.ldb") + glob.glob(f"{tmp}/*.log")):
            result = subprocess.run([LEVELDBUTIL, "dump", sst], capture_output=True)
            yield os.path.basename(sst), result.stdout
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def get_slack_token():
    """Extract Slack xoxc + d cookie from Chrome storage.

    The xoxc token lives in Chrome's localStorage (under localConfig_v2) since
    Slack's Gantry-v2 client migration moved bootstrap state out of the
    server-rendered HTML. The d cookie still lives in the cookies DB.

    Returns:
        dict with keys: xoxc, d_cookie, workspace
    """
    all_cookies = get_cookies("%slack.com%")
    if not all_cookies:
        raise RuntimeError("No Slack cookies found. Log into Slack in Chrome first.")

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

    xoxc = None
    workspace = None
    xoxc_re = re.compile(rb"xoxc-[A-Za-z0-9_-]+")
    domain_re = re.compile(rb'"domain"\s*:\s*"([a-zA-Z0-9_-]+)"')
    for _fname, blob in _dump_chrome_localstorage():
        if xoxc is None:
            m = xoxc_re.search(blob)
            if m:
                xoxc = m.group(0).decode()
        if workspace is None:
            m = domain_re.search(blob)
            if m:
                workspace = m.group(1).decode()
        if xoxc and workspace:
            break

    if not xoxc:
        raise RuntimeError(
            "No xoxc token in Chrome localStorage. "
            "Log into Slack at https://app.slack.com in Chrome and refresh."
        )

    workspace = os.environ.get("SLACK_WORKSPACE") or workspace or "slack"

    return {
        "xoxc": xoxc,
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
