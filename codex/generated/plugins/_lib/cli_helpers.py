#!/usr/bin/env python3
"""Shared CLI helpers for Claude Code skill scripts.

Location: .claude/envs/python/lib/cli_helpers.py
"""

import sys


def die(msg):
    """Print error message to stderr and exit with code 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def get_flag(args, flag, default=None):
    """Get a --flag value from args without modifying the list."""
    if flag in args:
        idx = args.index(flag)
        if idx + 1 < len(args):
            return args[idx + 1]
    return default


def get_flag_pair(args, flag):
    """Get two values after a --flag (e.g., --dos-range START END). Returns (v1, v2) or (None, None)."""
    if flag not in args:
        return None, None
    idx = args.index(flag)
    if idx + 2 < len(args):
        return args[idx + 1], args[idx + 2]
    return None, None


def extract_flag(args, flag, default=None):
    """Get a --flag value and remove both flag and value from args (mutates args)."""
    for i, a in enumerate(args):
        if a == flag and i + 1 < len(args):
            val = args[i + 1]
            args.pop(i + 1)
            args.pop(i)
            return val
    return default
