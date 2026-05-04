# Tokens, JWT, and OAuth/OIDC

Covers OWASP ASVS V9 (Self-contained Tokens) and V10 (OAuth and OIDC).

## When to reach for what

- **Server-side session ID in a cookie** — default for typical web apps. Easy to revoke, simple. See `auth-and-sessions.md`.
- **JWT (or other self-contained token)** — when you need stateless auth across services, mobile/native clients, or microservices that share a verification key. Stateless = harder to revoke, so plan for that.
- **API keys** — for machine-to-machine. Long-lived bearer credentials; treat them like passwords.
- **OAuth 2.x / OIDC** — when integrating with third-party identity providers ("Sign in with Google") or when *you* are an identity provider for other apps.

The mistake to avoid: using JWTs for browser sessions because "they're modern." A signed cookie holding a session ID is simpler, easier to revoke, and just as secure for a single web app. Reach for JWTs when you have a real reason.

## JWT: the things people get wrong

### 1. The `alg: none` and algorithm-confusion attacks

JWTs include the signing algorithm in the header. A library that trusts the header's `alg` field can be tricked.

- **Always pin the algorithm on the verifier side.** Don't accept whatever the token claims.
- **Reject `alg: none`** explicitly, or use a library that rejects it by default and verify your config.
- **HS256/RS256 confusion:** if your verifier accepts both HMAC and RSA and decides based on the header, an attacker who knows your RSA public key can sign a token with HS256 using the public key as the HMAC secret. Pin to one algorithm.

```python
# python-jose / pyjwt — explicit algorithms
import jwt
payload = jwt.decode(
    token,
    key=PUBLIC_KEY,
    algorithms=["RS256"],   # ← pin
    audience=EXPECTED_AUD,
    issuer=EXPECTED_ISS,
)
```

```javascript
// jsonwebtoken in Node
const payload = jwt.verify(token, PUBLIC_KEY, {
  algorithms: ['RS256'],   // ← pin
  audience: EXPECTED_AUD,
  issuer: EXPECTED_ISS,
});
```

### 2. The signing key

- **Symmetric (HS256):** secret is shared between signer and verifier. Use ≥256 random bits from a CSPRNG. Never a password or guessable string. Store in your secrets manager (see `secrets-and-config.md`).
- **Asymmetric (RS256, ES256, EdDSA):** preferred for tokens issued by one service and verified by others. Private key stays with the issuer. EdDSA (Ed25519) is excellent if your library supports it.
- **Rotate keys.** Have a key ID (`kid`) in the header so you can serve multiple verifying keys during rotation. Plan rotation before you need to.

### 3. Verifying the right things

A JWT verifier must check:

- **Signature** — using the pinned algorithm and the right key (selected by `kid` from your trusted set, not from a URL the token specifies).
- **Expiration (`exp`)** — the token has not expired. With a small leeway (≤30s) for clock skew.
- **Not-before (`nbf`)** — the token is not used before its valid time.
- **Issuer (`iss`)** — matches the expected issuer. Especially critical if multiple issuers exist.
- **Audience (`aud`)** — the token was issued for *this* service. Stops a token issued for service A from being replayed against service B.
- **(Optional) JWT ID (`jti`) for revocation** — see below.

### 4. Storing tokens on the client

If you're using JWTs as browser session credentials:

- **`localStorage` is risky.** Any XSS reads it. Avoid for session-equivalent tokens.
- **HttpOnly cookies** are the safer choice. Browser sends them automatically; JS can't read them. Combine with `Secure`, `SameSite=Lax` (or Strict for high-stakes), and CSRF defense.
- **Memory-only** for short-lived access tokens (e.g., a 5-minute access token kept in JS memory plus a refresh token in an HttpOnly cookie) is a pattern that works well — XSS at any moment can steal what's in memory but can't persist.

For mobile/native: secure platform storage (Keychain on iOS, Keystore on Android).

### 5. Lifetime and revocation

JWTs are stateless — the server can't easily say "this specific token is now revoked". Two patterns to live with that:

- **Short-lived access tokens + refresh tokens.** Access token lives 5–15 minutes. Refresh token lives longer but is opaque, server-tracked, and revocable. Logout invalidates the refresh token.
- **Token revocation list (denylist).** Track revoked `jti`s in Redis until their `exp` passes. Verifier checks the denylist on every request. Effectively turns the JWT system into "JWT for performance, with stateful revocation."

For browser sessions, a 10–30 minute access token is usually a reasonable starting point. Don't ship 24-hour access tokens — that's a stolen-cookie window of a full day.

### 6. The contents of the token

- **Don't put secrets in JWTs.** They're signed, not encrypted. Anyone who has the token can base64-decode the payload. Use JWE if you genuinely need encrypted tokens, but ask first whether you really need to put that data in a token at all.
- **Keep claims minimal** — user ID, roles, expiration. Don't try to embed the full user profile.
- **Don't include the password hash, password reset tokens, or other credentials.**

## API keys

For machine-to-machine. Treat them like passwords:

- **Generate from a CSPRNG**, ≥256 bits, displayed once at creation.
- **Store hashed** (SHA-256 is fine here since it's a high-entropy random value, not a low-entropy password).
- **Show a prefix** (`sk_live_xxxx_lastfour`) for UI identification without revealing the secret.
- **Scope keys** — keys should have explicit permissions (read-only, specific endpoints), not blanket account access.
- **Rotate.** Provide a UI for users to rotate keys without downtime (overlap period, key versioning).
- **Rate-limit per key.**
- **Audit-log usage.** When was this key last used, from what IP, against what endpoints?
- **Allow revocation** — instant, server-side.

## OAuth 2.x / OIDC

OAuth is for **delegated authorization** — letting your app act on behalf of a user with a third party (Google Drive, GitHub, etc.). OIDC is OAuth + identity layer — using the third party as a sign-in provider.

The protocol is intricate; getting it right by hand is a project. Use a vetted library (Auth.js / NextAuth, Authlib, doorkeeper, MSAL, Spring Security OAuth, etc.) and an established provider (Google, Auth0, Clerk, Keycloak).

### The flow that matters: Authorization Code with PKCE

For browser/mobile clients, the only flow you should use:

1. Client generates a random `code_verifier` and its SHA-256 `code_challenge`.
2. Client redirects user to the provider with the challenge and a random `state` value.
3. User authenticates at the provider and approves.
4. Provider redirects back with an `authorization_code` and the same `state`.
5. **Client verifies the `state` matches** what was sent (CSRF defense for the OAuth flow).
6. Client exchanges the code for tokens, sending the `code_verifier` for proof.
7. Client validates the ID token (if OIDC) and stores tokens appropriately.

What goes wrong:

- **Implicit flow** (returning tokens directly in the URL fragment) — deprecated. Don't use.
- **Resource Owner Password Credentials grant** (sending username/password directly) — deprecated. Don't use.
- **Skipping `state` verification** — opens a CSRF on the OAuth flow itself. Always check.
- **Skipping PKCE** — required for public clients, recommended for all clients.
- **Trusting unvalidated redirects.** The provider must only redirect to an exact-match registered URL. If your app accepts arbitrary `redirect_uri`s in the OAuth flow, an attacker can hijack codes.
- **Exposing client secrets in browser code.** If your app is a SPA, you don't have a client secret — use PKCE only.

### Validating an OIDC ID token

When using "Sign in with X" via OIDC:

- Fetch the provider's JWKS (signing keys) over HTTPS, cache, and refresh per the cache headers.
- Verify the ID token's signature, `iss`, `aud` (must be your client ID), `exp`, `nonce` (should match a value you sent), and `sub` (the stable user identifier — use this, not email, as the foreign key).
- The `email` claim is informational. Some providers don't verify email ownership. Check `email_verified` if you rely on it.
- The user's `sub` from a given provider is stable and unique within that provider — but a user can have accounts at multiple providers. Plan for "this user signed in with Google, then later wants to also link GitHub."

### When you are the OAuth provider

A much taller order. Read the OAuth 2.1 BCP (RFC 9700). Use a vetted server library (Hydra, Keycloak, Auth0, Authentik, doorkeeper). Things you must get right:

- Exact-match `redirect_uri` validation on every request.
- Authorization codes are single-use, expire in 10 minutes, bound to the client and `code_verifier`.
- Refresh tokens are rotated on every use; old refresh tokens are revoked when reused (stolen-token detection).
- Scopes are checked on every protected resource access.
- Consent screens that clearly show what's being requested and to whom.

## Resource server: validating tokens on incoming requests

If your API receives bearer tokens issued by an authorization server:

- Validate the token (signature, exp, iss, aud) before doing anything else.
- Cache JWKS lookups; don't fetch the keys on every request (and don't fetch from a URL the token specifies — use a configured URL).
- Map the token's `sub` (and `org` claim, if multi-tenant) to your local user/tenant model.
- Check scopes for the operation being performed.
- For revocation-sensitive contexts, consider token introspection (RFC 7662) — but that adds latency.

## Quick checklist

JWTs:
- [ ] Algorithm pinned on verification (no trusting the `alg` header)
- [ ] Strong key (≥256 bits, from secrets store, not in source)
- [ ] `exp`, `iss`, `aud`, signature all verified on every use
- [ ] Short access-token lifetime; refresh tokens for longer-lived auth
- [ ] No secrets in the payload
- [ ] HttpOnly cookie or memory-only storage on browser; not localStorage for session-equivalent tokens
- [ ] Revocation strategy in place (short TTL or denylist)

API keys:
- [ ] Generated from CSPRNG, displayed once
- [ ] Stored hashed
- [ ] Scoped permissions, not blanket
- [ ] Rate-limited and audit-logged
- [ ] Revocable from UI

OAuth:
- [ ] Authorization Code with PKCE flow only
- [ ] `state` verified on callback
- [ ] Exact-match `redirect_uri`
- [ ] ID token signature, claims, and `nonce` validated
- [ ] Use a vetted library; do not implement the protocol from scratch
