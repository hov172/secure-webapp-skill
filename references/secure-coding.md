# Secure Coding & Architecture

Covers OWASP ASVS V15 (Secure Coding and Architecture) and most of V12 (Secure Communication). Catch-all for things that don't fit cleanly into the other references — defensive coding, SSRF, race conditions, deserialization hazards.

> **Note on 2025 Top 10 framing:** SSRF was a standalone Top 10 entry (A10) in 2021 but in the 2025 edition was consolidated into A01 (Broken Access Control), recognizing that SSRF is fundamentally an access-control failure where the attacker tricks your *server* into accessing things on their behalf. Cross-link to `authorization.md` for the broader access-control framing. Software supply chain content moved to its own reference (`supply-chain.md`) since it was elevated to A03 in 2025.

## OWASP source sync

Deterministic notes regenerated from the refreshed OWASP source cache.

- SSRF: allowlist destinations and block private IPs after DNS resolution.
- Redirects: re-check every hop and reject unsafe schemes.
- Deserialization: keep untrusted data in safe formats such as JSON.
- Prototype pollution: strip dangerous keys before merging untrusted objects.

## SSRF: Server-Side Request Forgery

The threat: your server makes an HTTP request to a URL controlled by user input. Possible flavors:

- **Cloud metadata exfiltration:** `http://169.254.169.254/latest/meta-data/iam/security-credentials/` returns AWS instance role credentials. (Or the equivalent on GCP, Azure.) IMDSv2 mitigates but isn't universal.
- **Internal network reconnaissance and exploitation:** the user supplies `http://10.0.0.5:8080/admin` and your app fetches it on their behalf, with whatever internal access your server has.
- **Localhost services:** Redis on localhost, internal admin APIs.
- **Proto smuggling:** `gopher://`, `file://`, `dict://` URIs accepted by overly permissive HTTP libraries.

Where this hits in real apps:

- "Image proxy" features.
- Webhooks (the user gives you a URL, you POST to it).
- "Fetch URL" features (URL previews, OG image scraping).
- AI agents that fetch tools or follow links.
- PDF generators that load stylesheets/images by URL.
- SSO IdP discovery endpoints.
- Server-side render of user content with embedded iframes/images.

### Defenses

For any URL fetch from user input:

1. **Allowlist destinations** if possible. "URL must be on this list of approved domains."
2. **Block private IP ranges** — and block them after DNS resolution, not just by string match. The attacker can register `evil.com` resolving to `127.0.0.1`. Resolve the host, check the IP, then connect to that IP (with the original Host header). Block:
   - `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16` (RFC1918)
   - `127.0.0.0/8`, `0.0.0.0`
   - `169.254.0.0/16` (link-local, includes cloud metadata)
   - `100.64.0.0/10` (CGNAT)
   - Multicast, broadcast
   - IPv6 equivalents: `::1`, `fc00::/7`, `fe80::/10`, `::ffff:0:0/96` (IPv4-mapped — and check the embedded IPv4 too)
3. **Limit protocols** to `http://` and `https://`. Reject `file://`, `gopher://`, `dict://`, etc.
4. **Don't follow redirects** to disallowed destinations. A 302 to `http://169.254.169.254/...` bypasses defenses if redirects are followed without re-checking. Either disable redirects or re-validate at each hop.
5. **Use a hardened HTTP client** — libraries like `ssrf-req-filter` (Node), `socksio` + custom resolver (Python), or run egress traffic through an outbound proxy that enforces destination policy.
6. **For metadata services specifically:** require IMDSv2 on AWS instances; use Workload Identity on GCP; use Managed Identity on Azure — these all require special headers / setup that an SSRF can't easily replicate.
7. **Egress firewall.** A network policy that prevents your app servers from reaching arbitrary internal IPs is the strongest defense — it works even if the application code is wrong.

For webhooks specifically, an additional layer: queue the webhook delivery, verify the URL passes SSRF checks, and execute from a worker with restricted egress.

## Open redirects

The threat: `https://yourapp.com/login?next=https://evil.com` — after login, the user is redirected to `evil.com`. Phishers love these because the link starts at your real domain.

Defenses:

- **Allowlist redirect destinations.** Only relative paths within your app, or specific known external hosts.
- **Reject schemes other than `https://`** (and explicitly `javascript:` and `data:`).
- **Reject protocol-relative URLs** (`//evil.com`) — they're treated as absolute by browsers.
- **Be careful with URL parsing.** `urlparse('https://evil.com\\@yourapp.com')` parses differently in different libraries; use a strict, modern parser and validate the host explicitly.

## Race conditions and TOCTOU

Time-of-check / time-of-use bugs in web apps usually look like:

```python
# BUG
balance = get_balance(user_id)
if balance >= amount:
    deduct(user_id, amount)
    credit(recipient_id, amount)
```

Two concurrent requests for `amount = 100` with `balance = 100` both pass the check, both deduct → balance becomes negative.

Fixes:

- **Database transactions with appropriate isolation.** Wrap the check and update in a transaction; use `SELECT ... FOR UPDATE` or compare-and-swap (`UPDATE accounts SET balance = balance - 100 WHERE id = ? AND balance >= 100`).
- **Idempotency keys** for state-changing operations from clients. Client supplies a unique key per logical operation; server stores results keyed by it; replays return the original result.
- **Distributed locks** (Redis with proper expiry, dedicated locking service) only when database constraints don't suffice. A naive Redis SETNX without expiry leaks lock state when the holder crashes.

This is also why "check then write" patterns (`if not exists, create`) need to be either an atomic upsert (`INSERT ... ON CONFLICT`, `INSERT IGNORE`) or wrapped in a transaction.

## Defensive coding patterns

### Fail safely, fail closed

When something unexpected happens, the secure default is to deny. Some things to watch for:

- A try/except that silently catches everything and returns success.
- An auth check that returns `True` if it can't reach the auth service.
- A feature flag check that defaults to "feature on" (and the feature is dangerous).

### Don't trust filesystem layouts

If your code constructs paths with `os.path.join(base, user_input)`, the user can pass `..` or absolute paths and escape `base`. Resolve and check (see `apis-and-files.md` for path traversal).

### Constant-time comparison for secrets

Comparing secrets (HMAC values, password hashes already on disk being compared to known good, tokens) with `==` can leak via timing — early character mismatches return faster. Use:

- Python: `hmac.compare_digest`
- Node: `crypto.timingSafeEqual`
- Go: `crypto/subtle.ConstantTimeCompare`
- Java: `MessageDigest.isEqual`

### Avoid serialization-based RCE

Deserializing untrusted data with libraries that can construct arbitrary objects is a classic RCE:

- **Python:** `pickle`, `cPickle`, `pyyaml.load` (without SafeLoader), `marshal` — all dangerous on untrusted input. Use `json`, `pyyaml.safe_load`, `tomllib`.
- **Java:** `ObjectInputStream` on untrusted data is RCE; many gadget chains exist. Use JSON or schema-based serializers (Jackson with safe defaults).
- **Ruby:** `Marshal.load`, `YAML.load` (without `permitted_classes`) — dangerous. Use `JSON.parse`, `YAML.safe_load`.
- **PHP:** `unserialize` on untrusted input.
- **.NET:** `BinaryFormatter` is deprecated; avoid all formatters that allow type-controlled deserialization on untrusted input.

When in doubt, use JSON. It can't construct arbitrary types.

### Avoid prototype pollution (JS)

In JavaScript, deeply-merging untrusted JSON into objects can pollute `Object.prototype`:

```javascript
// vulnerable: input { "__proto__": { "isAdmin": true } } merged into config
deepMerge(config, JSON.parse(req.body));
```

Use libraries that explicitly prevent this (newer `lodash.merge` does), or sanitize input by stripping `__proto__`, `constructor`, `prototype` keys, or use `Object.create(null)` for dictionaries that hold untrusted data.

### Avoid `eval`, `new Function`, `vm.runInContext` on untrusted strings

Beyond the obvious. Includes templating engines used as `engine.render(userTemplate, data)` — the *template* must be a known string, the *data* is the input.

## Concurrency for systems making external calls

When your app calls external services:

- **Timeouts on every call.** No timeout = your service is at risk of cascading failures and DoS. 5-30 seconds for typical HTTP calls; less for fast services.
- **Retries with backoff and jitter** for idempotent operations only. Retrying a non-idempotent POST without idempotency keys = duplicate state changes.
- **Circuit breakers** for high-volume external dependencies (resilience4j, polly, hystrix-equivalents). When the dependency is dead, fail fast rather than queueing.

These are also security concerns — an attacker noticing your app blocks for a long time on a downstream call can amplify a DoS.

## Logging and observability — security-relevant

Covered in detail in `logging-and-errors.md`, but in this context:

- **Log security-relevant events:** auth successes, failures, MFA enrollment, password changes, permission changes, suspicious access patterns.
- **Don't log secrets, tokens, passwords, full request bodies on auth endpoints, full credit card numbers, etc.**
- **Centralize logs** so an attacker who compromises one server can't easily cover their tracks.

## Service-to-service communication (V12 highlights)

Beyond user-facing TLS:

- **Authenticate service-to-service traffic.** mTLS via service mesh (Istio, Linkerd), or signed requests, or short-lived workload tokens (SPIFFE/SPIRE), or cloud IAM (signed AWS SigV4 to internal endpoints).
- **Don't assume internal == trusted.** Lateral movement after a compromise is the standard attacker playbook.
- **Validate certificates.** Don't disable TLS verification for "internal" endpoints. The biggest "internal-only" cert mistakes are also the most common breach origins.

## Quick checklist

URL fetches from user input:
- [ ] Allowlist destinations or strict private-IP block (post-DNS resolution)
- [ ] Protocol allowlist (`http`, `https` only)
- [ ] Redirects either disabled or re-validated each hop
- [ ] Egress firewall as defense in depth

State changes:
- [ ] Atomic database operations (transactions, conditional updates) for shared resources
- [ ] Idempotency keys on POSTs that aren't naturally idempotent
- [ ] Sensible timeouts on every external call

Defensive coding:
- [ ] Fail closed on errors in security-relevant paths
- [ ] Constant-time comparison for token/HMAC equality
- [ ] No `pickle`/`yaml.load`/Java ObjectInputStream on untrusted data
- [ ] No `eval`/`new Function` on user content
- [ ] Path traversal defenses on any user-influenced filesystem operation

Service-to-service:
- [ ] Authenticated, encrypted (mTLS or equivalent)
- [ ] Cert verification not disabled
