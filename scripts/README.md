# Maintenance Scripts

This directory contains the tooling for keeping the skill current with upstream OWASP material and packaging it consistently. It also holds the end-user installers and the auto-update helper. The Node `npx` installer itself lives at `bin/install.js`.

## The workflow

The maintenance flow is deterministic:

1. `manifest.json` defines which upstream OWASP files are tracked.
2. `refresh.py` pulls those files into `_sources/` and writes `CHANGES.md`.
3. `sync_references.py` turns that cache into curated reference updates with fixed rules.
4. `package_skill.py` and `release_checksums.py` rebuild the distributable outputs.

The references stay opinionated, but they are no longer hand-edited after each upstream refresh.

## Recommended cadence

- **Quarterly** (default) — run on the first of Jan / Apr / Jul / Oct.
- **On-demand** when OWASP announces something significant: a new Top 10 edition, a new ASVS major version, a high-severity advisory affecting a topic the skill covers.
- **Weekly in GitHub Actions** if you want the repo to stay aligned with upstream without manual work.

## How to refresh

From the skill folder root:

```sh
python scripts/refresh.py
python scripts/sync_references.py
python scripts/package_skill.py
python scripts/release_checksums.py
```

This will:
1. Fetch each file in `manifest.json` from the upstream OWASP repos listed there, currently including `OWASP/Top10`, `OWASP/ASVS`, `OWASP/CheatSheetSeries`, and selected `OWASP/wstg` files.
2. Save them under `_sources/<source-name>/<filename>` (overwriting prior copies).
3. Compare against the previous run and write `_sources/CHANGES.md`.
4. Update `_sources/_state.json` with the new content hashes.

Then the curated references are regenerated from the refreshed cache, the package is rebuilt, and the release checksum is refreshed.

Other modes:
- `--dry-run` — list what would be fetched without fetching.
- `--quiet` — minimal output (good for CI).
- `--offline` — skip network; regenerate `CHANGES.md` from cached `_sources/` only.

## Customizing what's tracked

Edit `manifest.json`. It's grouped by source (`top10_2025`, `asvs_5_0`, `cheatsheets`). Add or remove file names from the `files` arrays.

When OWASP releases a new Top 10 edition (every 3-4 years), you'll add a new source group, e.g. `top10_2028`, and once stable, decide whether to retire the older one or keep both for transition.

The `cheatsheets` list is curated to the items most relevant for AI-assisted web app work. `wstg_selected` is intentionally narrow and should feed audit-checklist maintenance, not turn this skill into a penetration-testing agent. Adding more OWASP repos is fine when they directly support this skill's scope; keep the runtime references curated.

## Validate and package

Run the local validator before publishing:

```sh
python scripts/check_skill.py
```

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

Node / `npx` installer (macOS, Windows, Linux). Auto-detects which clients (`.claude`, `.codex`, `.gemini`) are already installed and updates each, copying all skill files including `AGENTS.md`, `GEMINI.md`, and `VERSION`. Flags: `--global`, `--claude` / `--codex` / `--gemini`, `--check`, `--force`, `--no-wire`.

```sh
npx --yes github:hov172/secure-webapp-skill --global
```

### `install.sh`

Bash installer for macOS and Linux (downloads the latest released `secure-webapp.skill`). Flags: `--local`, `--codex`, `--gemini`, `--local-codex`, `--local-gemini`, `--force`, `--no-wire`.

```sh
bash -c "$(curl -fsSL https://raw.githubusercontent.com/hov172/secure-webapp-skill/main/scripts/install.sh)" -- --codex
```

### `install.ps1`

PowerShell installer for Windows (no Node.js required).

```powershell
pwsh -File scripts/install.ps1 -Client gemini -Force
```

Parameters: `-Client claude|codex|gemini`, `-Local`, `-Force`, `-NoWire`.

## Auto-update

### `setup-auto-update.js`

Registers (or removes) an opt-in background job that runs the version-checked installer on a timer — launchd on macOS, Task Scheduler on Windows, cron on Linux.

```sh
node scripts/setup-auto-update.js            # enable weekly
node scripts/setup-auto-update.js --daily    # enable daily
node scripts/setup-auto-update.js --check    # show the plan, change nothing
node scripts/setup-auto-update.js --disable  # remove
```

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
      - run: python scripts/sync_references.py
      - run: python scripts/package_skill.py
      - run: python scripts/release_checksums.py
      - uses: peter-evans/create-pull-request@v6
        with:
          commit-message: "chore: refresh OWASP sources"
          title: "chore: refresh OWASP sources"
          branch: refresh-owasp-sources
          add-paths: |
            _sources/**
            references/**
            secure-webapp.skill
            SHA256SUMS
```

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
