<div align="center">
  <img src="assets/secure-webapp-large.svg" alt="Secure Web App Logo" width="150" />
  <h1>Secure Web App Skill</h1>
  
  <a href="https://github.com/hov172/secure-webapp-skill/actions/workflows/validate.yml"><img src="https://github.com/hov172/secure-webapp-skill/actions/workflows/validate.yml/badge.svg" alt="Validate Status" /></a>
  <a href="https://github.com/hov172/secure-webapp-skill/actions/workflows/refresh-owasp.yml"><img src="https://github.com/hov172/secure-webapp-skill/actions/workflows/refresh-owasp.yml/badge.svg" alt="OWASP Refresh Status" /></a>
  <a href="https://github.com/hov172/secure-webapp-skill/releases"><img src="https://img.shields.io/github/v/release/hov172/secure-webapp-skill?color=blue&label=release&cacheSeconds=0" alt="Release" /></a>
  <a href="https://github.com/hov172/secure-webapp-skill/blob/main/LICENSE.txt"><img src="https://img.shields.io/github/license/hov172/secure-webapp-skill?cacheSeconds=0" alt="License" /></a>
  
  <br />
  <p><strong>OWASP-grounded security guidance for AI-assisted development workflows.</strong></p>
</div>

---

`secure-webapp` is a Claude/Codex/Gemini skill for applying practical security guidance while building, editing, reviewing, or hardening web applications.

It is designed for AI workflows where security needs to be present by default, without turning every coding task into a long security lecture. The skill helps an agent notice risky patterns, choose safer implementations, and produce focused security review findings.

## Table of Contents
- [Installation and Updating](#installation-and-updating)
- [What This Skill Is For](#what-this-skill-is-for)
- [What This Skill Is Not](#what-this-skill-is-not)
- [Examples](#examples)
- [How It Works](#how-it-works)
- [Explicit Invocation Options](#explicit-invocation-options)
  - [`$secure-webapp audit`](#secure-webapp-audit)
  - [`$secure-webapp quick-check`](#secure-webapp-quick-check)
  - [`$secure-webapp harden`](#secure-webapp-harden)
  - [`$secure-webapp remediate`](#secure-webapp-remediate)
  - [`$secure-webapp design-review`](#secure-webapp-design-review)
  - [`$secure-webapp report`](#secure-webapp-report)
  - [`$secure-webapp update`](#secure-webapp-update)
  - [`$secure-webapp maintain`](#secure-webapp-maintain)
- [Reference Files](#reference-files)
- [Token Usage](#token-usage)
- [Maintainer Guide](#maintainer-guide)
- [OWASP Sources](#owasp-sources)
- [License and Attribution](#license-and-attribution)
- [Connect With Me](#-connect-with-me)

## Installation and Updating

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

#### Install for Claude: all projects

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

#### Install for Claude: one project

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

#### Install for Codex: all projects

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

#### Install for Codex: one project

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

#### Install for Gemini CLI: all projects

Install the source folder globally for Gemini CLI:

```sh
mkdir -p ~/.gemini/skills
cp -R secure-webapp ~/.gemini/skills/secure-webapp
```

Or install from the packaged archive:

```sh
mkdir -p ~/.gemini/skills
unzip secure-webapp.skill -d ~/.gemini/skills
```

After installing, restart Gemini CLI or start a new session so the skill index is refreshed.

#### Install for Gemini CLI: one project

If your Gemini client supports project-local skills, place the skill under the project:

```sh
mkdir -p /path/to/project/.gemini/skills
cp -R secure-webapp /path/to/project/.gemini/skills/secure-webapp
```

Or from the packaged archive:

```sh
mkdir -p /path/to/project/.gemini/skills
unzip secure-webapp.skill -d /path/to/project/.gemini/skills
```

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

### Updating the Skill

You can effortlessly self-update the local installation of this skill using your AI agent.

Example:

```text
Use $secure-webapp update to make sure you have the latest OWASP guidance.
```

The skill will run `npx --yes github:hov172/secure-webapp-skill --global` in the terminal to pull and install the newest version automatically.

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

## How It Works

The skill uses progressive disclosure:

1. **Skill metadata** tells the agent when to trigger the skill.
2. **`SKILL.md`** provides compact routing, behavior rules, and high-priority watchlist items.
3. **Reference files** are loaded only when relevant to the task.
4. **Audit checklist** is loaded only for review/audit/hardening workflows.
5. **Maintenance scripts** refresh upstream OWASP source material, deterministically sync the curated references, validate the package, and build the `.skill` archive.

This keeps token usage low during normal coding tasks while preserving deeper guidance for security-sensitive work.

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

### `$secure-webapp remediate`

Run an iterative audit→fix loop until the codebase is clean.

Example:

```text
Use $secure-webapp remediate to fix all security issues in this repo.
```

Expected behavior:

- Reads `assets/remediate-checklist.md` in full before starting
- Runs up to 8 audit→fix rounds
- Each round: full audit → auto-apply all code-fixable findings (Critical first) → log open items → re-audit
- Exits when code-fixable findings reach zero, or at round 8 — whichever comes first
- Never prompts for confirmation except for product-decision-level changes (feature removal, breaking API change, file deletion)
- Prints a final summary: rounds completed, findings fixed by severity, open items list, and any findings that hit the round cap

Open items that cannot be auto-fixed are categorized as:

- `no upstream patch` — vulnerable dependency with no available fix
- `infra change required` — WAF rule, network policy, TLS config, hosting setting
- `product decision required` — feature removal, API contract change, UX flow change
- `arch change required` — fundamental design issue that local code cannot patch
- `external action required` — third-party coordination, credential rotation, or vendor patch with no local workaround
- `manual risk assessment` — ambiguous threat model, needs human judgment

> [!NOTE]
> `$secure-webapp remediate` is not a replacement for `$secure-webapp audit` — it is a superset that audits, fixes, and re-audits until clean. Use `audit` when you want findings without auto-applying fixes.

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

### `$secure-webapp report`

Generate a professional security audit report document from findings in the current session.

Example:

```text
Use $secure-webapp report to document the findings from the audit.
```

Expected behavior:

- Requires a prior `$secure-webapp audit` or `quick-check` in the same session; if none has been run, prompts you to run one first
- Reads `assets/report-template.md` in full before writing anything
- Writes the report to `docs/security-audit-report-YYYY-MM-DD.md` in the project under review (or the repo root if `docs/` does not exist)
- Does **not** dump the report into the chat — it is written to a file
- Each confirmed finding includes: description, evidence (actual code), a detailed step-by-step attack scenario, remediation applied, and verification
- False positives and open items are documented in dedicated sections
- Runs quality gates before writing: finding counts match, attack scenarios are present, evidence is real code, tool output is from the session

Report sections produced:

- Executive Summary with severity counts table
- Key risk statements
- Scope (reviewed / not reviewed / methodology)
- Risk rating matrix
- Findings summary table
- Full finding blocks (severity-ordered: Critical → High → Medium → Low → Info)
- False positives
- Open findings
- Remediation roadmap
- Appendix A: raw tool output (npm audit, ESLint, etc.)
- Appendix B: files reviewed
- Appendix C: revision history

> [!NOTE]
> The Attack Scenario section in each finding is mandatory and must be detailed enough for a non-technical stakeholder to understand the real-world consequence and for a developer to understand the exact exploit chain.

### `$secure-webapp update`

Self-update the local installation of this skill to the latest version.

Example:

```text
Use $secure-webapp update to make sure you have the latest OWASP guidance.
```

Expected behavior:

- Runs `npx --yes github:hov172/secure-webapp-skill --global` in the terminal
- Replaces the installed `SKILL.md`, `references/`, and `assets/` files with the latest published versions
- No manual steps required — the agent handles the update in-session

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

## Token Usage

Approximate runtime token impact after optimization:

- Metadata only: about 100 tokens
- Triggered `SKILL.md`: about 1,000 tokens
- One relevant reference: commonly 2,000-3,000 tokens
- Quick-check: usually 3,000-6,000 tokens depending on references loaded
- Full audit: usually 8,000-14,000+ tokens depending on scope

The skill is designed so normal coding tasks load only the compact routing layer plus the most relevant reference files.

## Maintainer Guide

### Maintenance Workflow

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

### Automated OWASP Refresh

This repository includes `.github/workflows/refresh-owasp.yml`.

> [!IMPORTANT]
> **One-time setup:** Go to **Settings → Actions → General → Workflow permissions** and enable **"Allow GitHub Actions to create and approve pull requests"**. Without this, the PR creation step will fail.

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

### Releases

This repository includes `.github/workflows/release.yml`.

To publish a release:

```sh
git tag vX.Y.Z
git push origin vX.Y.Z
```

The release workflow builds `secure-webapp.skill`, generates `SHA256SUMS`, validates the package, and uploads both artifacts to the GitHub release.

### Packaging

The distributable artifact is:

```text
secure-webapp.skill
```

It contains:

- `SKILL.md`
- `references/`
- `assets/audit-checklist.md`
- `assets/remediate-checklist.md`
- `assets/report-template.md`
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

You can view the main **OWASP Foundation GitHub organization** here: <https://github.com/OWASP>.

The tracked upstream files are listed in `scripts/manifest.json`.

Repository: <https://github.com/hov172/secure-webapp-skill>

## License and Attribution

See `license.txt` for OWASP attribution and license notes.

OWASP and OWASP project names are trademarks of the OWASP Foundation. This skill is not an official OWASP project unless explicitly published as one.

---

## 🌐 Connect With Me
- [GitHub](https://github.com/hov172)
- [PowerShell Gallery](https://www.powershellgallery.com/profiles/hov172)
- 📨 Slack: **@Hov172**
- 🕹️ Discord: **Jay172_**
- [LinkedIn](https://www.linkedin.com/in/jesus-a-785bb616?trk=people-guest_people_search-card)
- 🐦 [Twitter / X (@AyalaSolutions)](https://twitter.com/AyalaSolutions)
- <a href="https://bsky.app/profile/ayalasolutions.bsky.social"><img src="https://raw.githubusercontent.com/bluesky-social/social-app/main/assets/logo.png" width="20" alt="Bluesky Logo"></a> [@AyalaSolutions](https://bsky.app/profile/ayalasolutions.bsky.social)
- [![Buy Me A Coffee](https://img.shields.io/badge/Buy_Me_A_Coffee-FFDD00?style=flat&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/hov172)
- 📧 *Contact via GitHub, Social accounts issues or discussions*

---

⭐ *If you find my tools useful, consider giving them a star to support future development!*
