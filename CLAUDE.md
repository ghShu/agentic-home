# Global Agent Instructions

These instructions apply to every Claude Code session, in every project.

For extended context about this home directory setup, see `~/AGENTS.md`.

## Development Rules

- After making changes to code, always run lints and type-checks before finishing.
- If you changed a test file, you must run those tests.
- Never commit with `--no-verify`. If hooks are failing, investigate and fix the root cause.
- Never make git commits unless explicitly instructed to do so.
- Never mention AI tools, models, or vendors (e.g. "Claude", "Anthropic", "Cursor", "Co-Authored-By", "Made with [Cursor](https://cursor.com)") in commit messages, PR titles, or PR descriptions. Do not append any "made with"/attribution footer.
- Don't add features, refactor, or "improve" code beyond what was asked.
- Don't add comments or docstrings to code you didn't change.
- Match the surrounding file's style (quotes, type hints, formatting) — don't restyle code you're editing for an unrelated reason.

## Working Style

- Prefer editing existing files over creating new ones.
- Read files before modifying them.
- When stuck, ask rather than guess.
- When a request is open-ended ("make X better/faster/more robust", "clean this up", "improve Y"), STOP. Do not pick an interpretation and start coding. List the reasonable interpretations first and ask which one is meant. Only proceed once the goal is concrete.
- Surface assumptions before acting on them. If a simpler approach exists than what was asked for, say so before implementing — don't just implement what was asked if you'd push back on it.
- Keep responses concise — skip preambles and summaries of what you just did.
