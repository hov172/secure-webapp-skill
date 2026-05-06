# Security Audit Report — Generation Instructions

This file drives the `$secure-webapp report` mode. Follow every section in order. Do not skip sections; mark them "Not assessed" if genuinely out of scope rather than omitting them.

---

## Step 1 — Collect Source Material

Before writing a single line of the report, gather everything available in the current session:

- All findings raised during `$secure-webapp audit` or `quick-check` in this conversation
- All fixes applied (file paths, before/after diffs, test output)
- All items investigated and ruled out (false positives with reasoning)
- npm audit output, lint output, CI logs if shared
- Any findings the user described verbally

If no audit has been run yet, tell the user: "Run `$secure-webapp audit` first, or describe the findings you want documented." Do not generate a report from memory or assumptions.

---

## Step 2 — Determine Output Path

Write the report to the project under review. Default path:

```
docs/security-audit-report-YYYY-MM-DD.md
```

Use today's date. If `docs/` does not exist, write to the repo root as `security-audit-report-YYYY-MM-DD.md`. Tell the user where the file was written.

---

## Step 3 — Write the Report

Use the structure below exactly. Every finding gets its own `---` delimited block. Severity order: Critical → High → Medium → Low → Info.

---

### REPORT STRUCTURE

```markdown
# Security Audit Report
**Project:** <project name and repo URL>
**Date:** <YYYY-MM-DD>
**Auditor:** Claude Code (secure-webapp skill) assisted by <user name if known>
**Audit Type:** Static code review / dependency analysis / CI configuration review
**Report Version:** 1.0
**Classification:** Internal — Handle Appropriately

---

## Executive Summary

<2–4 sentences describing the overall security posture, the most significant risks found, and the current state after remediation.>

### Finding Counts

| Severity | Total Found | Fixed | Open | Accepted Risk | False Positive |
|---|---|---|---|---|---|
| Critical | | | | | |
| High | | | | | |
| Medium | | | | | |
| Low | | | | | |
| Info | | | | | |
| **Total** | | | | | |

### Key Risk Statements

- <One sentence on the most severe confirmed finding and its business impact.>
- <One sentence on the overall post-remediation posture.>
- <One sentence on what remains open or out of scope.>

---

## Scope

### Reviewed

- <List components, directories, files, or services that were reviewed>
- <Include both frontend and backend if applicable>
- <Include CI/CD configuration, Dockerfiles, dependency manifests>

### Not Reviewed

- <Be explicit about what was NOT examined: dynamic testing, penetration testing, infrastructure, third-party SaaS, mobile, etc.>
- <Note any time or access constraints>

### Methodology

- **Approach:** Static source code review, manual code inspection, automated dependency scanning
- **Standards:** OWASP Top 10:2025, ASVS 5.0, OWASP Cheat Sheet Series
- **Tools:** ESLint (lint), npm audit (dependency CVEs), manual code review
- **Audit threshold:** `--audit-level=high` (HIGH and CRITICAL findings block CI)

---

## Risk Rating Matrix

| Severity | Definition | Response Target |
|---|---|---|
| **Critical** | Exploitable now with severe business impact: data breach, account takeover, RCE, cross-tenant write | Fix immediately — block release |
| **High** | Exploitable with material impact: auth bypass, persistent XSS, sensitive data leak, SSRF | Fix this sprint |
| **Medium** | Real risk but conditional or limited-impact: requires specific preconditions or attacker access | Fix this quarter |
| **Low** | Best-practice gap with minimal exploitability in isolation | Track and address opportunistically |
| **Info** | Observation only — no direct risk, but worth noting for future hardening | No action required |

---

## Findings Summary

| ID | Title | Severity | OWASP Category | Status | Location |
|---|---|---|---|---|---|
| SEC-001 | ... | High | ... | Fixed | ... |

---

## Confirmed Findings

<!-- One block per confirmed finding, in severity order -->

---

### SEC-001 — <Title>

| Field | Value |
|---|---|
| **Severity** | Critical / High / Medium / Low |
| **OWASP Category** | e.g. A07:2025 – Identification and Authentication Failures |
| **Status** | Fixed / Open / Accepted Risk |
| **Location** | `path/to/file.js:line` or component/service name |
| **Affected Version** | Commit hash or date when issue was present |
| **Fixed In** | Commit hash or date of fix |

#### Description

<Technical description of the vulnerability. Explain what the code does, why it is vulnerable, and what property of secure software it violates. Be precise about the mechanism — e.g. "the Joi schema defined string fields without `.max()` bounds, meaning an attacker could send a string of arbitrary length that would be written directly to MongoDB without size restriction.">

#### Evidence

```<language>
// Vulnerable code (before fix)
<paste the actual vulnerable code snippet>
```

#### Attack Scenario

<This section must be as detailed as possible. Structure it as a step-by-step attack chain.>

**Threat Actor:** <Who would exploit this — external unauthenticated attacker / authenticated user / insider / automated scanner>

**Prerequisites:** <What the attacker needs — network access, a valid account, knowledge of the endpoint, etc.>

**Step-by-step exploitation:**

1. <Describe exactly how an attacker discovers or targets this vulnerability>
2. <Describe the specific request, payload, or action they take>
3. <Describe what happens server-side or client-side as a result>
4. <Describe the immediate outcome — what data is exposed, what system state changes, what access is gained>
5. <Describe the downstream impact — lateral movement, persistence, data exfiltration, service disruption>

**Concrete example payload or request:**
```
<Show an actual HTTP request, curl command, malformed input, or exploit payload that would have worked before the fix>
```

**Business Impact:** <Translate the technical impact into business terms: data breach, regulatory penalty, reputational damage, service outage, financial loss, etc.>

**Real-world precedent:** <Reference a known CVE, public breach, or vulnerability class that demonstrates this type of attack has been exploited in the wild, if applicable.>

#### Remediation Applied

<Describe what was changed to fix the vulnerability. Include the approach taken, not just the outcome.>

```<language>
// Fixed code (after fix)
<paste the actual fixed code snippet>
```

**Fix rationale:** <Why this specific fix addresses the root cause, not just the symptom.>

#### Verification

- <How the fix was confirmed: test output, npm audit result, manual verification step, CI pass>
- <Include pass/fail counts, audit output lines, or other concrete evidence>

---

## False Positives

Items investigated during the audit that were initially suspected but determined not to be vulnerabilities.

### FP-001 — <Title>

| Field | Value |
|---|---|
| **Initial Concern** | <What triggered the investigation> |
| **Verdict** | False Positive |
| **Reasoning** | <Precise technical explanation of why this is not a vulnerability — e.g. "The CSP header is set dynamically by the helmet middleware on every response; the absence from the static source file does not indicate it is missing at runtime. Confirmed via live HTTP response headers."> |

---

## Open Findings

Items confirmed as vulnerabilities that have NOT yet been fixed. Include full finding detail using the same format as Confirmed Findings above.

> If all findings are resolved, write: "No open findings at time of report."

---

## Remediation Roadmap

| Priority | Finding ID | Title | Owner | Target Date |
|---|---|---|---|---|
| Immediate | | | | |
| This Sprint | | | | |
| This Quarter | | | | |
| Backlog | | | | |

---

## Appendix A — Raw Tool Output

### npm audit (backend)

```
<paste full npm audit output>
```

### npm audit (frontend)

```
<paste full npm audit output>
```

### ESLint

```
<paste relevant lint output>
```

---

## Appendix B — Files Reviewed

<List every source file, config file, or CI file that was opened and read during the audit>

---

## Appendix C — Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | YYYY-MM-DD | | Initial report |
```

---

## Step 4 — Quality Gates Before Writing the File

Before calling Write, verify:

- [ ] Every confirmed finding has a populated Attack Scenario with step-by-step exploitation
- [ ] Every finding has a concrete evidence snippet (actual code, not paraphrased)
- [ ] Every false positive has precise technical reasoning, not just "it looked fine"
- [ ] Finding counts in the Executive Summary match the actual finding blocks
- [ ] The Findings Summary table IDs match the detailed finding IDs
- [ ] Open findings section is present (even if empty)
- [ ] Appendix A contains actual tool output from the session, not placeholders

## Step 5 — Tell the User

After writing the file:
1. State the output path
2. List every finding ID and title with its severity and status in one compact table
3. Note anything that could not be documented due to missing information
