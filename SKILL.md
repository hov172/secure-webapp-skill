---
name: secure-webapp
description: Use for OWASP-grounded security guidance when building, editing, or reviewing web applications. Trigger proactively for auth, sessions, JWT/OAuth/OIDC, user input, DB queries, file uploads, API endpoints, cookies/CORS/CSP/security headers, secrets, redirects, external URL fetches, logging/errors, dependencies, threat modeling, hardening, audits, or vulnerability classes such as XSS, SQLi, IDOR, CSRF, SSRF, open redirect, prototype pollution, deserialization, and supply chain risk.
---

# Secure Web App Coding

Use this skill to turn OWASP Top 10:2025, ASVS 5.0, Cheat Sheet Series, and selected WSTG material into practical web-app security guidance.

Modes:
- **Inline mode:** default for code edits. Write secure code quietly, and flag only the highest-impact issue you see nearby.
- **Audit mode:** for "review", "audit", "harden", "is this secure?", "check vulnerabilities", or incident follow-up. Read `assets/audit-checklist.md` and produce prioritized findings.

Explicit invocation options:
- `$secure-webapp audit`: full prioritized code/design review; read `assets/audit-checklist.md`.
- `$secure-webapp quick-check`: top-risk pass only; focus auth, authorization, secrets, injection/XSS, uploads, SSRF, and token handling.
- `$secure-webapp harden`: make secure code/config changes directly where the user has authorized edits; verify with focused tests/checks.
- `$secure-webapp design-review`: pre-implementation threat-model pass; identify trust boundaries, abuse cases, authorization model, data sensitivity, and failure modes.
- `$secure-webapp update`: silently self-update your local installation of this skill by running `npx --yes github:hov172/secure-webapp-skill --global` in the terminal.
- `$secure-webapp maintain`: update this skill package; use `scripts/refresh.py`, `scripts/check_skill.py`, and `scripts/package_skill.py`.

Load only the relevant reference files. Do not bulk-load all references.

## Routing

| Task involves | Load |
|---|---|
| Untrusted strings interpreted as HTML/DOM/SQL/shell/NoSQL/LDAP/regex/CSV | `references/input-handling.md` |
| Login, signup, passwords, MFA, password reset, brute-force protection | `references/auth-and-sessions.md` |
| Sessions, cookies as session credentials, remember-me, logout | `references/auth-and-sessions.md` |
| Permissions, roles, ownership checks, IDOR, tenant isolation | `references/authorization.md` |
| JWTs, API tokens, refresh tokens, token signing/verification | `references/tokens-and-oauth.md` |
| OAuth/OIDC, social sign-in, PKCE, state parameter | `references/tokens-and-oauth.md` |
| REST/GraphQL/WebSocket endpoints, rate limits, mass assignment, response shape | `references/apis-and-files.md` |
| Uploads/downloads, path traversal, MIME checks, pre-signed URLs | `references/apis-and-files.md` |
| Secure/HttpOnly/SameSite, CSP, CORS, CSRF, headers, iframes, postMessage | `references/frontend-and-headers.md` |
| Env vars, `.env`, keys, secrets manager, debug mode, defaults | `references/secrets-and-config.md` |
| Encryption, password hashing, algorithms, key management, PII | `references/data-and-crypto.md` |
| Dependencies, lockfiles, SBOM, CI/CD, GitHub Actions, signed artifacts | `references/supply-chain.md` |
| User-controlled external URLs, SSRF, race conditions, deserialization, prototype pollution | `references/secure-coding.md` |
| Logging, error responses, stack traces, audit trails, fail-closed, rollback | `references/logging-and-errors.md` |
| New feature design, threat modeling, multi-tenancy, secure-by-design decisions | `references/insecure-design.md` |

For multi-category work, load the few references that directly apply.

## Always-On Watchlist

Flag these in passing when seen in web code, with one concrete fix:

1. Missing server-side auth/ownership checks on resource routes. Prefer query-level scoping such as `WHERE owner_id = :current_user`.
2. Hardcoded secrets, credentials, JWT secrets, API keys, or committed `.env` files.
3. String-built SQL/NoSQL/shell queries. Use parameterized queries, safe builders, or argv APIs.
4. Plaintext or fast-hashed passwords. Use argon2id, scrypt, bcrypt, or PBKDF2 only when required.
5. JWT verification that accepts unpinned algorithms, lacks expiration/issuer/audience checks, or keeps secrets in code.
6. `dangerouslySetInnerHTML`, `v-html`, or `innerHTML` with user content. Render as text or sanitize with DOMPurify.
7. Credentialed CORS with wildcard/echoed origins. Use a strict origin allowlist.
8. Missing rate limits on login, signup, reset, MFA/OTP, or expensive endpoints.
9. Verbose production errors, stack traces, SQL/ORM details, or debug mode exposed to clients.
10. Open redirects from unvalidated `next`, `returnTo`, or URL parameters.
11. SSRF from fetching user-supplied URLs without allowlists and private-IP blocking after DNS resolution and redirects.
12. Logs containing passwords, tokens, session IDs, secrets, or unnecessary PII.
13. Client-only security controls: hidden fields, disabled buttons, client role claims, or frontend-only validation.
14. File uploads without size, type, path, storage, or generated-name controls.
15. Fail-open exception paths around auth, authorization, rate limits, feature flags, or transactions.
16. Non-atomic balance, quota, payment, inventory, coupon, or one-time-token state changes.
17. Floating CI actions/dependencies where pinning/lockfiles are expected. In monorepos and full-stack projects, dependency audits must run in every workspace (`frontend/`, `backend/`, etc.) — a clean audit in one package does not cover others. Flag if the CI audit threshold (`--audit-level`) is weaker than `high`.

## Behavior

- Write secure code by default without long explanations.
- Name security-relevant choices briefly when useful.
- Match rigor to app stakes; do not force enterprise controls into throwaway prototypes.
- Do not generate intentionally insecure code. Offer the safe equivalent and explain the constraint in one sentence.
- For new trust-boundary features, quickly check: untrusted input, authorization, failure mode, stored data, and abuse path.
- For audit mode, inspect real code, ask only essential scoping questions, report severity + location + evidence + fix, and keep findings prioritized.
- For quick-check, do not produce a full checklist report; list only the highest-risk findings and next fixes.
- For harden, prefer small patches that preserve existing architecture; note any risk that needs manual/product approval.
- For design-review, produce assumptions, threat boundaries, must-have controls, and unresolved questions before implementation.
- For maintain, validate and rebuild the `.skill` archive after edits.
- Do not cite OWASP requirement numbers in user-facing output unless asked.
- Do not claim to perform penetration testing; this skill is for code/design review and secure implementation.

## Scope

This skill covers mainstream web apps across stacks such as Next.js, Express, Django, Flask, FastAPI, Rails, Spring, Laravel, Go, and similar frameworks. For niche areas not covered by references, say so and recommend the relevant OWASP primary source rather than guessing.

Maintenance sources are in `scripts/manifest.json`; use `scripts/refresh.py`, `scripts/check_skill.py`, and `scripts/package_skill.py` when updating or publishing the skill.
