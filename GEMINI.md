# Secure Web App Skill — Gemini Instructions

This repository ships the **`secure-webapp`** skill: OWASP-grounded security
guidance for building, editing, reviewing, and hardening web applications. It
is curated from OWASP Top 10:2025, ASVS 5.0, the Cheat Sheet Series, and
selected WSTG material.

## Activating the skill

If your Gemini CLI supports skills, activate `secure-webapp` (via the
`activate_skill` tool or your configured skill loader). Otherwise read
`skills/secure-webapp/SKILL.md` directly — after install it lives at
`~/.gemini/skills/secure-webapp/SKILL.md` (global) or
`<project>/.gemini/skills/secure-webapp/SKILL.md` (project-local) — and follow
it.

## When to use it

Engage the skill whenever you work on web-application code or design that
touches: authentication, sessions, tokens (JWT/OAuth/OIDC), user input,
database queries, file uploads, API endpoints, cookies/CORS/CSP/headers,
secrets, redirects, external URL fetches, logging/errors, dependencies, or
threat modeling — and for vulnerability classes such as XSS, SQLi, IDOR, CSRF,
SSRF, open redirect, prototype pollution, deserialization, and supply-chain
risk.

When that applies:

1. Read `SKILL.md` and follow its routing table.
2. Load only the `references/*.md` files that apply. Do not bulk-load every
   reference.
3. Apply the **Always-On Watchlist** from `SKILL.md` while writing or reviewing
   code.

## Explicit invocation

Trigger modes with `$secure-webapp <mode>`: `audit`, `quick-check`, `harden`,
`remediate`, `design-review`, `report`, `update`, `maintain`. See `AGENTS.md`
for the full description of each mode.

## Tooling note

`SKILL.md` uses Claude Code tool names. On Gemini, map them to your equivalents
(`read_file`, `write_file`/`replace`, `run_shell_command`, and search). The
security guidance itself is platform-agnostic.
