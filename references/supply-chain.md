# Software Supply Chain Security

Covers OWASP Top 10 2025 A03 (Software Supply Chain Failures) — a category that was elevated and renamed in 2025 from the old "Vulnerable and Outdated Components" to reflect that the threat is no longer just "old library has CVE." Modern attacks compromise *the supply chain itself* — npm package takeover, malicious build tools, signed releases altered before signing, IDE extensions, etc.

This is now A03, ranked #3 — and was the **top concern** in the 2025 community survey. It's relevant to every web app, even simple ones, because every modern web app has hundreds of transitive dependencies and a CI/CD pipeline.

## OWASP source sync

Deterministic notes regenerated from the refreshed OWASP source cache.

- Inventory: commit lockfiles and generate SBOMs for releases.
- CI/CD: pin GitHub Actions and other build dependencies.
- CI auth: prefer OIDC over long-lived cloud credentials.
- Releases: sign artifacts and keep provenance evidence.
- Install path: limit untrusted postinstall scripts and audit dependencies.
## Why this got worse

Recent supply chain incidents keep showing the same pattern: attackers target developer machines, package registries, CI runners, IDE extensions, build tools, and update paths because those systems hold the keys to publish artifacts that downstream users trust.

Use named incidents only as examples, not as static threat intelligence. When maintaining this reference, refresh the examples against current OWASP guidance and public advisories; the durable lesson is that dependency installation and build automation execute privileged code.

## What "supply chain" includes

Broader than people typically think:

- Direct dependencies (the packages in your `package.json` / `requirements.txt` / `Gemfile` / `go.mod`).
- **Transitive dependencies** (everything those packages depend on; usually 10-100x more than direct).
- Base container images (`FROM node:20`, `FROM python:3.12`).
- Build tools (your bundler, transpiler, test runner, linter — they execute arbitrary code at build time).
- IDE plugins / VS Code extensions on developer machines.
- GitHub Actions and other CI/CD plugins.
- The packages your CI pipeline installs (`actions/setup-node`, etc.).
- Operating system packages on hosts.
- Pre-built binaries downloaded by `postinstall` scripts.
- SaaS integrations whose webhooks/callbacks you process.
- AI/LLM models if you use them for code generation, summarization, etc.

Each of these is a potential injection point for an attacker.

## Defense in layers

### 1. Inventory: know what you ship

You can't defend a supply chain you can't see.

- **Lockfiles committed.** `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `Pipfile.lock`, `poetry.lock`, `Gemfile.lock`, `go.sum`. These pin exact versions of all transitive dependencies. Without them, every install can fetch different code.
- **Software Bill of Materials (SBOM).** Generated and stored with each release. Tools: `syft`, `cyclonedx-bom`, `cdxgen`. SBOMs let you answer "what's affected?" when a vulnerability is announced — without one, you guess.
- **Container provenance.** Container builds should attest to the build (Sigstore, SLSA framework). For Docker, `docker buildx build --attest=type=sbom,...`. For ECS/EKS, enforce signed images.
- **Continuous inventory.** Tools like Dependency-Track, Dependabot's dependency graph, GitHub's Software Composition Analysis maintain an evolving picture of what's deployed where.

### 2. Vulnerability awareness

- **Scan dependencies regularly.** `npm audit`, `pnpm audit`, `pip-audit`, `bundle-audit`, `cargo audit`, GitHub Dependabot alerts, Snyk, Trivy. In CI: fail the build on high/critical findings, with a documented exception process for legitimate cases.
- **Subscribe to advisories.** GitHub Advisory Database, OSV.dev, Vendor mailing lists for critical infrastructure (database, web framework). For high-stakes services, follow the maintainers on social media — emergency advisories often go out there first.
- **Track the time between advisory and patch.** "Mean time to remediate critical CVE" is a useful metric. Days, not months.

### 3. Choose dependencies deliberately

The decision to add a dependency is a security decision.

Before adding a package, look at:
- **Maintenance activity.** Last commit, last release, pace of issue response.
- **Maintainers.** Is it one person? Is there an org / company / foundation behind it?
- **Popularity.** Heavily-used packages get more security scrutiny (also more targeting, but on net safer).
- **Scope and size.** A 50-line utility shouldn't drag in 200 transitive dependencies. Smaller deps are easier to audit.
- **Alternative.** Stdlib first. A small dep written in-house is often safer than a small dep from npm.

For the larger functionality (cryptography, JWT, framework, ORM): use the well-known mainstream choice, not a clever new one.

### 4. Defend the install path

This is where many of the 2025 attacks landed.

- **Postinstall script awareness.** npm packages can run arbitrary code on install. `pnpm` is conservative by default; `npm install --ignore-scripts` blocks them entirely. Maintain an allowlist of which packages are permitted scripts (lockfile-lint can enforce this).
- **`npm ci` (not `npm install`) in production builds** to use the lockfile faithfully.
- **Pin GitHub Actions to commit SHAs**, not floating tags:
  ```yaml
  # WEAK
  - uses: actions/checkout@v4
  # STRONG
  - uses: actions/checkout@8e5e7e5ab8b370d6c329ec480221332ada57f0ab  # v4.0.0
  ```
  A compromised action versioned as `v4` can be silently re-pointed at malicious code. A SHA cannot.
- **Use Dependabot/Renovate to update those SHAs** on a regular cadence — pinning isn't useful if pins never move.
- **Verify package signatures where available.** PyPI is rolling out attestations; npm has provenance attestations (signed by GitHub Actions); Sigstore signs containers and binaries.

### 5. Defend the build pipeline

Your CI/CD has access to deploy credentials, signing keys, and source. Treat it like prod.

- **Restricted access.** Branch protection rules, required reviews, required CI passes before merge. Production deploys behind explicit approvals.
- **No secrets in CI logs.** Configure the CI to mask known secret values. Audit logs periodically.
- **Use OIDC for cloud auth.** GitHub Actions → AWS via OIDC role assumption instead of long-lived access keys stored as CI secrets. Less to leak; tokens are short-lived.
- **Scope CI permissions tightly.** A CI job that deploys staging shouldn't have prod credentials. A CI job for tests shouldn't have any deploy credentials.
- **Reproducible builds where possible.** Same input → same output. Lets you verify a published artifact matches the source.
- **Sign artifacts.** Sigstore (cosign for containers, gitsign for commits). The signature, plus an SBOM, is what lets downstream verify what they're getting.
- **Separate environments / accounts.** CI for staging and CI for prod don't share credentials; ideally they're different runners or different accounts.

### 6. Developer machine hygiene

The Shai-Hulud attack succeeded by harvesting npm tokens from developer machines. Treat your dev environment like a privileged credential store, because that's what it is.

- **MFA on every dev account** — npm, GitHub, AWS, package registries.
- **Patched OS, IDE, and IDE extensions.**
- **Audit IDE extensions** — they execute arbitrary code with your user's privileges.
- **Hardware-backed keys for code signing** if you maintain published packages.
- **Don't store long-lived credentials in `~/.npmrc` or `.env`** — use a credential helper or short-lived tokens.

### 7. Runtime controls

For production:

- **Don't deploy to all instances simultaneously** when updating dependencies. Canary/staged rollouts let you catch a malicious-update incident before it hits everyone.
- **Egress filtering.** Production app servers shouldn't be able to reach arbitrary internet hosts. Limits what a compromised dependency can exfiltrate.
- **Runtime monitoring for unusual behavior** — sudden outbound traffic, unexpected DNS lookups, new processes.

## When you find out a dependency is compromised

A real playbook because it happens often enough:

1. **Confirm scope.** Which version(s) are affected? Which of your services use them? (SBOM helps here.)
2. **Pin away from the bad version immediately** — even before the fix is available, pinning to a known-good prior version may be safer than the latest.
3. **Check for exfiltration.** If the malicious version ran in your CI or on dev machines, what credentials did it have access to? Rotate them.
4. **Patch and deploy** when a fix lands.
5. **Post-mortem**: how did this slip in? Should we tighten allowlists / scanning thresholds / human review thresholds?

For npm specifically, when a package is unpublished or yanked, you may have stale lockfile entries pointing at a now-missing tarball. `npm audit fix` and re-pinning is the path forward.

## Quick checklist

Inventory:
- [ ] Lockfile for every package manager committed
- [ ] SBOM generated per release; stored with the artifact
- [ ] Container/binary provenance via Sigstore or platform equivalent

Vulnerability mgmt:
- [ ] CI runs dependency scanning (`npm audit`, `pip-audit`, etc.) and fails on high/critical
- [ ] Dependabot or Renovate enabled with regular cadence
- [ ] Subscribed to advisories for critical dependencies

Install path:
- [ ] `npm ci` / `pip install --require-hashes` in CI rather than ad-hoc installs
- [ ] GitHub Actions pinned to commit SHAs (with Dependabot maintaining them)
- [ ] postinstall scripts reviewed for non-trusted packages

Pipeline:
- [ ] Production deploys gated on review/approval
- [ ] Cloud credentials via OIDC, not long-lived keys
- [ ] CI secrets masked in logs
- [ ] Separate credentials per environment

Developer:
- [ ] MFA on package registry accounts (npm, PyPI, etc.)
- [ ] IDE extensions reviewed; security updates applied
- [ ] No long-lived credentials in shell config / `.env` files

Runtime:
- [ ] Staged rollouts, not all-at-once deploys
- [ ] Egress filtering on app servers (or at least monitoring)
- [ ] Documented incident playbook for "dependency X just got compromised"

## Tools worth knowing

- **OWASP Dependency-Check / Dependency-Track** — open-source, language-agnostic vulnerability scanning.
- **Sigstore (cosign, gitsign)** — keyless signing for software artifacts.
- **OSV-Scanner** — Google's open-source vulnerability scanner using OSV.dev data.
- **Trivy** — container, IaC, and dependency scanner from Aqua.
- **Snyk** — commercial, broad coverage including container and IaC.
- **GitHub Advanced Security** — built-in if you're on GitHub: code scanning, secret scanning, dependency review on PRs.
- **socket.dev / Snyk Vulnerability DB** — supply chain risk intelligence (typo squatting, install-time risk indicators).

For most vibe-coder web apps: enable Dependabot + a CI scan + lockfile commits + SHA-pinned actions. That's 80% of the value with maybe an hour of setup.
