# Logging, Error Handling, and Exceptional Conditions

Covers OWASP ASVS V16 (Security Logging and Error Handling) plus OWASP Top 10 2025 A09 (Security Logging & Alerting Failures) and A10 (Mishandling of Exceptional Conditions). Logs are dual-purpose: they're how you detect and respond to security incidents, and they're a common channel for accidentally leaking the secrets you're trying to protect. Exceptional conditions — what happens when something goes wrong — became its own Top 10 category in 2025 because failing open, leaking errors, and mishandling partial-completion states are how a surprising number of vulnerabilities actually land.

## OWASP source sync

Deterministic notes regenerated from the refreshed OWASP source cache.

- Errors: do not leak stack traces or sensitive implementation details to clients.
- Logs: capture security-relevant events, but never secrets or raw auth payloads.
- Observability: centralize logs so incidents can be traced and alerted on.

## What to log

The minimum useful security log includes:

- **Authentication events:** login success, login failure (with username — for attack pattern detection), logout, MFA challenges, password resets, password changes.
- **Authorization decisions on sensitive actions:** admin actions, role/permission changes, access to other tenants' data (admin override).
- **Account lifecycle:** signup, account deletion, email change, MFA enrollment changes.
- **Access to sensitive data:** for HIPAA/PCI/SOX-scoped apps, every read of a regulated record may need to be logged.
- **Suspicious behavior:** rate limit hits, repeated 4xx from a single IP, unusual access patterns.
- **Server errors and exceptions:** with enough context to debug, but without secrets.
- **Configuration changes:** especially for prod systems.

For each event, include: timestamp (with timezone, ideally UTC), event type, user/principal ID (or anonymous identifier), source IP, user-agent, request ID for correlation, and outcome (success/failure/reason).

## What NEVER to log

The most dangerous logs are the ones that quietly leak secrets. Common patterns to grep for and remove:

- **Password fields.** `console.log(req.body)` on a login route logs the user's password. Wrap or redact before logging.
- **Authorization headers.** `Authorization: Bearer ...` ends up in proxy logs, error reports, request loggers. Most logging libraries have header redaction config — turn it on.
- **Session IDs and cookies.** A logged session ID is a stolen session. Some frameworks log full cookies on errors.
- **JWTs and API tokens.** If a token is in a query parameter (don't put tokens in URLs!) it'll show up in access logs and Referer headers. Even in headers, redact.
- **Password reset tokens, email verification tokens, OAuth codes.**
- **Cryptographic keys, encryption keys.**
- **Full credit card numbers.** Last 4 digits at most.
- **Sensitive PII** beyond what's necessary — full SSN, government IDs, health data, security questions and answers.
- **Internal stack traces sent to error-reporting services** that include local variable contents (Sentry's "Include Local Variables" feature is convenient and dangerous — review what's captured).

Strategies:

- **Allowlist what's logged**, not blocklist. Log specific fields you've decided are safe.
- **Use structured logging** (JSON) with explicit fields, not interpolated strings — easier to redact at the field level.
- **Use a logging middleware that masks known-sensitive headers and body fields.**
- **Periodically grep production logs** for things that look like secrets (e.g., `Bearer eyJ`, `password`, JWT-shaped strings) and fix the source.

## Where logs go

- **Centralized log aggregation.** (CloudWatch, Datadog, Loki, ELK, Splunk.) Local-only logs get destroyed on incident response — sometimes by attackers, sometimes by routine cleanup.
- **Logs leave the host promptly.** A few seconds of delay is fine; minutes/hours mean an attacker can rm the file before it's shipped.
- **Logs are write-once / append-only** in storage. Most cloud logging services support immutability or retention locks.
- **Access to logs is audited** itself. Especially for production logs containing user data.

## Log retention

- **Long enough to investigate incidents** (typically 90 days minimum for security logs, often longer for compliance).
- **Not so long that PII accumulates indefinitely** — privacy regulations may require deletion windows.

## Error handling: what the user sees vs. what's logged

The two audiences:

- **The user (or attacker)** sees a generic message: "Something went wrong. Reference: a3f8c1." A reference ID lets the user file a support ticket; the full error stays internal.
- **The logs / observability platform** see the full stack trace, request context, and any debugging information needed.

What this looks like in practice:

```python
@app.errorhandler(Exception)
def handle_uncaught(e):
    error_id = uuid.uuid4().hex
    logger.exception("Unhandled exception", extra={
        "error_id": error_id,
        "user_id": getattr(g, "user_id", None),
        "path": request.path,
    })
    if is_production():
        return jsonify({
            "error": "internal_error",
            "reference": error_id,
        }), 500
    else:
        # In dev, propagate the exception
        raise
```

```javascript
app.use((err, req, res, next) => {
  const refId = crypto.randomUUID();
  logger.error({ refId, userId: req.user?.id, path: req.path, err });
  res.status(500).json({
    error: 'internal_error',
    reference: refId,
  });
});
```

Things to make sure of:

- **No stack traces, SQL errors, ORM messages, framework-version strings, or library names in the response body.**
- **Same error response for distinct internal failures** when it would aid attackers to differentiate. (E.g., login failures should look the same regardless of whether the username exists or the password was wrong.)
- **A 5xx is a 5xx.** Don't return a 200 with `{"error": "..."}` when something went genuinely wrong; status codes carry meaning to clients and monitoring.

## Validation errors

For 4xx user errors, returning specific information is fine and useful — `{"error": "email_invalid", "field": "email"}` helps the user fix the problem. Just be careful that "specific" doesn't leak system internals or other users' data:

- "Email already registered" on signup may leak that an email is registered. For some apps that's acceptable; for others (security-sensitive: dating, mental health, HR, etc.) you should not confirm the email's presence; instead, send a normal "verify your email" flow that emails the existing user "someone tried to register your email."
- "Invalid SQL" obviously bad.
- "Account locked due to too many failed attempts" may help an attacker confirm they hit a real account.

## Mishandling of exceptional conditions

OWASP Top 10 2025 A10 calls out a class of vulnerabilities that aren't really about a single bug — they're about how systems behave when something unexpected happens. The pattern: code is written for the happy path, the failure path is an afterthought, and that failure path becomes the security gap.

### The three failure modes

**Failing open instead of failing closed.** When something the security control depends on isn't available (auth service down, database unreachable, key not loadable), the secure default is to deny — not to allow. Examples of failing open:

```python
# DANGEROUS — auth service unreachable becomes "user is authenticated"
def check_auth(token):
    try:
        return auth_service.verify(token)
    except Exception:
        return True   # silently allows everything when auth is down

# DANGEROUS — feature flag check defaults to enabled
def is_feature_enabled(flag, user):
    try:
        return flags.get(flag, user)
    except Exception:
        return True   # the dangerous feature gets enabled on flag service hiccup
```

The fix:

```python
def check_auth(token):
    try:
        return auth_service.verify(token)
    except Exception:
        log.exception("auth verify failed")
        return False  # fail closed
```

The same logic applies to authorization checks, MFA verifications, rate-limit checks, and any other security control. If the answer "I don't know" can come back from the check, the surrounding code should treat that as "no."

**Partial-completion state corruption.** A multi-step operation gets interrupted mid-way: account A debited, account B not credited yet, log entry not written. If the operation isn't transactional, the database now contains a state that violates the invariants of the system, and an attacker can exploit the gap.

```python
# DANGEROUS — three independent operations, no transaction
def transfer(from_id, to_id, amount):
    accounts.debit(from_id, amount)
    # network blip here = money disappears
    accounts.credit(to_id, amount)
    audit_log.write(from_id, to_id, amount)

# FIXED — single atomic transaction with rollback on failure
def transfer(from_id, to_id, amount):
    with db.transaction():
        accounts.debit(from_id, amount)
        accounts.credit(to_id, amount)
        audit_log.write(from_id, to_id, amount)
    # If anything raises, all three are rolled back
```

For operations that span systems (e.g., charging Stripe + recording in your DB), atomicity is harder. Patterns:

- **Idempotency keys.** Client provides a stable key per logical operation. Server stores results keyed by it; replays return the original outcome. Lets the client safely retry on network failure.
- **Two-phase / saga patterns.** Explicitly model the steps and the compensating actions if a later step fails (e.g., refund the Stripe charge if the DB write fails). Use a workflow engine (Temporal, Inngest, AWS Step Functions) for non-trivial cases — rolling your own is prone to subtle bugs.
- **Outbox pattern.** Local DB transaction writes the intent ("send email to X"); a separate worker processes the outbox. The DB transaction succeeds or rolls back atomically; the side effect happens after, with retries.

**Resource cleanup on exception.** Files opened, locks acquired, network connections, transactions, temp directories — anything that needs explicit cleanup. Exception in the middle leaves the resource leaked. Patterns:

```python
# DANGEROUS
def process_upload(file):
    f = open(temp_path, 'wb')
    f.write(file.read())  # if this raises, file handle leaks
    process(f)
    f.close()

# FIXED — context manager guarantees cleanup
def process_upload(file):
    with open(temp_path, 'wb') as f:
        f.write(file.read())
        process(f)
```

```javascript
// DANGEROUS — lock acquired, exception in middle, lock never released
const release = await lock.acquire();
await criticalSection();
release();

// FIXED
const release = await lock.acquire();
try {
  await criticalSection();
} finally {
  release();
}
```

For locks, file handles, DB connections, and the like, use the language's resource-management construct (`with` in Python, `try-finally` in JS, `defer` in Go, `using` in C#, RAII in Rust/C++). For HTTP request lifecycles, the framework usually handles this — but custom long-lived connections (WebSockets, SSE) need explicit cleanup on disconnect.

### Practical defenses

- **Centralize exception handling.** A global exception handler at the framework level catches everything that escapes individual handlers, logs it with a reference ID, and returns a generic error response. Per-route try/except is for handling expected errors specifically; the global handler is the safety net.
- **Catch specific exceptions, not generic ones.** `except Exception:` and `catch (e) {}` swallow bugs. Catch the specific exception you know how to handle; let the rest propagate to the global handler.
- **Don't hide errors.** A try/except that catches and silently returns a default value hides bugs that would otherwise be reported. If you must catch, log and propagate or return a value the caller knows is an error indicator.
- **Test the failure paths.** "What happens if Stripe times out?" should have a test, not a hope. Most "exceptional condition" bugs are found by chaos testing or by accident in prod.
- **Resource limits everywhere.** Timeouts on HTTP calls, max retries with backoff, DB connection pool caps, rate limits on expensive operations. Unlimited resources is itself an exceptional-condition bug — it just hasn't fired yet.
- **Don't repeat the same error in logs at high rate.** If a function fails 10,000 times per minute, log it once with a counter, not 10,000 times. Otherwise the log itself becomes a DoS on the log aggregation system.

### Common patterns by category

For **auth/authz failures** — fail closed, log the failure event, return generic 401/403, don't reveal why.

For **DB failures** — let transactions roll back; surface a generic 5xx with a reference; don't return SQL errors to the client.

For **third-party service failures** — circuit breakers (don't keep retrying a known-dead service); fall back to degraded mode where possible (cached value, default behavior); fail closed where security-relevant (don't process payment if fraud-check is down).

For **memory/resource exhaustion** — set explicit limits before they're exhausted (max body size, max concurrent connections, max upload size); when limits hit, return 429 or 503 with backoff; don't crash the process if you can avoid it.

For **input validation failures** — return 400 with a specific error code; don't log the full request body (PII / token leak); rate-limit the source if many bad requests in a row.

## Audit logging vs. application logging

For sensitive applications (financial, healthcare, B2B SaaS with admin actions), keep an *audit log* that's distinct from regular application logs:

- **Tamper-evident** — append-only, possibly with hash chaining or a service that prevents post-hoc edits.
- **Long retention** — typically years, per regulation.
- **Access controlled** — separate from operational logs; usually only security/compliance can read.
- **Limited fields** — exactly the events that matter (who did what to which resource when), not arbitrary debug noise.

For the average web app this is overkill. For anything with regulated or high-stakes data, build it from day one — retrofitting an audit log is much harder.

## Monitoring and alerting

Logs without monitoring are evidence after the fact, not prevention. The minimum useful alerts:

- Surge in authentication failures (per IP, per account, globally)
- Surge in 5xx error rates
- New IP / device login from a privileged user
- Failed authorization attempts (especially repeated)
- Unusual data exfiltration patterns (long page sizes, sustained reads)
- Critical service health (database, cache, auth provider)

Tune to your false-positive tolerance — bad alerting is worse than no alerting because it trains responders to ignore.

## Quick checklist

What gets logged:
- [ ] Authentication events with outcome
- [ ] Authorization decisions on sensitive actions
- [ ] Account lifecycle changes
- [ ] Server-side exceptions with full context
- [ ] Each event has timestamp, principal, source IP, request ID, outcome

What's redacted/excluded:
- [ ] Passwords, tokens, session IDs, JWTs, API keys
- [ ] Authorization headers
- [ ] Full credit card numbers, SSNs, health data
- [ ] Stack traces never returned to clients in prod

How logs flow:
- [ ] Centralized aggregation; logs leave hosts promptly
- [ ] Append-only / tamper-evident storage for audit logs
- [ ] Retention defined per category (security, audit, access)
- [ ] Alerts on auth surges, error surges, suspicious patterns

Error responses:
- [ ] 5xx responses are generic with a reference ID; full error in logs only
- [ ] No framework version, stack trace, or internal details in response bodies
- [ ] Status codes accurately reflect outcome
