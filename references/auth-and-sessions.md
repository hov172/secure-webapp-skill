# Authentication & Session Management

Covers OWASP ASVS chapters V6 (Authentication) and V7 (Session Management). Plus password storage, which technically lives in V11 but is too tightly coupled to auth to separate.

## The threat model in plain terms

Authentication answers "who is this?" Session management answers "is this the same who across requests?" Both must be impersonation-resistant. The realistic attackers a typical web app faces:

- **Credential stuffers** — automated login attempts using passwords leaked from other breaches. Affects everyone.
- **Phishers** — trick users into entering credentials on a lookalike site.
- **Session hijackers** — steal a session cookie via XSS, network sniffing, or shared devices.
- **Brute-forcers** — try a billion passwords against one account. Usually mitigated by lockout and slow hashing.
- **Insiders / DB-leak attackers** — get a copy of the DB and want to crack hashes offline.

Threat model first because it tells you what level of rigor is justified. A weekend hackathon project doesn't need WebAuthn; a healthcare app does.

## Use a battle-tested auth provider when you can

The single most important sentence in this file: **most apps should not implement auth from scratch.** Clerk, Auth0, Supabase Auth, AWS Cognito, Firebase Auth, NextAuth/Auth.js, Devise (Rails), django-allauth, and similar tools have absorbed thousands of person-years of attack research. They handle password hashing, MFA, session lifecycle, account recovery, OAuth integration, breached-password checks, and rate limiting in ways that are extremely hard to replicate without bugs.

Use a library/service unless there's a real reason not to. The rest of this document covers what you still need to think about even when using one (a lot — they're not magic), and what to do if you must roll your own.

## Password handling

### Storage: use a slow, salted, memory-hard KDF

The only acceptable algorithms for password storage in 2025+:

1. **argon2id** (preferred). Modern, memory-hard, designed for password hashing.
2. **scrypt** — also memory-hard, well-vetted.
3. **bcrypt** — older but still acceptable. Cap input at 72 bytes (bcrypt truncates) — pre-hash with SHA-256 if you need longer support, but be careful about null bytes.
4. **PBKDF2-HMAC-SHA256** — acceptable in FIPS-required environments. Needs high iteration counts.

What you must NOT use: MD5, SHA-1, SHA-256, SHA-512 alone (regardless of salting). Plain hash functions are designed to be fast — exactly the wrong property.

```python
# Python: argon2-cffi (preferred) or passlib
from argon2 import PasswordHasher
ph = PasswordHasher()  # sensible defaults
hashed = ph.hash(password)
ph.verify(hashed, password)  # raises on mismatch
```

```javascript
// Node: argon2 package (preferred)
import argon2 from 'argon2';
const hash = await argon2.hash(password, { type: argon2.argon2id });
const ok = await argon2.verify(hash, password);

// Or bcrypt (acceptable)
import bcrypt from 'bcrypt';
const hash = await bcrypt.hash(password, 12);
const ok = await bcrypt.compare(password, hash);
```

Salt is generated and stored automatically by these libraries. Don't try to manage it separately.

### Password policy: length, not character classes

Modern guidance (NIST SP 800-63B, OWASP):

- **Minimum length: 8** for low-stakes apps, 10–12 for sensitive apps. Allow at least 64 characters maximum (passphrases are great).
- **Allow all printable Unicode**, including spaces and emoji. Don't strip or truncate.
- **Verify the password exactly as submitted.** No silent lowercasing, no whitespace trimming beyond at the very edges if absolutely necessary, no case normalization.
- **Don't impose composition rules** (must contain digit + symbol + uppercase). They reduce entropy in practice because users follow predictable patterns.
- **Don't expire passwords** on a schedule. Rotate only when there's evidence of compromise.
- **Check against known breach corpora.** Use HaveIBeenPwned's k-anonymity API or equivalent on signup and password change. Reject passwords that appear in breach lists.

### Account lockout and rate limiting

Brute force is mitigated by a combination of:

- **Slow hashing** — already covered above. argon2id at sane parameters means an attacker gets ~10 guesses/second per CPU.
- **Rate limiting per IP** — limit login attempts per IP. Don't be too tight (a coffee shop NAT shares IPs).
- **Rate limiting per account** — separate counter for failed attempts on a given username. Tighter than per-IP.
- **Soft lockout** — after N failures, require CAPTCHA or impose a delay; don't permanently lock (it becomes a DoS vector against the user).
- **Notify the user** of suspicious activity by email — successful login from a new device, password change, MFA enrollment changes.

Don't reveal whether a username exists. The login error should be the same for "wrong password" and "no such user". Same for password reset — "if an account exists with that email, we sent a link".

### Password reset

The classic flow:

1. User submits email. Always show the same success message regardless of whether the email is registered.
2. If registered, generate a high-entropy reset token (≥128 bits from a CSPRNG), store its **hash** in the DB along with `user_id`, `created_at`, and `expires_at` (15–60 minutes).
3. Email the user a link with the raw token.
4. On click, verify the token (constant-time compare against the hash), check expiry, mark used.
5. Allow setting a new password. Invalidate all existing sessions for that user after a password reset.

Things that go wrong:
- Predictable tokens (using Math.random or sequential IDs). Use `crypto.randomBytes(32)` / `secrets.token_urlsafe(32)`.
- Storing the token in plaintext. If the DB leaks, all open reset links work.
- Long expiration windows (24h+). Tokens are bearer credentials.
- Reusable tokens. Mark used immediately.
- Not invalidating existing sessions. An attacker with a stolen session keeps it after the user resets.

### MFA / 2FA

For anything beyond a hobby project, support MFA. Order of preference:

1. **WebAuthn / passkeys (FIDO2)** — phishing-resistant, no shared secret. The future.
2. **TOTP** (Google Authenticator, Authy, 1Password) — shared secret, but no shared secret with the network. Strong against remote attackers, weak against phishing.
3. **Push-based** (e.g., Duo) — convenient but vulnerable to MFA fatigue attacks unless number-matching is enforced.
4. **SMS / email codes** — better than nothing but vulnerable to SIM swapping and email compromise. Don't use as the only second factor for sensitive accounts.

When implementing TOTP: store the shared secret encrypted at rest, generate via QR code, allow a small time window (±1 step) for clock drift, and lock the account after several failed codes.

Allow users to register multiple factors and provide backup codes (one-time, hashed at rest, generated as a set of 10).

## Session management

### Session storage: server-side vs. self-contained tokens

Two main models:

1. **Opaque session ID** stored in a cookie, with session state in a server-side store (Redis, DB, signed cookie). Easiest to invalidate. Default for most server-rendered apps.
2. **Self-contained tokens** (JWT or similar) — see `tokens-and-oauth.md`. Stateless but harder to revoke; require care.

For a typical web app: prefer opaque session IDs in cookies backed by a server store unless you have a specific reason to go stateless.

### Cookie settings

The session cookie must have:

- `Secure` — only sent over HTTPS.
- `HttpOnly` — not accessible from JavaScript (mitigates XSS-based theft).
- `SameSite=Lax` (or `Strict` for high-sensitivity actions) — mitigates CSRF.
- A reasonable `Path` (often `/`).
- An explicit name without identifying the framework (avoid `PHPSESSID`, `JSESSIONID` defaults — they tell attackers the stack).

```javascript
// Express
res.cookie('sid', sessionId, {
  httpOnly: true,
  secure: true,
  sameSite: 'lax',
  maxAge: 1000 * 60 * 60 * 8, // 8 hours
});
```

```python
# Django settings
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
```

### Session ID generation

- **Random and unguessable** — at least 128 bits of entropy from a CSPRNG. `crypto.randomBytes(32).toString('hex')` is fine.
- **Don't derive from user data** (username + timestamp, etc.).
- **Rotate on privilege change** — after login and after MFA elevation, generate a new session ID. Prevents session fixation.

### Session lifetime

- **Idle timeout:** rotate or expire after N minutes of inactivity (typical: 15–30 min for sensitive apps, hours for normal apps).
- **Absolute timeout:** even with activity, force re-authentication after N hours (typical: 8–24 hours for normal apps).
- **Long-lived "remember me":** if offered, use a separate token, not extended session lifetime. The "remember me" token authenticates a new session; it shouldn't itself be a session.
- **Logout invalidates server-side.** Clearing the cookie alone is insufficient — the session ID must be invalidated server-side so a stolen copy doesn't keep working.

### Concurrent sessions and "active devices"

For sensitive apps, surface active sessions to the user with the ability to revoke individual sessions. This is also where "logout everywhere" lives — used after password reset, suspected compromise, or a "log me out of all devices" UI action.

### Re-authentication for sensitive actions

Some actions warrant a fresh password/MFA prompt regardless of session age:

- Changing email
- Changing password
- Changing MFA settings
- Adding/removing a payment method
- Viewing or downloading sensitive data
- Granting access to API keys / tokens

This is sometimes called "step-up" authentication. The session should track when the user last authenticated, and sensitive actions check that this was recent (e.g., within the last 5 minutes).

### Logout and forced logout

- Logout button must invalidate the server-side session record immediately, then clear the cookie.
- After password reset or password change, invalidate **all** existing sessions for the user (other than perhaps the one that just performed the change).
- After MFA settings change or email change, similarly invalidate all sessions.
- When a user is deleted or suspended, invalidate all their sessions.

## Authentication flow checklist

When building or reviewing a login flow:

- [ ] Passwords hashed with argon2id (or bcrypt), never raw or fast-hashed
- [ ] Login error messages don't reveal whether a username exists
- [ ] Rate limiting on login per IP and per username (or CAPTCHA after threshold)
- [ ] Session ID is high-entropy, generated server-side, sent only via Secure/HttpOnly cookie
- [ ] Session ID rotated on login and on privilege change
- [ ] Session has both idle and absolute timeouts
- [ ] Logout invalidates server-side
- [ ] Password reset uses hashed, single-use, time-limited tokens; reveals no info about email registration; invalidates other sessions on use
- [ ] MFA available (TOTP at minimum) for accounts that warrant it
- [ ] Sensitive actions require recent re-authentication
- [ ] Notification email sent on password change, new device login, MFA changes
- [ ] No password complexity rules beyond a sane minimum length and breach-list check

## When using an auth provider (Clerk/Auth0/Supabase/etc.)

Even with a provider, you still own:

- **Authorization** (what the authenticated user can do — see `authorization.md`).
- **Session-level decisions in your app** (idle timeout, sensitive-action re-auth).
- **Verifying tokens correctly** on every backend request (see `tokens-and-oauth.md`).
- **Configuring the provider** (allowed redirect URLs, password policy, MFA enforcement).
- **Logout flow on your side** (clearing your local session even when the provider session ends).
- **Webhook handling** for events like user-deleted, email-changed, MFA-enrolled — keep your local user records in sync.
- **Rate limits on your endpoints**, especially anywhere the provider's token is used.

The provider shifts the hardest parts of credential and identity management off your plate, but it doesn't remove your application's responsibilities.
