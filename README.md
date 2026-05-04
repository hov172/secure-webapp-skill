<div align="center">
  <img src="assets/secure-webapp-large.svg" alt="Secure Web App Logo" width="150" />
  <h1>Secure Web App Skill</h1>
  
  <a href="https://github.com/hov172/secure-webapp-skill/actions/workflows/validate.yml"><img src="https://github.com/hov172/secure-webapp-skill/actions/workflows/validate.yml/badge.svg" alt="Validate Status" /></a>
  <a href="https://github.com/hov172/secure-webapp-skill/actions/workflows/refresh-owasp.yml"><img src="https://github.com/hov172/secure-webapp-skill/actions/workflows/refresh-owasp.yml/badge.svg" alt="OWASP Refresh Status" /></a>
  <a href="https://github.com/hov172/secure-webapp-skill/releases"><img src="https://img.shields.io/github/v/release/hov172/secure-webapp-skill?color=blue&label=release" alt="Release" /></a>
  <a href="https://github.com/hov172/secure-webapp-skill/blob/main/license.txt"><img src="https://img.shields.io/github/license/hov172/secure-webapp-skill" alt="License" /></a>
  
  <br />
  <p><strong>OWASP-grounded security guidance for AI-assisted development workflows.</strong></p>
</div>

---

`secure-webapp` is a Claude/Codex/Gemini skill for applying practical security guidance while building, editing, reviewing, or hardening web applications.

It is designed for AI workflows where security needs to be present by default, without turning every coding task into a long security lecture. The skill helps an agent notice risky patterns, choose safer implementations, and produce focused security review findings.

## Table of Contents
- [What This Skill Is For](#what-this-skill-is-for)
- [What This Skill Is Not](#what-this-skill-is-not)
- [How It Works](#how-it-works)
- [Installation](#installation)
- [Explicit Invocation Options](#explicit-invocation-options)
- [Reference Files](#reference-files)
- [Examples](#examples)
- [OWASP Sources](#owasp-sources)
- [Maintenance Workflow](#maintenance-workflow)

## What This Skill Is For

Use this skill when working on web application code or design that touches:

- Authentication, signup, login, MFA, password reset, sessions, cookies, JWTs, OAuth, or OIDC
- API endpoints, GraphQL, WebSockets, file uploads, file downloads, and pre-signed URLs
- User input, forms, search, templates, DOM rendering, SQL/NoSQL queries, shell commands, or CSV exports
- Authorization, roles, ownership checks, tenant isolation, IDOR, and admin functionality
- CORS, CSP, CSRF, security headers, redirects, frontend storage, and browser security behavior
- Secrets, `.env` files, debug mode, logging, error handling, production configuration, and dependency management
- Secure design, threat modeling, supply-chain risk, exceptional conditions, and security audits

The skill is stack-agnostic. It applies to frameworks such as Next.js, Express, Django, Flask, FastAPI, Rails, Spring, Laravel, Go services, and similar web stacks.

## What This Skill Is Not

This is not a penetration-testing agent and does not claim to exploit running systems. It is for:

- Secure implementation
- Static code review
- Design review
- Hardening recommendations
- Focused remediation
- OWASP-informed audit checklists

> [!WARNING]
> If dynamic testing or formal penetration testing is needed, this skill can help prepare scope and review code, but it should **not** replace a qualified security test.

## How It Works

The skill uses progressive disclosure:

1. **Skill metadata** tells the agent when to trigger the skill.
2. **`SKILL.md`** provides compact routing, behavior rules, and high-priority watchlist items.
3. **Reference files** are loaded only when relevant to the task.
4. **Audit checklist** is loaded only for review/audit/hardening workflows.
5. **Maintenance scripts** refresh upstream OWASP source material, deterministically sync the curated references, validate the package, and build the `.skill` archive.

This keeps token usage low during normal coding tasks while preserving deeper guidance for security-sensitive work.

## Installation

The fastest way to install the skill is using `npx` *(requires [Node.js](https://nodejs.org/))* . This downloads and copies the required files directly into your agent's skill directory without leaving a cloned repository behind.

### Quick Install via npx (Recommended)

**Install project-locally (current directory):**
```sh
npx github:hov172/secure-webapp-skill
```

**Install globally (system-wide):**
```sh
npx github:hov172/secure-webapp-skill --global
```

**Install for Codex or Gemini instead of Claude:**
```sh
npx github:hov172/secure-webapp-skill --codex
npx github:hov172/secure-webapp-skill --gemini
```

### Quick Install via Bash

For environments without Node.js, you can install the skill via bash:

**Install globally (system-wide):**
```sh
bash -c "$(curl -fsSL https://raw.githubusercontent.com/hov172/secure-webapp-skill/main/scripts/install.sh)"
```

**Install project-locally (current directory):**
```sh
bash -c "$(curl -fsSL https://raw.githubusercontent.com/hov172/secure-webapp-skill/main/scripts/install.sh)" -- --local
```

**Install for Codex or Gemini:**
```sh
bash -c "$(curl -fsSL https://raw.githubusercontent.com/hov172/secure-webapp-skill/main/scripts/install.sh)" -- --codex
bash -c "$(curl -fsSL https://raw.githubusercontent.com/hov172/secure-webapp-skill/main/scripts/install.sh)" -- --gemini
```

### Manual Install

> [!NOTE]
> You can also manually install the skill from either the source folder or the packaged archive.

Use the **source folder** when you want to maintain or edit the skill.

Use the **`.skill` archive** when you want a clean runtime artifact:

```text
secure-webapp.skill
```

### Install for Claude: all projects

Install the source folder globally for Claude-style clients:

```sh
mkdir -p ~/.claude/skills
cp -R secure-webapp ~/.claude/skills/secure-webapp
```

Or install from the packaged archive:

```sh
mkdir -p ~/.claude/skills
unzip secure-webapp.skill -d ~/.claude/skills
```

After installing, restart Claude or start a new session so the skill index is refreshed.

### Install for Claude: one project

If your Claude client supports project-local skills, place the skill under the project:

```sh
mkdir -p /path/to/project/.claude/skills
cp -R secure-webapp /path/to/project/.claude/skills/secure-webapp
```

Or from the packaged archive:

```sh
mkdir -p /path/to/project/.claude/skills
unzip secure-webapp.skill -d /path/to/project/.claude/skills
```

Use project-local installation when the skill should only affect one repository.

### Install for Codex: all projects

Install the source folder globally for Codex-style clients:

```sh
mkdir -p ~/.codex/skills
cp -R secure-webapp ~/.codex/skills/secure-webapp
```

Or install from the packaged archive:

```sh
mkdir -p ~/.codex/skills
unzip secure-webapp.skill -d ~/.codex/skills
```

After installing, restart Codex or start a new session so the skill index is refreshed.

### Install for Codex: one project

If your Codex client supports project-local skills, place the skill under the project:

```sh
mkdir -p /path/to/project/.codex/skills
cp -R secure-webapp /path/to/project/.codex/skills/secure-webapp
```

Or from the packaged archive:

```sh
mkdir -p /path/to/project/.codex/skills
unzip secure-webapp.skill -d /path/to/project/.codex/skills
```

Use global installation for security guidance across all web-app work. Use project-local installation when the skill should travel with one repo or stay limited to one codebase.

### Verify installation

Ask the agent to use the skill explicitly:

```text
Use $secure-webapp quick-check on this repo.
```

If the agent does not recognize the skill, check that the installed folder contains `SKILL.md` directly:

```text
~/.claude/skills/secure-webapp/SKILL.md
~/.codex/skills/secure-webapp/SKILL.md
~/.gemini/skills/secure-webapp/SKILL.md
```

Avoid an extra nested folder such as `secure-webapp/secure-webapp/SKILL.md`.

## Explicit Invocation Options

The skill can be triggered naturally by the task, or explicitly with these options:

### `$secure-webapp audit`

Run a full prioritized security review.

Example:

```text
Use $secure-webapp audit to review this Express app for security issues.
```

Expected behavior:

- Read `assets/audit-checklist.md`
- Inspect real code
- Prioritize findings by severity
- Include file/line evidence when possible
- Provide concrete fixes
- State what was not reviewed

### `$secure-webapp quick-check`

Run a fast top-risk pass.

Example:

```text
Use $secure-webapp quick-check on this PR before I merge it.
```

Focus areas:

- Authorization and IDOR
- Auth/session handling
- Secrets and debug config
- Injection and XSS
- Uploads/downloads
- SSRF and external URL fetches
- JWT/OAuth handling

### `$secure-webapp harden`

Apply secure changes directly when code edits are authorized.

Example:

```text
Use $secure-webapp harden to fix the session cookie and CORS settings.
```

Expected behavior:

- Make small targeted patches
- Preserve existing architecture
- Add or update focused tests when useful
- Explain security-relevant choices briefly

### `$secure-webapp design-review`

Review a feature before implementation.

Example:

```text
Use $secure-webapp design-review for a file-sharing feature with expiring public links.
```

Expected behavior:

- Identify trust boundaries
- Identify abuse cases
- Define authorization requirements
- Flag sensitive data handling
- Check failure modes and race conditions
- List unresolved product/security questions

### `$secure-webapp maintain`

Update or validate the skill package itself.

Example:

```text
Use $secure-webapp maintain to refresh OWASP sources and rebuild the package.
```

Expected behavior:

- Run or update `scripts/refresh.py`
- Run `scripts/sync_references.py`
- Rebuild the package and checksums
- Run `scripts/check_skill.py`

## Reference Files

The skill routes tasks to focused references:

| Topic | Reference |
|---|---|
| Input handling, injection, XSS, command injection, CSV injection | `references/input-handling.md` |
| Login, signup, password storage, MFA, reset flows, sessions | `references/auth-and-sessions.md` |
| Authorization, IDOR, roles, ownership, tenant isolation | `references/authorization.md` |
| JWTs, API tokens, refresh tokens, OAuth, OIDC | `references/tokens-and-oauth.md` |
| REST, GraphQL, WebSocket, file uploads/downloads | `references/apis-and-files.md` |
| Cookies, CORS, CSP, CSRF, headers, browser controls | `references/frontend-and-headers.md` |
| Secrets, environment config, debug mode, defaults | `references/secrets-and-config.md` |
| Crypto, encryption, key management, PII, password hashing | `references/data-and-crypto.md` |
| Dependencies, lockfiles, SBOM, CI/CD, signed artifacts | `references/supply-chain.md` |
| SSRF, defensive coding, race conditions, deserialization | `references/secure-coding.md` |
| Logging, errors, fail-closed behavior, exceptional conditions | `references/logging-and-errors.md` |
| Threat modeling, design review, multi-tenancy, abuse cases | `references/insecure-design.md` |

## Examples

### Secure Code Generation

```text
Use $secure-webapp to add a password reset flow to this Django app.
```

The skill should guide the agent toward:

- Random high-entropy reset tokens
- Hashing reset tokens in the database
- Short expiration
- Single-use tokens
- Generic reset responses
- Rate limiting
- No account enumeration

### Authorization Review

```text
Use $secure-webapp quick-check to inspect these API routes for IDOR issues.
```

The skill should look for route handlers that fetch by ID without scoping by the current user or tenant.

Risky pattern:

```javascript
const order = await db.orders.findById(req.params.id);
```

Safer pattern:

```javascript
const order = await db.orders.findOne({
  where: { id: req.params.id, userId: req.user.id }
});
```

### Upload Hardening

```text
Use $secure-webapp harden for this profile-photo upload endpoint.
```

The skill should consider:

- Maximum file size
- Server-generated filenames
- Storage outside the web root
- Magic-byte validation
- Restricted content types
- Safe image processing
- Authenticated downloads when needed

### Design Review

```text
Use $secure-webapp design-review for an invite-link feature.
```

The skill should ask or infer:

- Who can create invite links?
- What resource does the invite grant access to?
- Can links be revoked?
- How long do they live?
- Are tokens stored hashed?
- Are invites single-use or multi-use?
- Are invite acceptances logged?
- What happens if the user is removed before accepting?

## OWASP Sources

This skill is curated from multiple OWASP projects:

- OWASP Top 10:2025  
  <https://github.com/OWASP/Top10>

- OWASP Application Security Verification Standard 5.0  
  <https://github.com/OWASP/ASVS>

- OWASP Cheat Sheet Series  
  <https://github.com/OWASP/CheatSheetSeries>

- OWASP Web Security Testing Guide, selected files  
  <https://github.com/OWASP/wstg>

The tracked upstream files are listed in `scripts/manifest.json`.

Repository: <https://github.com/hov172/secure-webapp-skill>

## Maintenance Workflow

There are two ways this skill gets updated:

1. **Locally, by a maintainer** when you want to refresh the repo yourself.
2. **Automatically on GitHub** when the scheduled workflow runs.

The update order is the same in both cases:

1. Fetch the latest OWASP source files into `_sources/`.
2. Regenerate the curated `references/*.md` files with deterministic rules.
3. Rebuild `secure-webapp.skill`.
4. Regenerate `SHA256SUMS`.
5. Validate the result.

Refresh upstream OWASP source material locally:

```sh
python3 scripts/refresh.py
```

Sync curated references from the refreshed cache:

```sh
python3 scripts/sync_references.py
```

Dry-run refresh without downloading:

```sh
python3 scripts/refresh.py --dry-run
```

Validate the skill package:

```sh
python3 scripts/check_skill.py
```

Build the `.skill` archive:

```sh
python3 scripts/package_skill.py
```

Generate release checksums:

```sh
python3 scripts/release_checksums.py
```

Generate checksums and a detached GPG signature when a signing key is available:

```sh
python3 scripts/release_checksums.py --sign
```

The update flow does not require an API key. It reads OWASP repositories directly, then deterministically updates the curated references from the refreshed cache.

The package script intentionally excludes GitHub-facing docs, `_sources/`, cache files, and local scratch directories from the runtime `.skill` archive.

## Automated OWASP Refresh

This repository includes `.github/workflows/refresh-owasp.yml`.

The workflow runs weekly on Monday at 09:00 UTC and can also be started manually from GitHub Actions. It:

1. Runs `python3 scripts/refresh.py --quiet`.
2. Writes upstream OWASP changes under `_sources/`.
3. Runs `python3 scripts/sync_references.py`.
4. Rebuilds `secure-webapp.skill` and `SHA256SUMS`.
5. Opens a pull request on `refresh/owasp-sources` when changes are detected.
6. Automatically squash-merges the pull request.

This is the no-key automation path: OWASP source files are refreshed automatically, the curated `references/*.md` files are deterministically synced from the refreshed cache, and the distributable package is rebuilt from the updated tree.

> [!IMPORTANT]
> The skill content changes only through this refresh pipeline. Runtime installs do not self-update inside your agent; they update when you reinstall the rebuilt `.skill` archive or refresh the source folder via `npx` or `bash`.

The repository can keep `_sources/` in Git history for maintenance. The runtime `.skill` package still excludes `_sources/` so token usage stays low.

## Releases

This repository includes `.github/workflows/release.yml`.

To publish a release:

```sh
git tag vX.Y.Z
git push origin vX.Y.Z
```

The release workflow builds `secure-webapp.skill`, generates `SHA256SUMS`, validates the package, and uploads both artifacts to the GitHub release.

## Packaging

The distributable artifact is:

```text
secure-webapp.skill
```

It contains:

- `SKILL.md`
- `references/`
- `assets/audit-checklist.md`
- `assets/secure-webapp-small.svg`
- `assets/secure-webapp-large.svg`
- `agents/openai.yaml`
- `scripts/`
- `license.txt`

It does not contain:

- `package.json`
- `README.md`
- `_sources/`
- `.gitignore`
- `scripts/README.md`
- `scripts/install.sh`
- `bin/install.js`
- `SHA256SUMS` / `SHA256SUMS.asc`
- Python cache files
- Local build scratch directories

## Token Usage

Approximate runtime token impact after optimization:

- Metadata only: about 100 tokens
- Triggered `SKILL.md`: about 1,000 tokens
- One relevant reference: commonly 2,000-3,000 tokens
- Quick-check: usually 3,000-6,000 tokens depending on references loaded
- Full audit: usually 8,000-14,000+ tokens depending on scope

The skill is designed so normal coding tasks load only the compact routing layer plus the most relevant reference files.

## License and Attribution

See `license.txt` for OWASP attribution and license notes.

OWASP and OWASP project names are trademarks of the OWASP Foundation. This skill is not an official OWASP project unless explicitly published as one.
