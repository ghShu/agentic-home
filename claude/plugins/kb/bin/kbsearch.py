#!/usr/bin/env python3
"""
kbsearch — Search the personal knowledge base wiki.

Usage:
  kbsearch <query terms>     Search wiki/**/*.md for matching lines
  kbsearch --index-only      Print the contents of wiki/_index.md

Output is JSON for LLM consumption:
  [{"file": "wiki/topic/concept.md", "line": 12, "snippet": "...matching line..."}]

Empty result: []
"""

import os
import sys
import json
import re
from pathlib import Path

KNOWLEDGE_DIR = Path(os.environ.get("KB_HOME") or str(Path.home() / "knowledge"))
WIKI_DIR = KNOWLEDGE_DIR / "wiki"
INDEX_FILE = WIKI_DIR / "_index.md"


def index_only():
    if not INDEX_FILE.exists():
        print("", end="")
        return
    print(INDEX_FILE.read_text())


def search(terms: list[str]) -> list[dict]:
    if not WIKI_DIR.exists():
        return []

    pattern = re.compile(
        "|".join(re.escape(t) for t in terms),
        re.IGNORECASE,
    )

    results = []
    for md_file in sorted(WIKI_DIR.rglob("*.md")):
        # Skip meta files
        if "_meta" in md_file.parts:
            continue
        try:
            lines = md_file.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue

        rel = str(md_file.relative_to(KNOWLEDGE_DIR))
        for lineno, line in enumerate(lines, start=1):
            if pattern.search(line):
                results.append({
                    "file": rel,
                    "line": lineno,
                    "snippet": line.strip(),
                })

    return results


def main():
    args = sys.argv[1:]

    if not args:
        print("Usage: kbsearch <query terms>  |  kbsearch --index-only", file=sys.stderr)
        sys.exit(1)

    if args == ["--index-only"]:
        index_only()
        return

    terms = args
    results = search(terms)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
