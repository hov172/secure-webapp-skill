# Frontend Security: Headers, Cookies, CSRF, CORS

Covers OWASP ASVS V3 (Web Frontend Security). The browser is your application's untrusted-but-essential delivery mechanism — these defenses configure the browser to enforce policies on your behalf.

## OWASP source sync

Deterministic notes regenerated from the refreshed OWASP source cache.

- Browser controls: CSP plus HSTS and defensive headers on HTML responses.
- Cookies: Secure, HttpOnly, SameSite; do not rely on credentialed wildcard CORS.
- Clickjacking: prefer CSP frame-ancestors and deny framing by default.
- CSRF: keep anti-forgery tokens or equivalent defenses for cookie-auth state changes.
- Redirects: keep destinations relative or allowlisted; reject protocol-relative URLs.
## Security headers — the high-leverage set

Set these on every response (or at least every HTML response). Most frameworks have middleware (`helmet` for Express, `django-csp` and `SecurityMiddleware` for Django, `secure_headers` gem for Rails).

### Strict-Transport-Security (HSTS)

Forces HTTPS for the domain — the browser refuses HTTP after the first valid HTTPS response.

```
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

Add `preload` and submit to https://hstspreload.org/ once you're confident HTTPS is fully deployed across all subdomains.

Caveat: once the browser has cached HSTS, you can't easily go back. Don't enable on a domain where you might need to serve HTTP (a status page on a backup domain, etc.).

### Content-Security-Policy (CSP)

The most powerful XSS defense. Tells the browser what sources are allowed for scripts, styles, fonts, images, frames, etc. A well-tuned CSP turns most stored-XSS bugs into "browser refused to execute" — defense in depth, not a substitute for proper output encoding.

A reasonable starting policy for a typical app:

```
Content-Security-Policy:
  default-src 'self';
  script-src 'self' 'nonce-{RANDOM}' 'strict-dynamic';
  style-src 'self' 'nonce-{RANDOM}';
  img-src 'self' data: https:;
  font-src 'self';
  connect-src 'self' https://api.yourservice.com;
  frame-ancestors 'none';
  base-uri 'self';
  form-action 'self';
  object-src 'none';
  upgrade-insecure-requests;
```

Key choices:

- **Nonce-based, not allowlist-based.** A `'nonce-RANDOM'` per request, applied to legitimate `<script>` tags, beats an allowlist of CDNs (which research has shown is usually bypassable).
- **`'strict-dynamic'`** lets nonced scripts load other scripts they trust, simplifying complex apps.
- **No `'unsafe-inline'` for scripts.** This is the single most common CSP mistake — it opens the door to most XSS. Use nonces.
- **`object-src 'none'`** disables Flash and `<object>` tags.
- **`frame-ancestors 'none'`** prevents your page from being framed (clickjacking defense — also see X-Frame-Options below).
- **`base-uri 'self'`** prevents `<base href>` injection from redirecting relative URLs.

CSP is hard to deploy on existing apps with inline scripts and styles. Use **CSP report-only mode** first:

```
Content-Security-Policy-Report-Only: ...; report-uri /csp-report
```

Collect violation reports, fix them, then switch to enforcing. This is iterative — expect the first pass to break things.

### X-Frame-Options

Older clickjacking defense. Set to match your `frame-ancestors` policy:

```
X-Frame-Options: DENY
```

CSP `frame-ancestors` supersedes this in modern browsers, but X-Frame-Options is still useful for older clients.

### X-Content-Type-Options

```
X-Content-Type-Options: nosniff
```

Tells the browser not to override the declared `Content-Type` based on its own sniffing. Stops some XSS-via-uploaded-file attacks.

### Referrer-Policy

```
Referrer-Policy: strict-origin-when-cross-origin
```

Limits what's sent in the `Referer` header to other sites. Default is browser-dependent; set explicitly. `strict-origin-when-cross-origin` is a sensible default — full URL same-origin, just origin cross-origin over HTTPS, nothing on downgrade.

For sensitive apps where URLs themselves contain confidential info: `no-referrer`.

### Permissions-Policy

Restrict access to powerful browser APIs your app doesn't need:

```
Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()
```

Each `()` denies the feature for everyone. Explicitly allowlist origins where you need them. Reduces blast radius if an XSS does land.

### Cross-Origin-Opener-Policy and Cross-Origin-Embedder-Policy

For apps using `SharedArrayBuffer` or wanting cross-origin isolation:

```
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: require-corp
```

Even without those features, COOP defends against some cross-window attacks.

### Cache-Control on sensitive responses

API responses with user data should not be cached by intermediate proxies or browsers:

```
Cache-Control: no-store
```

Avoid `private, no-cache` alone — `no-store` is the right choice for sensitive responses.

## Cookie configuration

A session cookie at minimum:

```
Set-Cookie: sid=abc123; Secure; HttpOnly; SameSite=Lax; Path=/; Max-Age=28800
```

The flags:

- **`Secure`** — sent only over HTTPS. Required for any cookie carrying authentication.
- **`HttpOnly`** — JavaScript can't read it. Mitigates XSS-based theft.
- **`SameSite`** —
  - `Lax` (default in modern browsers): cookie is sent on same-site requests and on top-level navigations. Reasonable default for session cookies.
  - `Strict`: cookie not sent on any cross-site request, including a click on an external link to your site. Strongest but breaks "click email link to land logged in".
  - `None`: cookie sent on all requests. Required for cross-site embeds (e.g., a widget on third-party sites). Must be paired with `Secure`. Use only when you really need cross-site cookies.
- **`Path`** — typically `/`. Setting this narrower doesn't add real security; same-origin script can still read.
- **`Domain`** — leave unset for host-only cookies (recommended). Only set if you specifically need to share with subdomains, and understand the implications.

Avoid prefixes you don't intend:

- `__Host-` prefix requires `Secure`, `Path=/`, no `Domain`. Strongest binding to a single host. Use for session cookies if your setup allows.
- `__Secure-` prefix requires only `Secure`. Less strict than `__Host-`.

## CSRF: Cross-Site Request Forgery

Threat: a user's browser visiting `evil.com` makes a request to `your-app.com` that automatically includes the user's session cookie. If your app does state changes based purely on cookie auth, evil.com just performed an action as the user.

`SameSite=Lax` mitigates most CSRF in modern browsers, but isn't a complete fix:

- Some clients ignore it.
- It doesn't help against same-site attackers (subdomain takeover, XSS on a sibling subdomain).
- It allows GET requests, which might be misused if your app violates the "GET should be safe" rule.

Defense in depth options:

### Anti-CSRF tokens (synchronizer pattern)

Server generates a random token, stores it tied to the session, and embeds it in forms (and exposes it via an endpoint for SPAs). Every state-changing request must include the token; server verifies.

Most frameworks do this for you:

- Django: `{% csrf_token %}` in templates, `@csrf_exempt` to opt out (rare).
- Rails: `protect_from_forgery` in ApplicationController; `<%= csrf_meta_tags %>`.
- Spring Security: enabled by default for stateful apps.
- Express: `csurf` (deprecated; use double-submit pattern or per-request tokens via session).
- Next.js: depends on routing layer; for `app/`, use server actions which carry CSRF protection.

Use what your framework provides. Don't roll your own unless you have to.

### Double-submit cookie

Server sets a random value in a non-HttpOnly cookie. Client reads it via JS, sends it as a header on requests. Server checks the cookie value matches the header value. An attacker on evil.com can't read the cookie, so can't forge the header.

Less robust than the synchronizer pattern (vulnerable to subdomain attackers and cookie-jar shenanigans) but a reasonable default for SPA + JSON API.

### Custom header

For pure JSON APIs called via `fetch` or `XMLHttpRequest`, requiring a custom header (e.g., `X-Requested-With: XMLHttpRequest` or any app-specific header) on state-changing requests is itself a CSRF defense — browsers don't send custom headers cross-origin without preflight, and the preflight is itself blocked by CORS unless you allow it.

### Bearer tokens, not cookies

Authenticating with `Authorization: Bearer ...` in a header rather than cookies sidesteps CSRF entirely — the browser doesn't auto-attach the token. This is why pure JSON APIs often go this route. The trade-off is XSS-readable token storage; see `tokens-and-oauth.md`.

## CORS: Cross-Origin Resource Sharing

CORS is a *relaxation* of the same-origin policy, not a security boundary. Configuring it permissively expands attack surface; configuring it incorrectly leaks the protection you thought you had.

### The dangerous patterns

```javascript
// DANGEROUS
res.setHeader('Access-Control-Allow-Origin', '*');
res.setHeader('Access-Control-Allow-Credentials', 'true');
```

The combination of `*` + `credentials: true` is rejected by browsers — but apps often "fix" this by echoing back the request's `Origin`:

```javascript
// ALSO DANGEROUS — equivalent to allowing any origin with credentials
res.setHeader('Access-Control-Allow-Origin', req.headers.origin);
res.setHeader('Access-Control-Allow-Credentials', 'true');
```

Now any site can hit your authenticated endpoints with the user's cookies and read the response.

### Safe patterns

- **No CORS at all** if your API is only called by your same-origin frontend. The default behavior — no `Access-Control-Allow-*` headers — is safest.
- **Explicit allowlist** of origins for cross-origin needs:

```javascript
const ALLOWED = new Set(['https://app.yourservice.com', 'https://admin.yourservice.com']);
const origin = req.headers.origin;
if (origin && ALLOWED.has(origin)) {
  res.setHeader('Access-Control-Allow-Origin', origin);
  res.setHeader('Vary', 'Origin');
  res.setHeader('Access-Control-Allow-Credentials', 'true');
}
```

- **Public read-only APIs** can use `Access-Control-Allow-Origin: *` only if no credentials are involved and the data is genuinely public.

### The preflight (`OPTIONS`) request

For non-simple requests (custom headers, methods other than GET/POST/HEAD, JSON content-type), the browser sends an `OPTIONS` preflight first. Your CORS config must respond appropriately:

- `Access-Control-Allow-Methods` — only methods you actually expose
- `Access-Control-Allow-Headers` — only headers you actually expect
- `Access-Control-Max-Age` — cache the preflight result (e.g., 600 = 10 min)

Use `cors` middleware in Node, `django-cors-headers`, `Flask-CORS`, etc. Configure with an allowlist, not a regex that's easy to bypass.

## DOM-based foot-guns

These are framework-agnostic XSS sources to grep for in any frontend code:

- `dangerouslySetInnerHTML` (React)
- `v-html` (Vue)
- `[innerHTML]` (Angular without strict)
- `bypassSecurityTrust*` (Angular)
- `eval`, `Function`, `setTimeout(string, ...)`, `setInterval(string, ...)`
- `document.write`, `document.writeln`
- `element.innerHTML =`, `outerHTML =`
- `location = userInput`, `location.href = userInput` (open redirect / javascript: URL)
- `window.open(userInput)`
- `srcdoc` on iframes from user content
- Direct injection of user data into `<style>` blocks or inline `style="..."`

Each has legitimate uses, but each needs explicit justification. Sanitization with DOMPurify is the safety net when user-supplied HTML is genuinely required (rich-text comments, markdown rendering).

## postMessage / iframe communication

If your app uses `postMessage` to communicate with iframes or other windows:

- **Specify the target origin** (not `'*'`) when sending — `iframe.contentWindow.postMessage(data, 'https://expected.com')`.
- **Validate the `origin`** of received messages against an allowlist. `'*'` for incoming is always wrong.
- **Validate the message structure** — don't trust shape; treat the payload as untrusted input.

## Subresource Integrity (SRI) for third-party scripts

If you load scripts from a CDN you don't fully trust (e.g., a public-CDN-hosted version of a library), use SRI:

```html
<script src="https://cdn.example.com/lib.js"
        integrity="sha384-oqVuAfXRKap7fdgcCY5uykM6+R9GqQ8K/uxy9rx7HNQlGYl1kPzQho1wx4JwY8wC"
        crossorigin="anonymous"></script>
```

Without SRI, a CDN compromise serves malicious code to your users.

## Iframes that embed third-party content

If you embed third-party content in iframes (a payment provider, an embedded video, a widget):

- Use the `sandbox` attribute to limit what the iframe can do:

```html
<iframe src="https://untrusted.com" sandbox="allow-scripts allow-forms"></iframe>
```

Without `allow-scripts`, the iframe can't run JS. Without `allow-same-origin`, it's treated as a separate origin. Add only what's needed.

- Be aware that any iframe under your domain inherits your cookies (until SameSite blocks them).

## Quick checklist for any frontend deployment

- [ ] HSTS enabled (with `includeSubDomains` if applicable, `preload` once stable)
- [ ] CSP set, no `'unsafe-inline'` in script-src, nonce-based
- [ ] X-Frame-Options DENY (or `frame-ancestors` in CSP)
- [ ] X-Content-Type-Options: nosniff
- [ ] Referrer-Policy set explicitly
- [ ] Permissions-Policy denies APIs you don't use
- [ ] Session cookies: Secure, HttpOnly, SameSite=Lax (or Strict)
- [ ] CSRF defense via framework's built-in mechanism, OR bearer tokens (not cookies) for state-changing requests
- [ ] CORS configured with explicit allowlist, no `*` with credentials
- [ ] No `dangerouslySetInnerHTML` / `v-html` / `innerHTML =` with user data (or sanitized via DOMPurify)
- [ ] postMessage uses specific origins both ways
- [ ] Third-party scripts use SRI
- [ ] Iframes embedding untrusted content use `sandbox`
