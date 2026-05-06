# Remediate Checklist

Used by `$secure-webapp remediate`. Runs audit→fix cycles up to 8 rounds until all code-fixable findings are resolved.

## Before Starting

Read `assets/audit-checklist.md` — every audit step in that file applies here. Do not re-read it each round; hold it in context for the session.

## Per-Round Procedure

At the start of each round, print:

```
--- Remediate: Round N of 8 ---
```

### Step 1 — Audit

Run a full audit using all 11 categories from `audit-checklist.md`. For each finding, classify it immediately:

- **code-fixable**: can be fully resolved by changing code in this repo right now
- **open-item**: requires an infrastructure change, architectural/product decision, upstream dependency patch, or manual risk assessment

### Step 2 — Fix

Auto-apply all code-fixable findings. No confirmation required (except for product-decision-level changes — see Rules). Apply fixes in severity order: Critical → High → Medium → Low. For each fix applied, print one line:

```
Fixed [severity]: <short description> — <file:line>
```

### Step 3 — Log Open Items

For each open-item finding (new ones this round only), append to the open items list:

```
[severity] <title> — <reason it cannot be auto-fixed>
```

Categories for "reason":
- `no upstream patch` — vulnerable dependency with no available fix
- `infra change required` — WAF rule, network policy, TLS config, hosting setting
- `product decision required` — feature removal, API contract change, UX flow change
- `arch change required` — fundamental design issue that local code cannot patch
- `manual risk assessment` — ambiguous threat model, needs human judgment
- `external action required` — third-party coordination, credential rotation, or vendor patch with no local workaround

### Step 4 — Convergence Check

Count code-fixable findings that remain *after* applying all fixes in Step 2.

- If **zero**: exit the loop. Print the final summary (see below).
- If **non-zero and round < 8**: start the next round.
- If **non-zero and round = 8**: exit the loop. Print the final summary, then print the remaining code-fixable findings under "Needs Manual Attention."

## Final Summary Format

Print at exit:

```
=== Remediate Complete ===

Rounds completed: N of 8
Findings fixed:
  Critical: N
  High: N
  Medium: N
  Low: N
  Total: N

Open Items (not auto-fixable):
  [severity] <title> — <reason>
  ...

Needs Manual Attention (hit round cap):
  [severity] <title> — <file:line> — <brief description>
  (omit this section if empty)
```

## Rules

- Never mark a finding as fixed unless the code change was actually applied.
- Never skip an audit category to save time — each round is a full audit.
- Never prompt the user mid-loop for fixes. Only prompt if a fix would require deleting a file, removing a feature, or making a breaking API change — those are product decisions, not code fixes.
- If the same open-item finding appears in multiple rounds, do not append a duplicate — skip it.
