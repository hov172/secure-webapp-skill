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

`secure-webapp` is a Claude/Codex/Gemini skill for applying practical security guidance while building, editing, reviewing, or hardening web applications. It also works with any other AI agent that loads skills from a directory or reads an `AGENTS.md` / `GEMINI.md` instruction file.

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
  - [Reference Curation](#reference-curation)
  - [Detection Corpus](#detection-corpus)
- [Changelog](CHANGELOG.md)
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

> [!NOTE]
> Codex and Gemini do not auto-load a `skills/` folder, so the installer also wires their instruction file — `~/.codex/AGENTS.md` for Codex, `~/.gemini/GEMINI.md` for Gemini — with a managed pointer block to the installed `SKILL.md` (Gemini uses an `@import`). This makes the skill active in every session. Pass `--no-wire` to skip it. Claude needs no wiring — it auto-discovers `~/.claude/skills`.

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

> [!NOTE]
> The bash installer downloads `SHA256SUMS` from the same release and verifies
> the archive before unpacking. It fails closed: a mismatch, a missing sums
> file, or no available hashing tool aborts the install. `--no-verify`
> overrides this and is not recommended.

### Quick Install on Windows (PowerShell)

On Windows the `npx` commands above work as-is (Node.js required). If you prefer not to use Node.js, use the PowerShell installer, which downloads the latest release, verifies it against the published `SHA256SUMS` (use `-NoVerify` to skip), and version-checks before unpacking:

```powershell
# Install for Claude (default)
irm https://raw.githubusercontent.com/hov172/secure-webapp-skill/main/scripts/install.ps1 | iex
```

To target Codex or Gemini, or to force a reinstall, download the script and pass parameters:

```powershell
irm https://raw.githubusercontent.com/hov172/secure-webapp-skill/main/scripts/install.ps1 -OutFile install.ps1
pwsh -File install.ps1 -Client codex
pwsh -File install.ps1 -Client gemini -Force
```

Installs go to `%USERPROFILE%\.claude\skills\secure-webapp` (or `.codex` / `.gemini`). Add `-Local` to install into the current directory instead.

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

> [!NOTE]
> The skill ships with `AGENTS.md` and `GEMINI.md` at its root so agents that read those instruction files (Codex, Gemini CLI, and others) pick up *when* and *how* to use the skill. Claude Code discovers it from `SKILL.md` automatically.

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

#### Install for other AI agents

Any agent that loads skills from a directory, or that reads an `AGENTS.md` / `GEMINI.md` instruction file, can use this skill.

1. Copy the skill into a location your agent reads. The packaged archive unzips to a `secure-webapp/` folder containing `SKILL.md`, `references/`, `assets/`, `agents/`, `AGENTS.md`, and `GEMINI.md`:

   ```sh
   unzip secure-webapp.skill -d /path/your/agent/reads
   ```

2. Point your agent at it:
   - **Codex** and other `AGENTS.md`-aware tools read `AGENTS.md`.
   - **Gemini CLI** reads `GEMINI.md`.
   - Agents with a skills loader read `secure-webapp/SKILL.md` directly.

3. The guidance in `SKILL.md` uses Claude Code tool names. On other agents, map them to your equivalents (file read, file edit/write, shell, search) — the security content itself is platform-independent.

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

The skill will run `npx --yes github:hov172/secure-webapp-skill --global` in the terminal. The installer is **platform-aware and version-checked**:

- It auto-detects every client already installed (`.claude`, `.codex`, `.gemini`) and updates each one — so a Codex or Gemini user updates their own install, not a stray Claude copy.
- It compares the installed `VERSION` against the published version and **skips clients that are already current**, printing `already up to date` instead of reinstalling.

Useful flags:

```sh
# Update only one client
npx --yes github:hov172/secure-webapp-skill --global --codex
npx --yes github:hov172/secure-webapp-skill --global --gemini

# Report what would change without touching any files
npx --yes github:hov172/secure-webapp-skill --global --check

# Reinstall even if the version matches
npx --yes github:hov172/secure-webapp-skill --global --force
```

The bash installer (`scripts/install.sh`) applies the same version check and also accepts `--force`.

> [!NOTE]
> By default this is check-on-demand: installed copies stay frozen until you run `$secure-webapp update`, the installer, or reinstall the `.skill` archive — at which point the version check decides whether anything actually needs to change. To run the check automatically in the background, see [Automatic Updates](#automatic-updates-optional) below.

### Automatic Updates (optional)

For unattended updates, register a background scheduler with the cross-platform helper. It runs the version-checked installer on a timer — on **macOS** (launchd), **Windows** (Task Scheduler), or **Linux** (cron) — which only reinstalls when a newer version is published.

```sh
# Preview what would be scheduled (changes nothing)
node scripts/setup-auto-update.js --check

# Enable weekly (default) or daily background checks
node scripts/setup-auto-update.js
node scripts/setup-auto-update.js --daily

# Turn it off
node scripts/setup-auto-update.js --disable
```

On Windows, run the same commands in PowerShell or Command Prompt (Node.js required); the job is created in Task Scheduler as `secure-webapp-update`. This is the only true background option — the agents themselves do not poll; the scheduler runs the installer and the version check decides whether anything changes.

## What This Skill Is For

Use this skill when working on web application code or design that touches:

- Authentication, signup, login, MFA, password reset, sessions, cookies, JWTs, OAuth, or OIDC
- API endpoints, GraphQL, WebSockets, file uploads, file downloads, and pre-signed URLs
- User input, forms, search, templates, DOM rendering, SQL/NoSQL queries, shell commands, or CSV exports
- Authorization, roles, ownership checks, tenant isolation, IDOR, and admin functionality
- CORS, CSP, CSRF, security headers, redirects, frontend storage, and browser security behavior
- Secrets, `.env` files, debug mode, logging, error handling, production configuration, and dependency management
- Secure design, threat modeling, supply-chain risk, exceptional conditions, and security audits
- LLM/AI features: prompt construction, RAG and retrieval scoping, agent tool calls, MCP servers, and model output that gets rendered or executed

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
5. **Maintenance scripts** refresh upstream OWASP source material, validate the package, grade the detection corpus, and build the `.skill` archive.

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
- Is **platform-aware**: auto-detects every installed client (`.claude`, `.codex`, `.gemini`) and updates each, instead of assuming Claude
- Is **version-checked**: compares the installed `VERSION` against the published version and skips clients that are already current (`already up to date`)
- Replaces the installed `SKILL.md`, `AGENTS.md`, `GEMINI.md`, `references/`, `assets/`, `agents/`, `scripts/`, and `VERSION` with the latest published versions
- Accepts `--codex` / `--gemini` / `--claude` (target one client), `--check` (report only), and `--force` (reinstall regardless of version)
- For Codex/Gemini, refreshes the `AGENTS.md` / `GEMINI.md` discovery pointer so the skill stays active (skip with `--no-wire`)
- No manual steps required — the agent handles the update in-session

For unattended updates, see [Automatic Updates](#automatic-updates-optional).

### `$secure-webapp maintain`

Update or validate the skill package itself.

Example:

```text
Use $secure-webapp maintain to refresh OWASP sources and rebuild the package.
```

Expected behavior:

- Run or update `scripts/refresh.py`
- Run `scripts/curate_references.py` to propose reference edits from the upstream diff, and review them
- Rebuild the package and checksums
- Run `scripts/check_skill.py` and `scripts/eval_skill.py --check`

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
| LLM/AI features, prompt injection, RAG, agent tools, MCP servers | `references/ai-and-llm.md` |

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
2. Propose reference edits from the diff of what actually changed upstream.
3. Rebuild `secure-webapp.skill`.
4. Regenerate `SHA256SUMS`.
5. Validate the result.
6. **A human reviews the proposed edits before anything merges.**

> [!NOTE]
> Step 2 used to be a `sync_references.py` script that pattern-matched the cache
> and emitted a fixed bullet list; across twelve refreshes it touched a reference
> twice — once to insert itself, once to delete a blank line. It was replaced in v1.4.0 by
> `scripts/curate_references.py`, which works from the upstream **diff** instead
> — see [Reference Curation](#reference-curation).

Refresh upstream OWASP source material locally:

```sh
python3 scripts/refresh.py
```

Propose reference edits from what changed (needs `ANTHROPIC_API_KEY`; no-ops without it):

```sh
python3 scripts/curate_references.py --dry-run     # show what's in scope
python3 scripts/curate_references.py
```

Dry-run refresh without downloading:

```sh
python3 scripts/refresh.py --dry-run
```

Validate the skill package:

```sh
python3 scripts/check_skill.py
```

This checks package shape, that the modes in `SKILL.md` match all three installers and the docs, that the installers verify their downloads, that `reference_map.json` and `manifest.json` agree — and that the upstream cache is not stale. "Stale" defaults to 30 days and is tunable with `SKILL_MAX_SOURCE_AGE_DAYS`; it exists so a broken refresh turns normal CI red instead of hiding in a scheduled workflow.

Check the detection corpus still covers every watchlist item:

```sh
python3 scripts/eval_skill.py --check
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

The refresh itself does not require an API key — it reads OWASP repositories directly into the local cache. Only the optional curation step needs one; without it, references simply stay as they are and you triage `_sources/CHANGES.md` yourself.

A single upstream file that has been renamed or removed no longer fails the whole refresh — the cached copy is kept, the failure is reported in `_sources/CHANGES.md`, and CI opens a maintenance issue naming the file. Use `--strict` to make any fetch error fatal.

The package script intentionally excludes GitHub-facing docs, `_sources/`, cache files, and local scratch directories from the runtime `.skill` archive.

### Reference Curation

`scripts/curate_references.py` is how upstream OWASP changes actually reach the
curated references. It runs after `refresh.py`, while the upstream changes are
still uncommitted — that working-tree diff is its input.

For each reference whose grounding sources changed (per `scripts/reference_map.json`),
it sends the current reference plus the unified upstream diff to a model and asks
one question: does this change mean the guidance is now wrong, incomplete, or
outdated — and if so, what is the smallest edit that fixes it? Default is no change.

```sh
python3 scripts/curate_references.py --dry-run                    # scope only, no API call
python3 scripts/curate_references.py --print-prompt               # exact prompt, no API call
ANTHROPIC_API_KEY=sk-... python3 scripts/curate_references.py
python3 scripts/curate_references.py --reference auth-and-sessions.md
```

**What the model sees:** the current reference, the upstream diff with 25 lines
of context, the full current text of each changed upstream file where size
allows, and the names of sibling references grounded in the same sources so it
does not duplicate their material. `--print-prompt` shows exactly what would be
sent.

**Guardrails**, because this edits security guidance:

- Only references whose mapped sources actually changed are considered.
- Only files under `references/` are ever written — the model never touches the
  filesystem; the script reads, passes text, validates, then writes.
- A proposal is rejected if it drops the title, falls below 75% of the original
  length, reintroduces the old generated-section marker, is a no-op, leaves
  unbalanced code fences, collapses the section structure, links to a reference
  that does not exist, or introduces a credential-shaped string. Rejections are
  reported, never silently swallowed.
- The repository must validate **before** any edit; if it does not, the run
  refuses and spends no model calls. After editing, the validator runs again and
  every edit from that run is reverted if it fails.
- Rationales are written to `_sources/CURATION.md` and become part of the pull
  request body, so a reviewer sees the reasoning beside the diff.
- Per-run caps on references touched (`CURATION_MAX_REFERENCES`, default 4) and
  diff size (`CURATION_MAX_DIFF_CHARS`, default 60000). Model is
  `CURATION_MODEL`, default `claude-opus-5`.

> [!IMPORTANT]
> Model-proposed edits to security guidance are a starting point for review, not
> an authority. The refresh PR does not auto-merge, and `check_skill.py` fails
> the build if it ever does — or if the workflow commits `references/` without
> having run the curation step. Blind writes to the references are the failure
> mode this replaced; the guard exists so it cannot come back.

#### Curating without storing a credential

**Nothing in this repository requires an API key.** The weekly refresh,
validation, the detection corpus, packaging, and releases all run without one.
Automated curation is the single optional extra.

If you would rather not put a credential in the repository — a reasonable
default for a security-focused project — curate locally instead. You get the
*better* version of the agent path: full context, a real conversation, and you
watching it.

```sh
python3 scripts/refresh.py                  # fetch upstream, write _sources/CHANGES.md
# then, in Claude Code / Codex / Gemini:
#   "read _sources/CHANGES.md and update the affected references/*.md"
python3 scripts/verify_agent_changes.py     # same bounds CI would apply
python3 scripts/check_skill.py
```

`verify_agent_changes.py` enforces the identical boundary locally that the CI
workflow enforces: only `references/` may change, and the tree must still
validate. So a local agent session gets the same guarantee without a secret
existing anywhere.

This works with **any** agent, not just Claude Code. `curate_references.py` can
render self-contained curation briefs that Codex, Gemini CLI, or anything else
can consume — no Anthropic API involved:

```sh
python3 scripts/refresh.py
python3 scripts/curate_references.py --write-briefs    # -> _sources/briefs/*.brief.md
```

Each brief carries the curation instructions, the current reference, the
upstream diff, and the full changed source text. Hand one to your agent, apply
its edits, then run `verify_agent_changes.py`. Briefs are gitignored and can
never reach the package.

`--print-prompt` renders the same thing for a single reference to stdout.

**If you do want it automated in CI:** set the `ANTHROPIC_API_KEY` repository
secret (or `CLAUDE_CODE_OAUTH_TOKEN`), optionally the `CURATION_MODEL` variable.
Leave both unset and the weekly refresh works exactly as it does now, minus the
proposed edits — the curation step no-ops and exits 0.

#### The agent variant (manual only)

The scripted path above handles routine upstream edits well, but it is
single-turn: it cannot go read a whole document, compare several references, or
reason about a change that spans them. For the rare structural case — a new
OWASP Top 10 edition, an ASVS major version — there is
`.github/workflows/curate-agent.yml`, which runs Claude Code with real repository
access.

Trigger it from **Actions → Curate references (agent) → Run workflow**, and
describe what changed upstream and what you want revised. It optionally refreshes
first, validates the tree as a baseline, curates, and opens a PR.

> [!IMPORTANT]
> This workflow is `workflow_dispatch` only and must stay that way — it is never
> scheduled, and `check_skill.py` fails the build if anyone adds a `schedule:`
> trigger, removes the bounds check, or adds auto-merge.

The scripted path is safe *by construction*: the model never touches the
filesystem, so "only `references/` can change" is a property of the code. An
agent has real write access, so that boundary is re-established afterward by
`scripts/verify_agent_changes.py`, which fails the run — no PR opened — if
anything outside `references/` was touched. `SKILL.md`, `scripts/`, `.github/`,
`bin/`, `agents/`, `VERSION`, `package.json`, and the packaged archive are
rejected even if someone widens the allowlist. You can run it by hand after any
agent-assisted editing session:

```sh
python3 scripts/verify_agent_changes.py
```

### Detection Corpus

`scripts/check_skill.py` proves the package has the right *shape*. `tests/`
proves it has the right *effect*.

`tests/fixtures/` holds one deliberately vulnerable file per Always-On Watchlist
item in `SKILL.md`, and `tests/expectations.json` records what a correct finding
for each one looks like (severity floor plus expected terms).

```sh
# Structural gate — runs in CI, no model needed.
# Fails if a watchlist item has no fixture, or a fixture is undeclared/missing.
python3 scripts/eval_skill.py --check

# Behavioral eval — run by hand after changing SKILL.md, references, or checklists.
python3 scripts/eval_skill.py --prompt          # prints the audit prompt
python3 scripts/eval_skill.py --grade findings.json
```

Grading reports `PASS` / `UNDER` (found but under-severity) / `MISS` per fixture
plus overall recall, and exits non-zero on anything short of full recall. Add a
watchlist item without adding a fixture and the build goes red.

> [!WARNING]
> Every file in `tests/fixtures/` is insecure on purpose. They are detection
> targets, not examples. They are excluded from the `.skill` archive.

### Automated OWASP Refresh

This repository includes `.github/workflows/refresh-owasp.yml`.

> [!IMPORTANT]
> **One-time setup:** Go to **Settings → Actions → General → Workflow permissions** and enable **"Allow GitHub Actions to create and approve pull requests"**. Without this, the PR creation step will fail.

The workflow runs weekly on Monday at 09:00 UTC and can also be started manually from GitHub Actions. It:

1. Runs `python3 scripts/refresh.py`.
2. Writes upstream OWASP changes under `_sources/`.
3. Runs `python3 scripts/curate_references.py` to propose reference edits from those diffs (skipped automatically when no `ANTHROPIC_API_KEY` secret is set).
4. Rebuilds `secure-webapp.skill` and `SHA256SUMS`.
5. Opens a pull request on `refresh/owasp-sources`, with the curation rationale in the body.
6. Opens (or comments on) a maintenance issue if any manifest file could not be fetched.

Without the API key this is a no-key automation path: sources refresh, the package rebuilds, references stay put.

> [!IMPORTANT]
> **The refresh PR does not auto-merge.** Upstream OWASP content — or a model's
> reading of it — reaching a shipped artifact without human review is a
> supply-chain path this repository deliberately closes. `check_skill.py` fails
> the build if auto-merge returns, or if the workflow commits `references/`
> without having run the curation step.

> [!IMPORTANT]
> Runtime installs do not self-update inside your agent; they update when you reinstall via `npx` / `bash` / PowerShell, run `$secure-webapp update`, or enable [Automatic Updates](#automatic-updates-optional). Each path is version-checked, so it only reinstalls when a newer version is published.

The repository can keep `_sources/` in Git history for maintenance. The runtime `.skill` package still excludes `_sources/` so token usage stays low.

### Releases

This repository includes `.github/workflows/release.yml`.

To publish a release:

```sh
git tag vX.Y.Z
git push origin vX.Y.Z
```

The release workflow builds `secure-webapp.skill`, generates `SHA256SUMS`, validates the package, and uploads both artifacts to the GitHub release.

### Versioning and Installers

`VERSION` (repository root) is the single source of truth for the skill version and **must match `version` in `package.json`** — `scripts/check_skill.py` fails the build if they drift. Bump both when publishing user-visible changes so existing installs detect the update via the version check.

The version is read by the cross-platform installers and updater:

| Script | Platform | Purpose |
|---|---|---|
| `bin/install.js` | macOS / Windows / Linux | Node/`npx` installer; auto-detects clients, version-checks, installs the same file set as the `.skill` archive |
| `scripts/install.sh` | macOS / Linux | Bash installer for environments without Node.js; verifies the download against `SHA256SUMS` (`--no-verify` to override) |
| `scripts/install.ps1` | Windows | PowerShell installer for environments without Node.js; verifies the download against `SHA256SUMS` (`-NoVerify` to override) |
| `scripts/setup-auto-update.js` | macOS / Windows / Linux | Registers an opt-in background updater (launchd / Task Scheduler / cron) |

### Packaging

The distributable artifact is:

```text
secure-webapp.skill
```

It contains:

- `SKILL.md`
- `AGENTS.md`
- `GEMINI.md`
- `VERSION`
- `references/`
- `assets/audit-checklist.md`
- `assets/remediate-checklist.md`
- `assets/report-template.md`
- `assets/secure-webapp-small.svg`
- `assets/secure-webapp-large.svg`
- `agents/claude.yaml`
- `agents/openai.yaml`
- `agents/gemini.yaml`
- `scripts/` (including `setup-auto-update.js` and the maintenance scripts)
- `LICENSE` (MIT, for the skill itself)
- `LICENSE.txt` (upstream OWASP attribution)

It does not contain:

- `package.json`
- `README.md`
- `_sources/`
- `tests/`
- `.gitignore`
- `scripts/README.md`
- `scripts/install.sh`
- `scripts/install.ps1`
- `bin/install.js`

`bin/install.js` installs this same set. `scripts/check_skill.py` fails the build if the two diverge.
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

The skill itself is MIT licensed — see `LICENSE`. Upstream OWASP attribution and the licenses of the source material are in `LICENSE.txt`. Both files ship inside the `.skill` archive and in every install.

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
