# APIs and File Handling

Covers OWASP ASVS V4 (API and Web Service) and V5 (File Handling).

## API surface: what changes vs. server-rendered apps

API endpoints are programmatic, easy to enumerate, and accessed by code. The threat model shifts:

- **Authorization is the dominant risk** — every endpoint is a potential IDOR (see `authorization.md`).
- **Rate limiting matters more** — bots find APIs faster than UIs.
- **Schema discipline matters more** — clients may send anything, and frameworks may auto-bind it.
- **Errors leak more** — verbose error responses give attackers a map.

## REST endpoint hardening

### Authentication

Every endpoint that returns or modifies data should require authentication unless explicitly public. Use a default-deny middleware setup (see `authorization.md`).

For API-only services, accept tokens via `Authorization: Bearer <token>` rather than cookies — avoids CSRF concerns. (If you do use cookies, you need CSRF tokens; see `frontend-and-headers.md`.)

### HTTP methods matter

- `GET` must be safe and idempotent — never used for state changes. Bots, browser prefetchers, and link previewers will hit GET URLs.
- Use `POST` for creation, `PUT`/`PATCH` for updates, `DELETE` for deletion.
- For destructive `DELETE`s and dangerous `POST`s, consider requiring a confirmation token or recent re-authentication.

### Content type validation

Reject requests with unexpected content types. Don't accept `application/x-www-form-urlencoded` on a JSON-only API — it's a common CSRF vector when combined with cookie auth. Set strict `Accept` and `Content-Type` handling.

### Request size limits

Set a max body size on the framework or reverse proxy. Default Express has no body size limit on raw bodies; nginx default is 1MB. A 100MB JSON body to a login endpoint is a DoS waiting to happen.

```javascript
// Express
app.use(express.json({ limit: '100kb' }));
```

```python
# Flask
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024
```

For file upload endpoints, the limit is appropriate to the file type — see below.

### Rate limiting

The minimum useful set:

- Per-IP rate limit globally (e.g., 100 req/min) — slows mass abuse.
- Per-IP rate limit on auth endpoints (login, signup, password reset, MFA verify) — much tighter, e.g., 5/min.
- Per-account rate limit on auth endpoints — separate from per-IP.
- Per-user rate limit on expensive operations (PDF generation, search, bulk export).
- Per-API-key rate limit for machine clients.

For a typical app, use a battle-tested middleware (`express-rate-limit`, `django-ratelimit`, `flask-limiter`, `slowapi`) backed by Redis if you have multiple processes. For more sophisticated cases, a gateway like Cloudflare, AWS WAF, or Kong handles it at the edge.

Rate-limit responses should be `429 Too Many Requests` with a `Retry-After` header.

### Pagination and bulk reads

Endpoints that list resources should:

- Require pagination (default page size, max page size — typically 25 default, 100 max).
- Reject requests asking for absurd limits (don't return 100,000 records in one response — DoS, memory exhaustion, accidental data dump).
- Use cursor-based pagination for stable iteration over large datasets; offset pagination is fine for small ones.

### Mass assignment

Covered in `authorization.md`. The short version: explicitly allowlist updatable fields. Don't `Object.assign(user, req.body)`.

### Error responses

The body of an error response should be:

- A short, generic message ("Invalid request", "Not found", "Forbidden").
- Optionally, a structured error code your client knows how to handle (`{"code": "user_not_found"}`).

The body should NOT be:

- A stack trace.
- An ORM error including the SQL.
- The full validation error from Pydantic/Zod *if* it would echo back unexpected internal field names.
- Different responses for "user exists with wrong password" vs "no such user" on auth endpoints (see `auth-and-sessions.md`).

In production, set the framework to non-debug mode. Common foot-guns:

- Flask: `DEBUG=False` in production. Debug mode exposes a Werkzeug console — code execution as a feature.
- Django: `DEBUG=False`, `ALLOWED_HOSTS` set.
- Express: don't ship the default error handler that prints stack traces; use a custom one.
- Next.js: production build, not `next dev`.

### Response shape — don't leak more than asked

A `GET /api/users/me` response should not include `password_hash`, `mfa_secret`, `email_verification_token`, internal flags, etc. Use serializers/DTOs that explicitly project public fields:

```python
# Django REST Framework
class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name']  # explicit
        # NOT: fields = '__all__'
```

```javascript
// Manual projection in plain Express
res.json({
  id: user.id,
  email: user.email,
  name: user.name,
  // do NOT spread the full user object
});
```

For listing operations, the same applies. Be deliberate about what each endpoint returns.

## GraphQL

GraphQL has its own pitfalls:

- **Authorization on every resolver, not just at the entry point.** A user fetching `me { team { invoices { ... } } }` needs the invoices resolver to check that the user can see those invoices. Don't trust the upstream check.
- **Query depth and complexity limits.** Without these, a malicious client can craft a deeply nested query that exhausts the server. Use libraries like `graphql-depth-limit` and `graphql-cost-analysis`.
- **Disable introspection in production** if your schema isn't meant to be public.
- **Disable suggestions** in error messages — they leak field names attackers haven't guessed.
- **Batch operations** can multiply the cost of a missing authorization check by N. Test bulk fields with a different user's IDs.
- **Persisted queries** (only known query hashes accepted) for production clients drastically reduce the attack surface.

## WebSocket / SSE

Both bypass standard request authentication patterns:

- **Authenticate the connection at upgrade time**, then track the user identity for the connection's lifetime. Don't trust per-message claims.
- **Re-authorize on every action.** A connection authenticated at hour 0 may have had its session revoked at hour 1; check.
- **Origin validation on the upgrade handshake** — same-origin policy doesn't apply to WebSocket, so check the `Origin` header against your allowlist.
- **Backpressure / message rate limiting** — a malicious client can flood messages.

## File uploads — the most-broken corner of any web app

Uploads are dangerous in proportion to what happens to the file afterward. The four risk dimensions:

1. **Storage** — does the file end up somewhere it can be served?
2. **Processing** — does any tool parse it (image library, PDF reader, AV scanner)?
3. **Naming** — can the user influence the filename or path?
4. **Serving** — does the file get served back, and to whom, with what content-type?

### Validation at upload time

- **Cap the size** at the smallest reasonable limit. A 5MB profile picture limit. A 50MB document upload. Set this at multiple layers (web server, reverse proxy, framework, storage).
- **Cap the file count** if multiple files are accepted.
- **Validate by content, not just by extension.** An attacker uploading `evil.jpg` that's actually PHP/JS is a classic. Use a magic-byte / MIME sniffing library (`file-type` in Node, `python-magic`, Apache Tika), and check the result against an allowlist.
- **For images,** re-encode after upload (decode + re-encode with a known-good library). This strips polyglot files (a JPEG that's also a valid HTML page), removes EXIF metadata that may contain GPS, and provides a defense against image parser exploits via re-encoding. Sharp, Pillow, ImageMagick all work — but ImageMagick has had its share of CVEs; configure its policy file or use an alternative.
- **For documents (PDF, DOCX, XLSX),** consider running them through a sanitizer (e.g., libraries that flatten/normalize) if they'll be opened by other users.

### Filename handling — never trust the client name

```python
# DANGEROUS
filename = request.files['upload'].filename
path = f"/var/uploads/{filename}"  # could be "../../etc/passwd"
file.save(path)
```

The fixes:

- **Generate a server-side filename** — UUID or random string. Store the original filename as metadata if needed for display.
- **Strip path components** — only keep the basename. `os.path.basename(filename)` in Python, similar in others.
- **Limit allowed characters** — alphanumeric + a few specific punctuation. Reject the rest.
- **Validate the resolved path is inside the intended directory** — after constructing the destination path, check it doesn't escape via symlinks or resolved `..`s:

```python
import os
upload_dir = os.path.realpath('/var/uploads')
target = os.path.realpath(os.path.join(upload_dir, filename))
if not target.startswith(upload_dir + os.sep):
    abort(400)
```

### Storage location

- **Don't store uploads under the web root.** A file in `/public/uploads/foo.html` is served directly. If a malicious file slips through, it executes.
- **Store on object storage (S3, GCS, R2) or a dedicated directory** outside the web-served paths.
- **For S3-compatible storage:** keep the bucket private, serve via pre-signed URLs (with expiration ≤ 1 hour for sensitive content), and validate that uploaders can only PUT to their own keys (use a server-generated key, don't accept the key from the client).

### Serving uploaded files

- **Set the right `Content-Type`** based on what you actually allow, not what the user said.
- **Set `Content-Disposition: attachment`** for any file type that could be interpreted by the browser (HTML, SVG, PDF in some contexts) unless inline display is the entire point.
- **Set `X-Content-Type-Options: nosniff`** so the browser doesn't override your content type with its sniffing.
- **Authenticate the download.** A pre-signed URL is fine, but if files contain user data, the URL itself becomes the authorization grant — keep its lifetime short and use it once.
- **Beware of SVG.** SVG files can contain `<script>` and execute when displayed inline. Either disallow SVG, or sanitize them with DOMPurify (browser) / svglib pre-processing (server).

### File downloads

If your app generates downloads (CSV exports, PDFs):

- **Don't take the filename from user input.** If you must, allowlist characters strictly.
- **Don't take the path from user input.** Path traversal in download endpoints is common. The user provides an *ID*, the server resolves the path.
- **For CSV exports,** apply formula-injection escaping (see `input-handling.md`).
- **Don't include sensitive data the user shouldn't see** — same projection rules as API responses.

## Request/response checklist

REST endpoints:
- [ ] Authentication required by default
- [ ] Authorization (function + object level) on every handler
- [ ] Body size limit configured
- [ ] Content-type validated; CSRF defense if cookie-authed
- [ ] Rate limiting on auth, sensitive ops, and globally
- [ ] Pagination required on list endpoints with sane max
- [ ] Mass assignment prevented (explicit field allowlist)
- [ ] Errors are generic in production; debug mode is off
- [ ] Response bodies project only public fields

GraphQL:
- [ ] Authorization on every resolver, not just entry
- [ ] Depth and complexity limits
- [ ] Introspection disabled in prod (if not public schema)
- [ ] Persisted queries for production clients (if feasible)

WebSocket:
- [ ] Auth checked at upgrade
- [ ] Re-authz on each action
- [ ] Origin validated
- [ ] Message rate-limited

File uploads:
- [ ] Size and count caps at multiple layers
- [ ] Content-type validated by magic bytes, allowlisted
- [ ] Images re-encoded server-side; EXIF stripped
- [ ] Server-generated filenames; user input not in path
- [ ] Stored outside web root or in private object storage
- [ ] Path-traversal check after resolution
- [ ] Served with correct Content-Type, nosniff, and disposition
- [ ] SVG either disallowed or sanitized
- [ ] Downloads authenticated and authorized; no user input in path
