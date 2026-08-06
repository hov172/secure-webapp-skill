---
name: secure-webapp
description: Use for OWASP-grounded security guidance when building, editing, or reviewing web applications. Trigger proactively for auth, sessions, JWT/OAuth/OIDC, user input, DB queries, file uploads, API endpoints, cookies/CORS/CSP/security headers, secrets, redirects, external URL fetches, logging/errors, dependencies, threat modeling, hardening, audits, LLM/AI features such as prompt handling, agent tools, and MCP servers, or vulnerability classes such as XSS, SQLi, IDOR, CSRF, SSRF, open redirect, prototype pollution, deserialization, prompt injection, and supply chain risk.
---

# Secure Web App Coding

Turns OWASP Top 10:2025, ASVS 5.0, the Cheat Sheet Series, and selected WSTG material into practical web-app security guidance.

**Default (inline):** write secure code quietly; flag only the highest-impact issue you see nearby.
**Audit:** on "review", "audit", "harden", "is this secure?", or incident follow-up — read `assets/audit-checklist.md` and produce prioritized findings.

Modes, invoked as `$secure-webapp <mode>`:

- `$secure-webapp audit`: full prioritized review; read `assets/audit-checklist.md`.
- `$secure-webapp quick-check`: highest-risk pass only — authorization, auth/session, secrets, injection/XSS, uploads, SSRF, tokens. No full checklist report.
- `$secure-webapp harden`: apply secure changes directly where edits are authorized; small patches that preserve the architecture; verify, and flag anything needing product approval.
- `$secure-webapp remediate`: iterative audit→fix loop; read `assets/remediate-checklist.md` in full first.
- `$secure-webapp design-review`: pre-implementation threat model — assumptions, trust boundaries, abuse cases, must-have controls, unresolved questions.
- `$secure-webapp report`: write a formal report to `docs/security-audit-report-YYYY-MM-DD.md`; read `assets/report-template.md` in full first and follow every step. Requires a prior audit this session. Write to the file, never into the chat.
- `$secure-webapp update`: self-update this install by running `npx --yes github:hov172/secure-webapp-skill --global`. It version-checks and only reinstalls when a newer release exists. Flags: `--claude`/`--codex`/`--gemini`, `--check`, `--force`.
- `$secure-webapp maintain`: update the skill package itself, from a clone of the source repository — see `scripts/README.md`.

Load only the references the task needs. Never bulk-load them all.

## Routing

| Task involves | Load |
|---|---|
| Untrusted strings interpreted as HTML/DOM/SQL/shell/NoSQL/LDAP/regex/CSV | `references/input-handling.md` |
| Login, signup, passwords, MFA, reset, brute force, sessions, cookies, logout | `references/auth-and-sessions.md` |
| Permissions, roles, ownership checks, IDOR, tenant isolation | `references/authorization.md` |
| JWTs, API/refresh tokens, signing and verification, OAuth/OIDC, PKCE, state | `references/tokens-and-oauth.md` |
| REST/GraphQL/WebSocket endpoints, rate limits, mass assignment, response shape, uploads/downloads, path traversal, pre-signed URLs | `references/apis-and-files.md` |
| Secure/HttpOnly/SameSite, CSP, CORS, CSRF, headers, iframes, postMessage | `references/frontend-and-headers.md` |
| Env vars, `.env`, keys, secrets manager, debug mode, defaults | `references/secrets-and-config.md` |
| Encryption, password hashing, algorithms, key management, PII | `references/data-and-crypto.md` |
| Dependencies, lockfiles, SBOM, CI/CD, GitHub Actions, signed artifacts | `references/supply-chain.md` |
| User-controlled external URLs, SSRF, race conditions, deserialization, prototype pollution | `references/secure-coding.md` |
| Logging, error responses, stack traces, audit trails, fail-closed, rollback | `references/logging-and-errors.md` |
| New feature design, threat modeling, multi-tenancy, secure-by-design decisions | `references/insecure-design.md` |
| LLM/AI features, prompt construction, RAG, agent tool calls, MCP servers, model output rendered or executed | `references/ai-and-llm.md` |

## Always-On Watchlist

Flag these in passing when seen in web code, with one concrete fix:

1. Missing server-side auth/ownership checks on resource routes. Prefer query-level scoping such as `WHERE owner_id = :current_user`.
2. Hardcoded secrets, credentials, JWT secrets, API keys, or committed `.env` files.
3. String-built SQL/NoSQL/shell queries. Use parameterized queries, safe builders, or argv APIs.
4. Plaintext or fast-hashed passwords. Use argon2id, scrypt, or bcrypt; PBKDF2 only where required.
5. JWT verification with unpinned algorithms, missing `exp`/`iss`/`aud` checks, or secrets in code.
6. `dangerouslySetInnerHTML`, `v-html`, or `innerHTML` with user content. Render as text or sanitize.
7. Credentialed CORS with wildcard or echoed origins. Use a strict allowlist.
8. Missing rate limits on login, signup, reset, MFA/OTP, or expensive endpoints.
9. Verbose production errors, stack traces, SQL/ORM details, or debug mode exposed to clients.
10. Open redirects from unvalidated `next`, `returnTo`, or URL parameters.
11. SSRF from user-supplied URLs without allowlists and private-IP blocking after DNS and redirects.
12. Logs containing passwords, tokens, session IDs, secrets, or unnecessary PII.
13. Client-only security controls: hidden fields, disabled buttons, client role claims, frontend-only validation.
14. File uploads without size, type, path, storage, or generated-name controls.
15. Fail-open exception paths around auth, authorization, rate limits, feature flags, or transactions.
16. Non-atomic balance, quota, payment, inventory, coupon, or one-time-token state changes.
17. Model/LLM output reaching a sink unchecked — `innerHTML`, shell, SQL, file paths, `fetch` URLs, or a downstream agent. Treat it as untrusted input.
18. Agent tool calls authorized against the service account rather than the end user, or generic `run_shell`/`execute_sql`/`http_request` tools that turn prompt injection into RCE, SQLi, or SSRF.
19. Untrusted text concatenated into a system prompt; secrets or other users' data in the model context.
20. Mutable dependency or CI-action references where pinning and lockfiles are expected — a moved tag runs attacker code in that job with that job's secrets. Rate High when the job holds deploy credentials, signing keys, or publish rights; same for long-lived cloud credentials where OIDC exists. Audit every workspace in a monorepo, and flag an `--audit-level` weaker than `high`.

## Behavior

- Write secure code by default, without long explanations. Name security-relevant choices briefly when useful.
- Match rigor to the app's stakes; do not force enterprise controls into throwaway prototypes.
- Never generate intentionally insecure code. Offer the safe equivalent and state the constraint in one sentence.
- For new trust-boundary features, check: untrusted input, authorization, failure mode, stored data, abuse path.
- When auditing, inspect real code, ask only essential scoping questions, and report severity + location + evidence + fix, prioritized.
- Do not cite OWASP requirement numbers unless asked.
- Do not claim to perform penetration testing; this is code and design review.

## Scope

Mainstream web stacks — Next.js, Express, Django, Flask, FastAPI, Rails, Spring, Laravel, Go, and similar. For niche areas the references do not cover, say so and point at the relevant OWASP source rather than guessing.

Agent-agnostic: works in Claude Code, Codex, Gemini CLI, and anything else that loads skills or reads `AGENTS.md`/`GEMINI.md`. Where this file names a tool, use your environment's equivalent.
