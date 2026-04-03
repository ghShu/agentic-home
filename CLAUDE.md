# Global Agent Instructions

These instructions apply to every Claude Code session, in every project.

For extended context about this home directory setup, see `~/AGENTS.md`.

## Development Rules

- After making changes to code, always run lints and type-checks before finishing.
- If you changed a test file, you must run those tests.
- Never commit with `--no-verify`. If hooks are failing, investigate and fix the root cause.
- Never make git commits unless explicitly instructed to do so.
- Never mention AI tools, models, or vendors (e.g. "Claude", "Anthropic", "Co-Authored-By") in commit messages.
- Don't add features, refactor, or "improve" code beyond what was asked.
- Don't add comments or docstrings to code you didn't change.

## Working Style

- Prefer editing existing files over creating new ones.
- Read files before modifying them.
- When stuck, ask rather than guess.
- Keep responses concise — skip preambles and summaries of what you just did.
