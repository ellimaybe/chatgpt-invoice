# CLAUDE.md
Project guidance for Claude Code in this repository.

## What this repo is
Invoice automation scripts + docs (Python/PowerShell/Markdown).

## Defaults
- Make small, reviewable changes.
- Prefer clarity over cleverness.
- Keep Windows-friendly instructions (PowerShell).

## Safety (non-negotiable)
- Never commit secrets: `.env`, `*.env`, tokens, passwords, cookies, session data.
- If anything looks secret-ish, stop and warn.

## Git workflow
- When the user asks to commit/push, delegate to the **git-helper** subagent:
  - “Use the git-helper agent to commit…” / “Use the git-helper agent to push…”
- Main agent should not push to `main` unless the user explicitly asks.

## Subagents and commands
- Subagents live in `.claude/agents/` (project-scoped).
- Slash commands live in `.claude/commands/` (project-scoped).
