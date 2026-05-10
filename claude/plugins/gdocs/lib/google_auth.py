#!/usr/bin/env python3
"""Google auth helper via gcloud CLI.

Usage:
    from google_auth import get_access_token, google_api_get, google_api_download
    token = get_access_token()
    data = google_api_get("https://docs.googleapis.com/v1/documents/{id}", token)

Prerequisite:
    gcloud auth login --enable-gdrive-access
"""

import json
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request


def _try_reauth():
    """Attempt interactive gcloud re-auth by launching the browser automatically."""
    print(
        "Credentials expired or missing. Launching browser for gcloud auth...",
        file=sys.stderr,
    )
    proc = subprocess.run(
        ["gcloud", "auth", "login", "--enable-gdrive-access", "--launch-browser"],
        timeout=120,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            "gcloud re-auth failed. Please run manually:\n"
            "  gcloud auth login --enable-gdrive-access"
        )
    print("Re-authenticated successfully.", file=sys.stderr)


def get_access_token():
    """Get OAuth access token from gcloud CLI, auto-reauthenticating if needed."""
    result = subprocess.run(
        ["gcloud", "auth", "print-access-token"],
        capture_output=True,
        text=True,
    )
    token = result.stdout.strip()

    if result.returncode != 0 or not token:
        _try_reauth()
        result = subprocess.run(
            ["gcloud", "auth", "print-access-token"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"gcloud auth failed after re-auth: {result.stderr.strip()}\n"
                "Run manually: gcloud auth login --enable-gdrive-access"
            )
        token = result.stdout.strip()
        if not token:
            raise RuntimeError(
                "Empty token after re-auth. Run: gcloud auth login --enable-gdrive-access"
            )

    return token


def google_api_get(url, token=None, params=None):
    """Make authenticated GET request to a Google API."""
    if not token:
        token = get_access_token()
    full_url = url + ("?" + urllib.parse.urlencode(params) if params else "")
    for attempt in range(2):
        req = urllib.request.Request(full_url)
        req.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if attempt == 0 and e.code in (401, 403):
                _try_reauth()
                token = get_access_token()
                continue
            raise


def google_api_download(url, token=None):
    """Make authenticated GET request and return raw bytes."""
    if not token:
        token = get_access_token()
    for attempt in range(2):
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if attempt == 0 and e.code in (401, 403):
                _try_reauth()
                token = get_access_token()
                continue
            raise


if __name__ == "__main__":
    token = get_access_token()
    print(f"Token: {token[:20]}...{token[-10:]}")
    print(f"Length: {len(token)}")
