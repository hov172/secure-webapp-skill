# Remediate Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `$secure-webapp remediate` — an audit→fix loop that runs up to 8 rounds, auto-applying all code-fixable findings each round and logging open items (infra, arch, unpatched deps) until code-fixable findings reach zero.

**Architecture:** Two file changes — a new `assets/remediate-checklist.md` that defines the per-round procedure, and an update to `SKILL.md` to register the new mode. After edits, `scripts/check_skill.py` validates correctness and `scripts/package_skill.py` rebuilds the `.skill` archive.

**Tech Stack:** Markdown (skill files), Python 3 (build/validation scripts)

---

### Task 1: Create `assets/remediate-checklist.md`

**Files:**
- Create: `assets/remediate-checklist.md`

- [ ] **Step 1: Create the file with this exact content**

```markdown
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

Auto-apply all code-fixable findings. No confirmation required. Apply fixes in severity order: Critical → High → Medium → Low. For each fix applied, print one line:

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

### Step 4 — Convergence Check

Count remaining code-fixable findings.

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
- If the same open-item finding appears in multiple rounds, do not duplicate it in the log — update in place.
```

- [ ] **Step 2: Verify the file exists**

```bash
ls assets/remediate-checklist.md
```

Expected: file listed with no error.

- [ ] **Step 3: Commit**

```bash
git add assets/remediate-checklist.md
git commit -m "feat: add assets/remediate-checklist.md for remediate mode"
```

---

### Task 2: Update `SKILL.md` — add remediate to invocation options

**Files:**
- Modify: `SKILL.md:14-21` (explicit invocation options block)

- [ ] **Step 1: Add remediate entry after the `harden` line**

In the explicit invocation options block, after the line:
```
- `$secure-webapp harden`: make secure code/config changes directly where the user has authorized edits; verify with focused tests/checks.
```

Insert:
```
- `$secure-webapp remediate`: iterative audit→fix loop. Read `assets/remediate-checklist.md`. Auto-apply all code-fixable findings each round, log open items (infra/arch/unpatched deps), and repeat up to 8 rounds until code-fixable findings reach zero. Print a final summary of rounds completed, findings fixed by severity, open items, and any findings that hit the round cap.
```

- [ ] **Step 2: Add remediate behavior rule to the Behavior section**

In the `## Behavior` section, after the line:
```
- For harden, prefer small patches that preserve existing architecture; note any risk that needs manual/product approval.
```

Insert:
```
- For remediate, read `assets/remediate-checklist.md` in full before starting. Run up to 8 audit→fix rounds. Auto-apply all code-fixable fixes; never prompt for confirmation except for product-decision-level changes (feature removal, breaking API change, file deletion). Log open items once; do not duplicate across rounds. Exit clean when code-fixable findings = 0 or round 8 completes.
```

- [ ] **Step 3: Commit**

```bash
git add SKILL.md
git commit -m "feat: add \$secure-webapp remediate mode to SKILL.md"
```

---

### Task 3: Validate and repackage

**Files:**
- Run: `scripts/check_skill.py`
- Run: `scripts/package_skill.py`
- Modified: `secure-webapp.skill`

- [ ] **Step 1: Run validation**

```bash
python3 scripts/check_skill.py
```

Expected output:
```
OK: secure-webapp skill validation passed
```

If it fails, read the FAIL message, fix the referenced file, and re-run before continuing.

- [ ] **Step 2: Rebuild the skill archive**

```bash
python3 scripts/package_skill.py
```

Expected output:
```
Built /path/to/secure-webapp-skill/secure-webapp.skill
```

- [ ] **Step 3: Run validation again against the rebuilt package**

```bash
python3 scripts/check_skill.py
```

Expected: same `OK` output as Step 1.

- [ ] **Step 4: Commit**

```bash
git add secure-webapp.skill
git commit -m "chore: rebuild skill archive with remediate mode"
```
