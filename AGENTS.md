# Secure Web App Skill — Agent Instructions

This repository ships the **`secure-webapp`** skill: OWASP-grounded security
guidance for building, editing, reviewing, and hardening web applications. It
is curated from OWASP Top 10:2025, ASVS 5.0, the Cheat Sheet Series, and
selected WSTG material.

This file is read by Codex and any other agent that loads `AGENTS.md`. Gemini
users: see `GEMINI.md`. Claude Code users: the skill is auto-discovered from
`SKILL.md`.

## When to use the skill

Engage `secure-webapp` whenever you work on web-application code or design that
touches: authentication, sessions, tokens (JWT/OAuth/OIDC), user input,
database queries, file uploads, API endpoints, cookies/CORS/CSP/headers,
secrets, redirects, external URL fetches, logging/errors, dependencies, or
threat modeling — and for vulnerability classes such as XSS, SQLi, IDOR, CSRF,
SSRF, open redirect, prototype pollution, deserialization, and supply-chain
risk.

When that applies:

1. Read `SKILL.md` and follow it. After install it lives at
   `<client-dir>/skills/secure-webapp/SKILL.md` — for example
   `~/.codex/skills/secure-webapp/SKILL.md`.
2. Load only the `references/*.md` files the routing table in `SKILL.md` points
   to. Do not bulk-load every reference.
3. Apply the **Always-On Watchlist** from `SKILL.md` as you write or review
   code.

## Explicit invocation

Users can trigger specific modes with `$secure-webapp <mode>`:

- `$secure-webapp audit` — full prioritized review (reads `assets/audit-checklist.md`)
- `$secure-webapp quick-check` — fast top-risk pass
- `$secure-webapp harden` — apply secure changes directly where edits are authorized
- `$secure-webapp remediate` — iterative audit→fix loop (reads `assets/remediate-checklist.md`)
- `$secure-webapp design-review` — pre-implementation threat model
- `$secure-webapp report` — write a formal audit report (reads `assets/report-template.md`)
- `$secure-webapp update` — self-update the local install
- `$secure-webapp maintain` — refresh and rebuild the skill package

## Tooling note

`SKILL.md` uses Claude Code tool names where it references tools. On Codex,
Gemini, or any other agent, use the equivalent capability in your environment
(file read, file edit/write, shell, and search). The security guidance itself
is platform-agnostic.
