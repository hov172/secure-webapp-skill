# Maintenance Scripts

This directory contains the tooling for keeping the skill current with upstream OWASP material and packaging it consistently. It also holds the end-user installers and the auto-update helper. The Node `npx` installer itself lives at `bin/install.js`.

## What's here

| Script | Purpose | Needs a credential? |
|---|---|---|
| `refresh.py` | Fetch tracked upstream OWASP files into `_sources/`, diff them, write `CHANGES.md` | No |
| `curate_references.py` | Propose reference edits from the upstream diff, or render briefs for any agent | Only to call a model; `--dry-run`, `--print-prompt` and `--write-briefs` do not |
| `verify_agent_changes.py` | Bound what an agent-driven run was allowed to change | No |
| `eval_skill.py` | Detection-corpus gate, plus the graded behavioral eval | No |
| `check_skill.py` | Validate the package, the workflows, and cross-file consistency | No |
| `package_skill.py` | Build the reproducible `.skill` archive | No |
| `release_checksums.py` | Generate `SHA256SUMS` (and an optional signature) | No |
| `install.sh` / `install.ps1` | End-user installers for environments without Node.js | No |
| `setup-auto-update.js` | Register an opt-in background updater | No |
| `manifest.json` | Which upstream files are tracked | — |
| `reference_map.json` | Which upstream sources ground which reference | — |

## The workflow

1. `manifest.json` defines which upstream OWASP files are tracked.
2. `refresh.py` pulls those files into `_sources/` and writes `CHANGES.md`.
3. `curate_references.py` reads the **diff** of what moved upstream and proposes targeted edits to the references it grounds (`reference_map.json` says which is which). With no credential, use `--write-briefs` and hand the briefs to whatever agent you use.
4. `verify_agent_changes.py` bounds the result when an agent did the editing — only `references/` may change.
5. **A maintainer reviews those edits.** Nothing merges automatically.
6. `eval_skill.py --check` confirms the detection corpus still covers every watchlist item.
7. `package_skill.py` and `release_checksums.py` rebuild the distributable outputs.

Step 3 replaced `sync_references.py`, which regenerated a fixed bullet list from
substring matches against the cache. Across twelve refreshes it touched
`references/` twice — once to insert itself, once to delete a blank line — while
the README claimed references were "synced automatically." The difference is the input: pattern
matches on the cache tell you nothing, the diff tells you what actually changed.

Step 4 is not optional. Model-proposed edits to security guidance are a starting
point for review, not an authority. `check_skill.py` fails the build if the
refresh workflow ever auto-merges, or if it commits `references/` without having
run the curation step.

A renamed or removed upstream file no longer fails the refresh: the cached copy
is kept, `CHANGES.md` records the failure, and CI opens a maintenance issue.
`refresh.py` exits non-zero only when a whole source comes back empty, or under
`--strict`.

**Quiet weeks produce no commit.** `refresh.py` rewrites `_state.json` and
`CHANGES.md` only when the upstream content or the fetch-error list actually
changed. Previously it stamped a fresh `last_run` every run, so an unchanged
week still produced a diff — a pull request every Monday, and a commit that
pushed `main` past the last release tag for nothing. To keep `check_skill.py`'s
30-day staleness gate meaningful through a genuinely quiet stretch, the
timestamp is refreshed on a heartbeat every `REFRESH_HEARTBEAT_DAYS` (default
20) even when nothing moved.

## Recommended cadence

- **Quarterly** (default) — run on the first of Jan / Apr / Jul / Oct.
- **On-demand** when OWASP announces something significant: a new Top 10 edition, a new ASVS major version, a high-severity advisory affecting a topic the skill covers.
- **Weekly in GitHub Actions** if you want the repo to stay aligned with upstream without manual work.

## How to refresh

From the skill folder root:

```sh
python scripts/refresh.py
python scripts/curate_references.py          # needs a credential; no-ops without one
# or, with no credential and any agent:
#   python scripts/curate_references.py --write-briefs
#   ...hand the briefs to your agent, apply its edits...
#   python scripts/verify_agent_changes.py
python scripts/eval_skill.py --check
python scripts/package_skill.py
python scripts/release_checksums.py
```

This will:
1. Fetch each file in `manifest.json` from the upstream OWASP repos listed there, currently including `OWASP/Top10`, `OWASP/ASVS`, `OWASP/CheatSheetSeries`, and selected `OWASP/wstg` files.
2. Save them under `_sources/<source-name>/<filename>` (overwriting prior copies).
3. Compare against the previous run and write `_sources/CHANGES.md`.
4. Update `_sources/_state.json` with the new content hashes.

5. Prune cached files the manifest no longer tracks, so a rename upstream cannot leave a stale copy behind.

Then a maintainer updates the curated references, the package is rebuilt, and the release checksum is refreshed.

Other modes:
- `--dry-run` — list what would be fetched without fetching.
- `--quiet` — minimal output (good for CI). Fetch errors are still printed.
- `--offline` — skip network; regenerate `CHANGES.md` from cached `_sources/` only.
- `--strict` — treat any fetch error as fatal (default is to keep the cached copy and carry on).

## Reference curation

### `curate_references.py`

Runs after `refresh.py`, while the upstream changes are still uncommitted — that
working-tree diff is the input. For each reference whose mapped sources moved,
it sends the current reference plus the unified diff to a model and asks for a
targeted edit, or for no change.

```sh
python scripts/curate_references.py --dry-run             # what's in scope; no API call
python scripts/curate_references.py --print-prompt        # exact prompt for the first reference; no API call
ANTHROPIC_API_KEY=sk-... python scripts/curate_references.py
python scripts/curate_references.py --reference auth-and-sessions.md
```

Without `ANTHROPIC_API_KEY` it prints what it would curate and exits 0, so the
no-key refresh path is unchanged.

**What the model sees.** The current reference, the upstream diff with 25 lines
of context (three — git's default — is not enough to tell whether guidance
actually shifted), the full current text of each changed upstream file where
size allows, and the names of any sibling references grounded in the same
sources, so it stays in its lane instead of duplicating their material. Use
`--print-prompt` to inspect exactly what would be sent.

**Guardrails.** It only writes files under `references/`, only those whose
mapped sources actually changed, and it rejects any proposal that drops the
title, falls below 75% of the original length, reintroduces the old generated
section marker, comes back identical, leaves unbalanced code fences, collapses
the section structure, links to a reference that does not exist, or introduces a
credential-shaped string. Rejections are reported, never silently swallowed.

**Validation, both ends.** The repository must validate *before* any edit — if
it does not, the run refuses and spends no model calls, because otherwise an
unrelated pre-existing problem would fail the post-run check and revert good
edits. After editing, `check_skill.py` runs again; if it fails, every edit from
that run is reverted. A curation run never leaves the tree worse than it found
it.

Rationales land in `_sources/CURATION.md`, which becomes part of the pull
request body so a reviewer sees the reasoning beside the diff.

Tunable via environment: `CURATION_MODEL` (default `claude-opus-5`),
`CURATION_MAX_REFERENCES` (default 4 per run), `CURATION_MAX_DIFF_CHARS`
(default 60000), `CURATION_DIFF_CONTEXT` (default 25),
`CURATION_FULL_SOURCE_MAX_CHARS` (default 45000), `CURATION_MAX_FULL_SOURCES`
(default 3).

In CI, set the `ANTHROPIC_API_KEY` repository secret (or
`CLAUDE_CODE_OAUTH_TOKEN`) to enable it; leave both unset and the weekly refresh
keeps working exactly as it does today, just without proposed edits.

**No credential required.** Nothing else in this repository needs one — refresh,
validation, the corpus, packaging and releases all work without it. To curate
without storing a secret anywhere, do it locally:

```sh
python scripts/refresh.py
# then, in your agent: "read _sources/CHANGES.md and update the affected references"
python scripts/verify_agent_changes.py
```

That applies the same bounds locally that CI would, so a supervised local
session is strictly the better version of the agent path: more context, a real
conversation, and no secret in the repository.

**Any agent, not just Claude.** `--write-briefs` renders one self-contained
curation brief per in-scope reference — instructions, the current reference, the
upstream diff, and the full changed source text — with no API call:

```sh
python scripts/refresh.py
python scripts/curate_references.py --write-briefs   # -> _sources/briefs/*.brief.md
```

Hand a brief to Codex, Gemini CLI, or anything else, apply its edits, then run
`verify_agent_changes.py`. Briefs are gitignored and `_sources/` never ships, so
they cannot leak into the package.

### `verify_agent_changes.py`

Bounds what an agent-driven curation run was allowed to change. The scripted
path never needs this — the model there cannot touch the filesystem — but
`.github/workflows/curate-agent.yml` gives Claude Code real write access, so the
boundary is re-established afterward:

```sh
python scripts/verify_agent_changes.py
python scripts/verify_agent_changes.py --allow references _sources
```

It fails if anything outside `references/` changed, if nothing changed at all,
or if the tree no longer validates. `SKILL.md`, `scripts/`, `.github/`, `bin/`,
`agents/`, `VERSION`, `package.json`, `secure-webapp.skill` and `SHA256SUMS` are
rejected even when the allowlist is widened — a curation run has no business
changing how the skill is built, validated, or shipped. Useful by hand after any
agent-assisted editing session, not just in CI.

### `reference_map.json`

Declares which upstream sources ground which reference — the input that tells
curation what to re-read. `check_skill.py` validates it both ways: every file in
`references/` must have an entry, and every source it names must still be
tracked in `manifest.json`.

## Customizing what's tracked

Edit `manifest.json`. It's grouped by source (`top10_2025`, `asvs_5_0`, `cheatsheets`). Add or remove file names from the `files` arrays.

When OWASP releases a new Top 10 edition (every 3-4 years), you'll add a new source group, e.g. `top10_2028`, and once stable, decide whether to retire the older one or keep both for transition.

The `cheatsheets` list is curated to the items most relevant for AI-assisted web app work. `wstg_selected` is intentionally narrow and should feed audit-checklist maintenance, not turn this skill into a penetration-testing agent. Adding more OWASP repos is fine when they directly support this skill's scope; keep the runtime references curated.

## Validate and package

Run the local validator before publishing:

```sh
python scripts/check_skill.py
```

It checks package shape, installer/`SKILL.md` mode parity, installer checksum
verification, and that the upstream cache is not stale (older than
`SKILL_MAX_SOURCE_AGE_DAYS`, default 30). Then confirm the detection corpus is
in sync:

```sh
python scripts/eval_skill.py --check
```

That gate also rejects a fixture containing a real provider key format, and
fails if `tests/clean/` is empty — without secure counterparts the corpus would
only measure recall, and flagging everything would score perfectly.

For the behavioural eval, grading reports recall over `tests/fixtures/` and
precision over `tests/clean/`; either a miss or a medium-or-higher false positive
fails. Blind it first, since filenames and the directory split both leak the
answer:

```sh
python scripts/eval_skill.py --blind /tmp/corpus     # neutral names, flat dir
python scripts/eval_skill.py --grade findings.json --map /tmp/corpus_map.json
```

See `tests/README.md` for the full protocol.

Build the distributable archive:

```sh
python scripts/package_skill.py
```

The package script excludes `_sources/` caches, the bootstrap installers (`install.sh`, `install.ps1`, `bin/install.js`), and local build artifacts. `_sources/` is maintainer input, not runtime skill content.

## Versioning

`VERSION` (repository root) is the single source of truth for the skill version and **must match `version` in `package.json`** — `check_skill.py` fails the build if they drift. Bump both when publishing user-visible changes so existing installs detect the update via the version check.

## Installers

End-user installers. All are version-checked: they skip installation when the installed copy already matches the published version (pass a force flag to override). For Codex and Gemini they also wire the agent's `AGENTS.md` / `GEMINI.md` to point at the installed `SKILL.md` (skip with `--no-wire`); Claude auto-discovers `~/.claude/skills` and needs no wiring.

### `bin/install.js`

Node / `npx` installer (macOS, Windows, Linux). Auto-detects which clients (`.claude`, `.codex`, `.gemini`) are already installed and updates each. It installs the same file set as the released `.skill` archive — including `scripts/`, which `$secure-webapp maintain` and `setup-auto-update.js` need; `check_skill.py` fails the build if the two lists diverge. Flags: `--global`, `--claude` / `--codex` / `--gemini`, `--check`, `--force`, `--no-wire`.

```sh
npx --yes github:hov172/secure-webapp-skill --global
```

### `install.sh`

Bash installer for macOS and Linux (downloads the latest released `secure-webapp.skill` and verifies it against the release's `SHA256SUMS` before unpacking — fails closed on mismatch, missing sums, or no available hashing tool). Flags: `--local`, `--codex`, `--gemini`, `--local-codex`, `--local-gemini`, `--force`, `--no-wire`, `--no-verify`.

```sh
bash -c "$(curl -fsSL https://raw.githubusercontent.com/hov172/secure-webapp-skill/main/scripts/install.sh)" -- --codex
```

### `install.ps1`

PowerShell installer for Windows (no Node.js required). Verifies the download against the release's `SHA256SUMS` before unpacking.

```powershell
pwsh -File scripts/install.ps1 -Client gemini -Force
```

Parameters: `-Client claude|codex|gemini`, `-Local`, `-Force`, `-NoWire`, `-NoVerify`.

## Auto-update

### `setup-auto-update.js`

Registers (or removes) an opt-in background job that runs the version-checked installer on a timer — launchd on macOS, Task Scheduler on Windows, cron on Linux.

```sh
node scripts/setup-auto-update.js            # enable weekly
node scripts/setup-auto-update.js --daily    # enable daily
node scripts/setup-auto-update.js --check    # show the plan, change nothing
node scripts/setup-auto-update.js --disable  # remove
```

Scheduled jobs run with a minimal `PATH`, so the job explicitly exports one containing both npx's directory and the directory of the node binary that ran the setup — npx is a `#!/usr/bin/env node` script and cannot start without node on `PATH`. It also logs to `~/Library/Logs/com.hov172.secure-webapp-update.log` (macOS) or `~/.cache/secure-webapp-update.log` (Linux); `--check` prints both the resolved `PATH` and the log path. Enabling again rewrites the job in place, which is the supported way to repair one written by a version before 1.4.12.

## CI integration (optional)

For a hands-off setup, run the refresh weekly in GitHub Actions and open a pull request when upstream OWASP content changes:

For production CI, pin third-party actions to commit SHAs and let Dependabot or Renovate update those pins.

```yaml
# .github/workflows/refresh-owasp.yml
name: Refresh OWASP sources
on:
  schedule:
    - cron: '0 8 * * 1'  # weekly Monday 08:00 UTC
  workflow_dispatch:
jobs:
  refresh:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.x' }
      - run: python scripts/refresh.py
      - run: python scripts/package_skill.py
      - run: python scripts/release_checksums.py
      - uses: peter-evans/create-pull-request@v6
        with:
          commit-message: "chore: refresh OWASP sources"
          title: "chore: refresh OWASP sources"
          branch: refresh-owasp-sources
          add-paths: |
            _sources/**
            secure-webapp.skill
            SHA256SUMS
```

Note what is **not** here: `references/**` is not in `add-paths`, and there is no
auto-merge step. Upstream OWASP text is third-party content; letting it reach a
published artifact without review is a supply-chain path. The live workflow in
`.github/workflows/refresh-owasp.yml` also opens a maintenance issue when a
manifest file 404s, so a rename upstream surfaces instead of silently freezing
the cache. `check_skill.py` enforces both properties.

## What lives in `_sources/`

- One subfolder per source (`top10_2025/`, `asvs_5_0/`, `cheatsheets/`).
- Additional selected source folders may appear as `manifest.json` grows, such as `wstg_selected/`.
- Raw markdown files as fetched from upstream — verbatim, no transformation.
- `_state.json` — content hashes from the last successful refresh (used for change detection).
- `CHANGES.md` — human-readable summary of what changed in the most recent refresh.

`_sources/` is maintainer material, not runtime skill content. It is **not** packaged into the `.skill` bundle and **not** loaded by Claude when the skill triggers. It exists to ground the curated references in real upstream content during maintenance.

## Licenses

The OWASP material being pulled is licensed:

- Top 10 — CC BY 3.0
- ASVS — CC BY-SA 4.0
- Cheat Sheet Series — CC BY 4.0
- WSTG — CC BY-SA 4.0

These licenses permit redistribution with attribution. If you redistribute this skill (e.g., publish it to a marketplace), include the upstream attribution somewhere visible — referencing OWASP and linking to the source projects is typical and expected.
