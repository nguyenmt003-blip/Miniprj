# Project Rules

- Read the current ticket before changing code.
- Only read files directly related to the current ticket; avoid repository-wide scans unless explicitly instructed.
- Inspect existing code and call relationships before editing.
- Use CodeGraph to locate relevant symbols and dependencies
  when useful, then verify against the actual source code.
- Keep changes limited to the current ticket.
- Follow existing architecture and coding conventions.
- Run relevant tests and report the actual results.
- Check git status / diff before editing; never revert unstaged changes or run destructive commands (git reset --hard, git checkout .) on files outside the ticket.
- If handing work to a new conversation, save a concise
  handoff containing progress, changed files, tests, and blockers.