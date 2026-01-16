\# CLAUDE.md

Guidance for Claude Code when working in this repository.



\## Project goal

Automate invoice-related workflows (scripts, docs, scheduling). Prefer maintainable, safe automation over clever one-offs.



\## Working style

\- Make small, reviewable changes.

\- Prefer clarity over micro-optimizations.

\- When editing files, preserve existing structure unless refactoring is requested.

\- Don’t introduce new dependencies unless necessary; explain why if you do.



\## Safety rules (do not violate)

\- Never commit secrets:

&nbsp; - `.env`, `\*.env`, tokens, API keys, passwords, cookies, session data, private URLs.

&nbsp; - If suspicious strings appear (Bearer tokens, long random keys, credentials), STOP and warn.

\- Prefer `.env.example` for documenting required environment variables.

\- If a file looks user/private (personal notes, credentials), ask before using or committing it.



\## Git policy (IMPORTANT)

\### Default behavior

\- If the user says \*\*"commit"\*\*: commit locally only. Do NOT push.

\- If the user says \*\*"commit and push"\*\*: push to a \*\*feature branch\*\*, not `main`, unless the user explicitly says "push to main".

\- Only push to `main` when the user explicitly says \*\*"push to main"\*\*.



\### Pre-commit checklist (always)

When asked to commit and/or push, do this sequence:

1\. Show:

&nbsp;  - `git status`

&nbsp;  - `git diff --stat`

2\. Summarize changes in 3–6 bullets (human-readable).

3\. Propose ONE short commit message:

&nbsp;  - imperative mood: "Add …", "Fix …", "Refactor …", "Docs: …"

&nbsp;  - <= 72 chars if possible

4\. Check for secrets:

&nbsp;  - Ensure `.env` is not staged

&nbsp;  - If any secret-like patterns appear, STOP and warn

5\. Stage everything intended:

&nbsp;  - `git add -A`

6\. Commit with the proposed message.

7\. If pushing:

&nbsp;  - Confirm current branch (`git branch --show-current`)

&nbsp;  - If branch is `main`, only push if user explicitly requested "push to main"

&nbsp;  - Otherwise push the current feature branch



\### Branch naming

If a feature branch is needed, create one using:

\- `feature/<short-topic>` for new work (e.g. `feature/invoice-scheduler`)

\- `fix/<short-topic>` for bug fixes (e.g. `fix/playwright-timeout`)

\- `docs/<short-topic>` for documentation (e.g. `docs/setup-guide`)



\### Sync policy (avoid messy merges)

\- If pushing to a shared branch, prefer:

&nbsp; - `git pull --rebase` before pushing

\- If conflicts occur, STOP and explain the conflict before proceeding.



\## Tests / checks

\- If there is a test command or linting configured, run it before pushing.

\- If none exists, state "No automated tests found" and proceed (unless the user asked to add tests).



\## Documentation

\- Keep `README.md` current when workflows change.

\- For setup steps, include Windows-friendly instructions (PowerShell where relevant).



\## What to do when the user asks:

\### "Commit all changes and push"

\- Follow the Git policy above.

\- Prefer pushing to a feature branch unless user said "push to main".



\### "Now commit all changes, generate a short message, push to main"

\- Follow checklist.

\- Ensure secrets check passes.

\- Commit, then `git push origin main`.

\- Output the commit hash.



\## Output expectations

After a commit/push, report:

\- the commit message

\- the commit hash

\- the branch pushed

\- a 1–2 sentence summary of what changed



