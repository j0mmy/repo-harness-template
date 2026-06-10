# Claude Code Instructions

This repository uses `AGENTS.md` as the canonical agent operating contract.
This file is only the Claude Code entrypoint into those repo docs; do not duplicate roadmap, architecture, or active task state here.

Before editing anything:

1. Read `AGENTS.md`.
2. Follow the read order and session lifecycle in `AGENTS.md`.
3. Never read, print, summarize, move, or commit `.env*` files or other secret material.
4. Use `make initialize` for cold-start verification when starting or resuming repo work.
5. Use `make check` as the canonical final consistency gate.

Project status lives in `PROGRESS.md`; module health and cleanup priorities live in `QUALITY.md`.
