# Audit Checklist

Use for security reviews, audits, hardening passes, or incident follow-up. Inspect real code; do not audit hypothetically. Keep findings specific: file/line, evidence, impact, fix.

If invoked as `$secure-webapp quick-check`, review only the highest-risk areas: authorization, auth/session handling, secrets, injection/XSS, uploads/downloads, SSRF/external fetches, and token/OAuth handling.

## Scope First

Ask only what is needed: app purpose/users, handled data (auth, PII, payments, uploads, multi-tenant), stack/auth provider/DB/hosting, deployment stakes, and any specific concern.

Severity:
- **Critical:** exploitable now with serious impact: breach, account takeover, RCE, cross-tenant write. Fix this week.
- **High:** exploitable with material impact: auth bypass, persistent XSS, sensitive leak. Fix this sprint.
- **Medium:** real but conditional or limited-impact risk. Fix this quarter.
- **Low:** limited best-practice gap. Track.
- **Info:** observation only.

## Walkthrough

Check in this order; load named references for depth only when needed.

1. **Authorization / Access Control** (`references/authorization.md`, SSRF in `references/secure-coding.md`)
   Look at every route touching user/tenant data. Common findings: no auth middleware, IDOR from fetch-by-ID without ownership scope, client-only admin checks, mass assignment, bulk IDs not scoped, resource-existence leaks, SSRF from user-controlled URLs.

2. **Authentication / Sessions** (`references/auth-and-sessions.md`)
   Review login, signup, reset, MFA, session creation/logout. Findings: weak/fast password hashing, username enumeration, missing auth rate limits, reset tokens unhashed/no expiry/reusable, predictable session IDs, weak session cookies, no session rotation, logout not invalidating server state.

3. **Secrets / Config** (`references/secrets-and-config.md`)
   Check source, `.gitignore`, history, env handling, prod config. Findings: hardcoded keys/passwords/JWT secrets, committed `.env`, shared dev/prod secrets, debug mode or stack traces in prod, default credentials, public admin interfaces.

4. **Input / Injection / XSS** (`references/input-handling.md`)
   Trace user input into queries, commands, templates, DOM, CSV. Findings: string SQL/NoSQL, shell execution with user input, unsafe HTML sinks, missing schema/length validation, CSV formula injection.

5. **Files and APIs** (`references/apis-and-files.md`)
   Check uploads/downloads, public APIs, GraphQL, WebSocket. Findings: no upload size/type/magic-byte checks, path traversal, uploads in web root, SVG served inline, long-lived pre-signed URLs, missing API rate limits/pagination/max page size, sensitive response fields, missing CSRF on cookie-auth state changes.

6. **Frontend / Browser Controls** (`references/frontend-and-headers.md`)
   Check headers, cookies, CORS, redirects, DOM patterns. Findings: missing/weak CSP, script `unsafe-inline`, no HSTS, credentialed wildcard/echo CORS, missing nosniff/frame/referrer headers, weak cookies, open redirects, third-party scripts without SRI.

7. **Tokens / OAuth** (`references/tokens-and-oauth.md`)
   Check JWT verification, OAuth flows, token storage. Findings: unpinned JWT alg, weak/source secrets, missing `exp`/`iss`/`aud`, browser tokens in `localStorage`, implicit flow, missing OAuth `state`, loose `redirect_uri`, plaintext API keys in DB.

8. **Crypto / Data Protection** (`references/data-and-crypto.md`)
   Check encryption, randomness, TLS, retention. Findings: ECB or unauthenticated CBC, non-CSPRNG security tokens, hardcoded keys, TLS verification disabled, sensitive data unencrypted where warranted, no retention/deletion path.

9. **Supply Chain** (`references/supply-chain.md`)
   Check lockfiles, dependency scan output, CI/CD, actions, artifacts. Findings: missing lockfiles, vulnerable deps, floating GitHub Actions, untrusted postinstall scripts, long-lived CI cloud secrets, no deploy approvals, no SBOM/provenance.

10. **Design / Business Logic** (`references/insecure-design.md`)
    Look for flaws implementation cannot patch locally. Findings: UI-only authorization, client-trusted state, no credential/key rotation path, single-tenant design reused as multi-tenant, server-side state machines missing, non-atomic money/quota/coupon flows, no abuse controls on signup/login/expensive endpoints.

11. **Errors / Logging / Exceptional Conditions** (`references/logging-and-errors.md`)
    Check failure paths and logs. Findings: catch-all returns success, security controls fail open, multi-step operations lack transactions, no cleanup on exceptions, missing timeouts/circuit breakers, secrets in logs, stack traces in responses, missing security-event logs/alerts.

## Report Format

Use:

```markdown
## Security Review Summary
Scope: ...
Method: static review / dynamic testing / both

## Critical Findings
1. Title — path:line
   Evidence: ...
   Impact: ...
   Fix: ...

## High Findings
...

## Medium / Low / Info
...

## Not Reviewed
...

## Roadmap
This week: ...
This month: ...
Eventually: ...
```

Rules: prioritize real risk, avoid padding, show small code fixes when useful, state what was not tested, and calibrate to the app’s stakes.
