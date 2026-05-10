#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["pycryptodome"]
# ///
"""Slack CLI for the slack plugin.

Usage:
    slack_cmd channels [filter]                          List channels (JSON), optionally filtered
    slack_cmd messages <ch_ids> [days] [--max-chars N]   Fetch messages + threads from channels
    slack_cmd thread <channel_id> <thread_ts>            Fetch a single thread by timestamp
    slack_cmd search <query> [count] [--max-chars N]     Search messages
    slack_cmd summary <filter> [days]                    channels + messages in one shot

Options:
    --max-chars N   Max characters per message (default: 2000)

All commands authenticate via Chrome cookies automatically.
"""

import datetime
import json
import os
import sys
import time

_PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
_LIB = os.path.join(_PLUGIN_DIR, "lib")
_SHARED_LIB = os.path.join(_PLUGIN_DIR, "..", "_lib")
sys.path.insert(0, _LIB)
sys.path.insert(0, _SHARED_LIB)
from chrome_cookies import get_slack_token  # noqa: E402
from slack_api import SlackAPIError, SlackClient  # noqa: E402


def cmd_channels(args):
    """List channels the user is in, optionally filtered. Returns JSON."""
    pattern = args[0].lower() if args else None
    channels = _list_channels(_get_client(), pattern)
    print(json.dumps(channels, indent=2))


def cmd_messages(args):
    """Fetch messages + thread replies from given channel IDs."""
    if not args:
        _die("Usage: slack_cmd messages <channel_ids> [days_back] [--max-chars N]")

    _parse_max_chars(args)
    channel_ids = args[0].split(",")
    days_back = int(args[1]) if len(args) > 1 else 3
    client = _get_client()
    _fetch_and_print(client, channel_ids, days_back)


def cmd_thread(args):
    """Fetch a single thread by channel ID and thread timestamp."""
    if len(args) < 2:
        _die("Usage: slack_cmd thread <channel_id> <thread_ts>")

    _parse_max_chars(args)
    ch_id = args[0]
    thread_ts = args[1]
    if thread_ts.startswith("p"):
        raw = thread_ts[1:]
        thread_ts = raw[:10] + "." + raw[10:]

    client = _get_client()
    ch_name = _get_channel_name(client, ch_id)
    my_id = client.my_id

    print(f"\n{'='*60}")
    print(f"# #{ch_name} ({ch_id}) — thread {thread_ts}")
    print(f"{'='*60}")

    try:
        data = client.api(
            "conversations.replies",
            {"channel": ch_id, "ts": thread_ts, "limit": "100"},
        )
    except SlackAPIError as e:
        print(f"  ERROR: {e.error}")
        return

    msgs = data.get("messages", [])
    if not msgs:
        print("  (no messages found for this thread)")
        return

    print(f"  {len(msgs)} messages in thread\n")
    for m in msgs:
        _print_msg(client, m, my_id, indent="    ")


def cmd_search(args):
    """Search messages using Slack search syntax."""
    if not args:
        _die("Usage: slack_cmd search <query> [count] [--max-chars N]")

    _parse_max_chars(args)
    query = args[0]
    count = int(args[1]) if len(args) > 1 else 50
    client = _get_client()

    data = client.api(
        "search.messages",
        {
            "query": query,
            "sort": "timestamp",
            "sort_dir": "desc",
            "count": str(count),
        },
    )
    matches = data.get("messages", {}).get("matches", [])
    total = data.get("messages", {}).get("total", 0)

    print(f"Found {total} results (showing {len(matches)}):\n")
    for m in matches:
        ts = datetime.datetime.fromtimestamp(float(m["ts"]))
        ch_name = m.get("channel", {}).get("name", "?")
        text = m.get("text", "")[:_max_chars]
        permalink = m.get("permalink", "")

        print(f"[{ts.strftime('%b %d %H:%M')}] #{ch_name} ({m.get('username', '?')}):")
        for line in text.split("\n"):
            print(f"  {line}")
        if permalink:
            print(f"  link: {permalink}")
        print()


def cmd_summary(args):
    """List matching channels then fetch all their messages."""
    pattern = args[0].lower() if args else None
    days_back = int(args[1]) if len(args) > 1 else 3
    client = _get_client()

    channels = _list_channels(client, pattern)
    if not channels:
        print("No channels found.")
        return

    print(f"Found {len(channels)} channel(s):")
    for c in channels:
        print(f"  #{c['name']}")
    print(f"\nFetching messages from last {days_back} day(s)...\n")

    _fetch_and_print(client, [c["id"] for c in channels], days_back)


_client = None


def _get_client():
    global _client
    if not _client:
        token = get_slack_token()
        print(f"Authenticated to: {token['workspace']}.slack.com", file=sys.stderr)
        _client = SlackClient.from_token_json(token)
    return _client


def _list_channels(client, pattern=None):
    """Paginate through user's channels, optionally filtered by name substring."""
    channels = []
    cursor = None
    while True:
        params = {
            "types": "public_channel,private_channel",
            "limit": "500",
            "exclude_archived": "true",
        }
        if cursor:
            params["cursor"] = cursor
        data = client.api("users.conversations", params)
        for ch in data.get("channels", []):
            if pattern and pattern not in ch["name"].lower():
                continue
            channels.append(
                {
                    "id": ch["id"],
                    "name": ch["name"],
                    "num_members": ch.get("num_members", 0),
                }
            )
        cursor = data.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break
    channels.sort(key=lambda c: c["name"])
    return channels


def _fetch_and_print(client, channel_ids, days_back):
    """Fetch messages + threads for a list of channel IDs and print them."""
    my_id = client.my_id
    oldest = str(int(time.time()) - days_back * 86400)

    for ch_id in channel_ids:
        ch_name = _get_channel_name(client, ch_id)
        print(f"\n{'='*60}")
        print(f"# #{ch_name} ({ch_id})")
        print(f"{'='*60}")

        try:
            data = client.api(
                "conversations.history",
                {"channel": ch_id, "oldest": oldest, "limit": "50"},
            )
        except SlackAPIError as e:
            print(f"  ERROR: {e.error}")
            continue

        msgs = data.get("messages", [])
        if not msgs:
            print("  (no messages in this period)")
            continue

        print(f"  {len(msgs)} messages in last {days_back} day(s)\n")

        for m in reversed(msgs):
            _print_msg(client, m, my_id, indent="    ")
            if m.get("reply_count", 0) > 0:
                try:
                    replies = client.api(
                        "conversations.replies",
                        {"channel": ch_id, "ts": m["ts"], "limit": "30"},
                    )
                    for r in replies.get("messages", [])[1:]:
                        _print_msg(client, r, my_id, indent="        ")
                except SlackAPIError:
                    pass
                print()


def _get_channel_name(client, ch_id):
    try:
        return client.api("conversations.info", {"channel": ch_id})["channel"]["name"]
    except Exception:
        return ch_id


_max_chars = 2000


def _print_msg(client, m, my_id, indent="    "):
    ts = datetime.datetime.fromtimestamp(float(m["ts"]))
    user_id = m.get("user", m.get("bot_id", "?"))
    user_name = client.get_user_name(user_id) if user_id != "?" else "?"
    text = m.get("text", "")[:_max_chars]
    mentioned = my_id and my_id in text
    prefix = ">>> " if mentioned else indent

    print(f"{prefix}[{ts.strftime('%b %d %H:%M')}] {user_name}:")
    for line in text.split("\n"):
        print(f"{prefix}  {line}")
    if m.get("reply_count") and indent == "    ":
        print(f"{prefix}  [{m['reply_count']} replies]")
    if m.get("files"):
        print(f"{prefix}  [files: {len(m['files'])}]")
    if m.get("attachments"):
        for att in m["attachments"][:2]:
            if att.get("title"):
                print(f"{prefix}  [attachment: {att['title'][:80]}]")
    print()


def _parse_max_chars(args):
    """Extract --max-chars N from args and update global _max_chars."""
    global _max_chars
    for i, a in enumerate(args):
        if a == "--max-chars" and i + 1 < len(args):
            _max_chars = int(args[i + 1])
            del args[i : i + 2]
            return


def _die(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


COMMANDS = {
    "channels": cmd_channels,
    "messages": cmd_messages,
    "thread": cmd_thread,
    "search": cmd_search,
    "summary": cmd_summary,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__, file=sys.stderr)
        print(f"Commands: {', '.join(COMMANDS)}", file=sys.stderr)
        sys.exit(1)
    try:
        COMMANDS[sys.argv[1]](sys.argv[2:])
    except (SlackAPIError, RuntimeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
