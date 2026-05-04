# Secrets and Configuration

Covers OWASP ASVS V13 (Configuration). Misconfiguration is consistently a top OWASP risk because it's easy to do wrong, hard to detect, and often catastrophic.

## Where secrets actually go

A secret is anything that, if disclosed, lets someone impersonate your app or access data they shouldn't: API keys, DB passwords, OAuth client secrets, signing keys (JWT, cookie), TLS private keys, third-party service tokens (Stripe, SendGrid, Twilio), encryption keys.

The fundamental rules:

1. **Not in source code.** Not in committed files, not in container images, not in config files checked into git.
2. **Not in logs.** No `console.log(config)`, no `print(env)`, no error messages that include the env dict.
3. **Not in client-side code.** Anything sent to the browser is public. (`NEXT_PUBLIC_*`, `VITE_*`, `REACT_APP_*` and similar prefixes are deliberately exposed to the client — never put real secrets there.)
4. **Not shared across environments.** Dev, staging, and prod each get their own credentials, with the smallest scope each needs.
5. **Rotatable without redeployment.** If rotating a secret requires editing source and pushing, rotation won't happen.

### Where they should live, in rough order of preference

1. **Cloud secrets manager** — AWS Secrets Manager, GCP Secret Manager, Azure Key Vault, HashiCorp Vault, Doppler, Infisical. Apps fetch at startup or per-request (with caching). Audit logs of access. Rotation tooling.
2. **Platform-injected env vars** — Vercel/Netlify/Render/Railway/Fly env var UI. Acceptable for small apps; the secrets live in the platform's encrypted store. Watch out: easy to accidentally check the env panel into a screenshot.
3. **`.env` file local to the deployment** — simplest, but high risk if the file leaks. Outside source control. Restricted file permissions (`chmod 600`).

What goes WRONG:

- Secrets committed to git (even if later removed — git history retains them; rotate immediately if pushed).
- Secrets in CI/CD logs (configure your CI to mask secret values in output).
- Secrets baked into container images (visible to anyone with image pull access).
- Secrets in browser-exposed env vars (anything `NEXT_PUBLIC_*` etc. is *intentionally* exposed).
- Secrets returned by debug endpoints.
- Secrets shared in chat / email / docs.

### `.gitignore` minimums

For any web project, ensure:

```
.env
.env.local
.env.*.local
*.pem
*.key
secrets/
.aws/
.netrc
```

If the user is starting a project, suggest these. If reviewing, check that they've been in place since project inception (`git log --all -p -- .env` shows whether `.env` was ever committed).

For an existing project that has committed secrets: rotate the affected credentials immediately, then clean history with `git filter-repo` or BFG. Removing from the latest commit doesn't help — it's still in history.

## Default credentials and seed data

Many frameworks/services ship with default credentials (admin/admin, etc.). Production deployments must:

- Change all default passwords on first boot.
- Delete or disable test/demo accounts.
- Disable any accounts created by example seed scripts.
- Not deploy databases or admin panels with default credentials accessible from the network.

Common offenders: MongoDB without auth enabled, Redis bound to 0.0.0.0 without password, ElasticSearch with no auth, Jenkins with default admin, default admin pages exposed (`/admin`, `/wp-admin`, `/phpmyadmin`).

## Debug mode and development features in production

Each framework has a debug mode that exposes far more than acceptable in production:

- **Flask:** `app.debug = True` enables the Werkzeug interactive debugger — RCE on any error.
- **Django:** `DEBUG=True` shows tracebacks with local variables (including secrets in scope) and SQL queries.
- **Rails:** `config.consider_all_requests_local = true` enables the dev error page.
- **Express:** the default error handler returns stack traces.
- **Next.js:** running `next dev` instead of `next start`/`next build && next start` ships a development server.
- **GraphQL:** GraphiQL/Apollo Sandbox enabled by default in many setups.
- **Spring Boot Actuator:** `/actuator/*` endpoints exposing health, env, and heap dumps must require auth and be limited to internal access.

Verify in production:

- Debug flags off (often via `NODE_ENV=production`, `DJANGO_SETTINGS_MODULE=settings.prod`, etc.).
- Stack traces not in responses.
- Source maps, if served, point only to public JS — don't expose backend source maps.

## Default and verbose error responses

A 500 with full trace is a major info leak. A 404 with the framework name and version (`Django 4.2.7 — Page not found`) is a smaller leak but useful to attackers building a target profile. Best practices:

- Custom error pages for 404 and 500.
- Don't include framework version in `Server` or `X-Powered-By` headers (`app.disable('x-powered-by')` in Express; nginx `server_tokens off`).
- Generic error responses on APIs (see `apis-and-files.md`).

## Configuration as code, not by hand

For non-trivial deployments, infrastructure config should be version-controlled (Terraform, Pulumi, CDK, Ansible, etc.) rather than clicked into a console. This is a security control because:

- Reviewable changes.
- No "what's running where" mystery.
- Drift detection.
- Reproducibility for incident response.

For small projects, this is overkill — but at least keep a README documenting what services exist and how they're configured.

## Network configuration

- **Don't bind admin interfaces or databases to public IPs** unless absolutely required. Bind to 127.0.0.1 or a private network interface.
- **Use security groups / firewalls** to restrict access. Default deny inbound.
- **Internal services** should require authentication even on private networks (defense in depth — VPC compromise happens).

## Dependency configuration

Many vulnerabilities live in default config of dependencies:

- ORMs that load `__all__` fields by default (mass assignment — see `authorization.md`).
- HTTP clients that follow redirects to anywhere by default (SSRF — see `secure-coding.md`).
- Cookie libraries with insecure defaults.
- TLS libraries that accept old/weak ciphers if not configured.

Read the security section of any major dependency's docs once, when you first add it. Most have a "production checklist" page.

## Build and deploy pipeline

The CI/CD pipeline itself is a high-value target — it has access to deploy credentials, signing keys, and source.

- **Restrict who can trigger deploys to production.** Require approval for production deploys.
- **Don't echo secrets in build logs.** Configure CI to mask known secret values.
- **Use OIDC for cloud auth** (e.g., GitHub Actions → AWS via OIDC) rather than long-lived access keys stored as CI secrets.
- **Pin GitHub Actions to commit SHAs**, not floating tags. A compromised action versioned as `v1` can be backdoored without changing the version reference.
- **Sign artifacts** for high-stakes deployments (Sigstore, Cosign for containers).

## Cloud infrastructure quick wins

- S3 buckets default-private, with `Block Public Access` on at the account level. Pre-signed URLs for sharing, not public ACLs.
- IAM roles / service accounts scoped to minimum permissions; no `*` policies.
- Cloud audit logging enabled (CloudTrail, Cloud Audit Logs) and shipped to a separate account/project for tamper resistance.
- Backups of critical databases — and *test the restore*. An untested backup is a wish.

## Quick checklist

- [ ] No secrets in source code, committed config, or built images
- [ ] Secrets stored in a manager or platform env var, with audit logs
- [ ] `.env`, key files, and credentials in `.gitignore` from the start
- [ ] Different secrets per environment (dev / staging / prod)
- [ ] Default credentials changed and demo accounts removed
- [ ] Debug mode off in production; stack traces not in responses
- [ ] Server/framework version headers stripped
- [ ] Admin interfaces and databases not bound to public networks
- [ ] Cloud storage buckets default private; pre-signed URLs for shares
- [ ] CI/CD: approval gates for prod, secret masking, OIDC cloud auth, action pinning
- [ ] A documented (and tested) plan for rotating each class of secret
