# Design: `$secure-webapp remediate` Mode

**Date:** 2026-05-05  
**Status:** Approved

---

## Overview

Add a `$secure-webapp remediate` mode that loops audit→fix cycles until all code-fixable security findings are resolved, or a maximum of 8 rounds is reached.

---

## Motivation

Existing modes (`audit`, `harden`) are one-shot: audit finds issues, harden fixes them, but there is no built-in way to re-audit after fixes and keep going until clean. Each fix can expose new surface or unmask previously unreachable issues, so a single pass is often not enough. `remediate` automates the loop.

---

## Behavior

### Loop

Each round:

1. Run a full audit using `audit-checklist.md` categories
2. Classify every finding as `code-fixable` or `open-item`
3. Auto-apply all code-fixable fixes immediately (no user confirmation per fix)
4. Append any new open items to the open items log with: finding, severity, and one-line reason it cannot be auto-fixed
5. Check convergence:
   - If zero code-fixable findings remain → exit early with final summary
   - Otherwise → start next round

### Exit conditions

- **Clean exit:** code-fixable findings = 0 (any round)
- **Cap exit:** round 8 completes with findings still remaining → surface them explicitly for manual handling

### Max rounds: 8

The cap prevents infinite loops in pathological cases where each fix introduces a new finding. Expected convergence is 1–3 rounds in practice.

---

## Open Items

Findings that cannot be auto-fixed are logged throughout all rounds. Categories:

- Unpatched upstream dependency (no patch available)
- Requires infrastructure change (WAF, network policy, hosting config)
- Requires architectural or product decision (feature removal, API contract change)
- Ambiguous threat model (needs manual risk assessment)

Each open item is recorded with: description, severity, and reason it cannot be auto-fixed.

---

## Final Summary (printed at exit)

- Rounds completed
- Total findings fixed, broken down by severity (Critical / High / Medium / Low)
- Open items list (each with severity and reason)
- Any remaining code-fixable findings that hit the round 8 cap (for manual follow-up)

---

## Implementation

### Files to add

- `assets/remediate-checklist.md` — per-round procedure, convergence check, open items log format, final summary format

### Files to modify

- `SKILL.md` — add `$secure-webapp remediate` to the explicit invocation options table and behavior section

### Files to rebuild

- `secure-webapp.skill` — repackage after changes via `scripts/package_skill.py`

---

## Non-goals

- No interactive confirmation per fix (auto-apply only)
- No URL/live-site scanning (code review only, consistent with existing skill scope)
- No per-finding rollback — fixes are applied as normal code edits
