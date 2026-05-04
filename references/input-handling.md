# Input Handling: Validation, Encoding, Injection Prevention

Covers OWASP ASVS chapters V1 (Encoding and Sanitization) and V2 (Validation and Business Logic).

The core principle: **untrusted data is anything that crosses a trust boundary**, including request bodies, query strings, headers, cookies, file contents, third-party API responses, database rows that originated from user input, environment variables in shared environments, and AI/LLM outputs that will be interpreted as code or commands. Every interpreter (HTML, SQL, shell, regex, LDAP, XML, template engine) has its own escaping rules. Mixing them up is where injection happens.

## The decision: validate, encode, or sanitize?

These are not interchangeable.

- **Validation** rejects input that doesn't match what the application expects (e.g., "this field must be a positive integer ≤ 1000"). It's a *business logic* check. It is **not** a security boundary on its own — never rely on validation alone to prevent injection.
- **Encoding/escaping** transforms data for safe inclusion in a specific output context (HTML body vs. HTML attribute vs. URL vs. JS string vs. SQL parameter). It happens at the *output* boundary, as late as possible, by the right function for the *target* interpreter.
- **Sanitization** removes dangerous parts of input — used when you genuinely need to accept HTML/markdown from users (a rich-text comment box). Use a vetted library (DOMPurify, bleach, sanitize-html), never roll your own.

When in doubt: **encode at the output, don't sanitize at the input**. Storing data in its raw, original form and encoding at render time prevents double-encoding bugs and means a future change in output context (e.g., the same data later goes into a JSON API) doesn't suddenly become unsafe.

## SQL and database injection

The fix is almost always parameterized queries / prepared statements / the ORM's query builder. The unsafe pattern looks like:

```python
# DANGEROUS
cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")
cursor.execute("SELECT * FROM users WHERE email = '" + email + "'")
```

Safe versions:

```python
# psycopg / sqlite3 / most DB-API drivers
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))

# SQLAlchemy core
session.execute(select(User).where(User.email == email))

# Django ORM
User.objects.filter(email=email)

# Raw SQL with placeholders if you must
session.execute(text("SELECT * FROM users WHERE email = :email"), {"email": email})
```

```javascript
// Node.js with pg
client.query('SELECT * FROM users WHERE email = $1', [email]);

// Prisma
prisma.user.findUnique({ where: { email } });

// Knex
knex('users').where('email', email);

// Raw with template tag (dangerous!)
client.query(`SELECT * FROM users WHERE email = '${email}'`); // NEVER
```

**Edge case: dynamic identifiers.** Table names, column names, and `ORDER BY` columns *cannot* be parameterized. If those need to come from user input, validate against an explicit allowlist:

```python
ALLOWED_SORT = {"created_at", "name", "email"}
sort_col = request.args.get("sort")
if sort_col not in ALLOWED_SORT:
    sort_col = "created_at"
# Now safe to interpolate
query = f"SELECT * FROM users ORDER BY {sort_col}"
```

Same for `LIMIT`/`OFFSET` if not parameterizable in your driver: cast to int and clamp.

**NoSQL injection** is real too. In MongoDB, accepting raw JSON request bodies into queries lets attackers send `{"$gt": ""}` to bypass auth checks. Strict input typing fixes this — coerce values to strings/numbers before they reach the query. With Mongoose, use schema validation; with raw drivers, validate types explicitly.

## XSS: cross-site scripting

XSS happens when user-controlled data is interpreted as HTML/JS by the browser. Three flavors: **stored** (saved to DB then rendered), **reflected** (echoed back from the request), **DOM** (manipulated client-side from `location.hash` or similar).

**Defense priority order:**

1. **Use a templating engine that auto-escapes by default** — React JSX, Vue templates, Django templates, ERB with `<%= %>`, Handlebars `{{ }}`. Outputting user content via `{user.name}` in JSX is automatically HTML-escaped.

2. **Don't bypass auto-escape unless you have a very specific reason.** The bypasses to grep for:
   - React: `dangerouslySetInnerHTML`
   - Vue: `v-html`
   - Angular: `bypassSecurityTrust*`
   - Django: `|safe`, `mark_safe()`, `{% autoescape off %}`
   - ERB: `<%== %>`, `raw()`, `html_safe`
   - Handlebars: `{{{ }}}`

3. **When you must render user-supplied HTML (markdown comments, rich-text), sanitize with a vetted library:**
   ```javascript
   import DOMPurify from 'dompurify';
   element.innerHTML = DOMPurify.sanitize(userHtml);
   ```
   ```python
   import bleach
   safe = bleach.clean(user_html, tags=['p', 'a', 'strong'], attributes={'a': ['href']})
   ```

4. **Context-aware encoding for non-HTML contexts:** the right escape function depends on *where* the data lands.
   - HTML body: HTML-encode (`<` → `&lt;`)
   - HTML attribute: HTML-encode plus quote-aware
   - URL parameter: `encodeURIComponent` / `urllib.parse.quote`
   - Inside a `<script>` tag with user data: don't. Use `JSON.stringify` and parse, or pass via `data-` attribute and read with `.dataset`.
   - CSS: avoid; if unavoidable, allowlist values. Don't put user data in CSS.

5. **Add a Content Security Policy as defense in depth** — see `frontend-and-headers.md`.

## Command injection

Triggered when user input flows into a shell command, file path passed to a shell, or anything that ultimately calls `system()`, `exec()` with a string, `child_process.exec`, `os.system`, etc.

The fix: don't pass strings to a shell. Use the array/argv form that bypasses shell interpretation.

```python
# DANGEROUS
os.system(f"convert {filename} output.png")
subprocess.call(f"convert {filename} output.png", shell=True)

# SAFE - argv list, no shell
subprocess.run(["convert", filename, "output.png"], shell=False, check=True)
```

```javascript
// DANGEROUS
const { exec } = require('child_process');
exec(`convert ${filename} output.png`);

// SAFE
const { execFile } = require('child_process');
execFile('convert', [filename, 'output.png']);
```

Even with argv form, validate that filenames don't contain `../` (path traversal) — see `apis-and-files.md`.

## Other injection contexts

- **LDAP injection:** escape per RFC 4515 or use a parameterized API (`ldap3` in Python, `ldapjs` filter builders). Never interpolate user input into a filter string.
- **XPath injection:** use parameterized XPath APIs (`XPathExpression` with variables) or precompile queries.
- **Regex injection (ReDoS + logic bugs):** if you build regex from user input, escape metacharacters (`re.escape()` in Python, `lodash.escapeRegExp` in JS). Avoid catastrophic-backtracking patterns (nested quantifiers like `(a+)+`); use timeouts on regex execution if the input is untrusted.
- **CSV/formula injection:** when exporting to CSV or Excel, prefix any cell starting with `=`, `+`, `-`, `@`, tab, or null with a single quote. RFC 4180 escaping alone doesn't address spreadsheet formula execution.
- **Header injection:** if user input goes into HTTP response headers (e.g., a redirect Location, a Set-Cookie value, a custom CORS header), strip CR/LF. Most modern frameworks do this; raw `res.setHeader` calls are the risk.
- **Template injection (SSTI):** never use user input as a template — `render_template_string(user_input)` in Flask/Jinja, `eval` in JS template engines, `Mustache.render(userTemplate, data)`. The user input goes in the *data*, not the *template*.
- **Log injection:** if user input is written to logs that someone later parses or views in a terminal, strip CR/LF and ANSI escape codes. (Not a high-severity vuln on its own but enables forging log entries.)

## Decoding: do it once, in the right place

Decode/unescape user input exactly once, before validation, and only when you expect that encoding (e.g., URL-decoding a query param, base64-decoding a token). Decoding *after* validation defeats the validation. Double-decoding (`urldecode(urldecode(x))`) is a common bypass for path-traversal filters that check for `..` but miss `%252e%252e`.

## Validation rules that earn their keep

Validation is for business correctness, but a few patterns also reduce attack surface:

- **Type coercion at the boundary.** If a field should be an integer, parse it to an integer. Don't pass strings around and hope.
- **Length caps.** Every string field gets a max length appropriate to its purpose. Prevents DoS and bounds the blast radius of any downstream parsing bug.
- **Allowlists over blocklists** for any enumerable field — countries, currencies, sort columns, file types, redirect destinations.
- **Reject vs. sanitize:** prefer rejecting invalid input outright (return a 400) over silently cleaning it. Silent cleaning hides bugs and creates surprising behavior.
- **Validate on the server, always.** Client-side validation is for UX, not security.

For request schemas, use a validation library (Zod, Yup, Joi, Pydantic, marshmallow, FluentValidation) and apply it at the request boundary before the handler runs. This makes input shape an enforced contract.

## Business logic checks that look like input validation but aren't

The standard separates these from injection prevention because they're about *intent*, not *interpretation*:

- A user transferring a negative amount (turns a withdrawal into a deposit).
- An email field validating syntactically but the email belongs to a different user.
- A coupon code that's syntactically valid but expired.
- A multi-step workflow where step 3 is hit directly without completing steps 1 and 2.
- A "quantity" field that accepts 999999999 and crashes the inventory system.

Defenses are application-specific: enforce state machines on the server, check ownership and state on every step, set rational bounds on all numeric inputs, and treat client-supplied step indicators as hints not facts.

## Quick checklist for any handler that takes input

- [ ] Schema-validate the request body/params at the boundary
- [ ] Coerce types; don't accept stringly-typed values where you want numbers/booleans
- [ ] Cap all string lengths
- [ ] Use parameterized queries / ORM methods for any DB access
- [ ] Use argv-form `execFile`/`subprocess.run` (no `shell=True`) for any process calls
- [ ] Pass user content through templating that auto-escapes; only bypass with a sanitizer
- [ ] If building URLs from input, use the framework's URL builder (don't string-concat)
- [ ] If the handler returns user-supplied data, ensure it's encoded for the response context (HTML vs. JSON vs. plain text vs. CSV)
- [ ] If file paths are involved, see `apis-and-files.md` for path-traversal defenses
