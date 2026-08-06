# Cached upstream OWASP source material

This directory is populated by `scripts/refresh.py`. It holds raw upstream OWASP
markdown fetched verbatim from the official GitHub repositories listed in
`scripts/manifest.json`.

Purpose:

- Keep a local, reviewable cache of upstream OWASP files
- Make it possible to diff what changed between refreshes — that diff is the
  input to reference curation
- Feed the maintenance workflow without loading any of it into the runtime skill

## What lives here

| Path | Written by | What it is |
|---|---|---|
| `<source>/**` | `refresh.py` | Upstream markdown, verbatim, one directory per source (`top10_2025/`, `asvs_5_0/`, `cheatsheets/`, `wstg_selected/`) |
| `_state.json` | `refresh.py` | Content hashes and `last_run` from the last refresh; drives change detection, and `check_skill.py` fails the build if it goes stale |
| `CHANGES.md` | `refresh.py` | Human-readable summary of what moved upstream, plus any files that could not be fetched |
| `CURATION.md` | `curate_references.py` | Rationale for each proposed reference edit; becomes the refresh PR body |
| `briefs/` | `curate_references.py --write-briefs` | Self-contained curation briefs for any agent. Gitignored — scratch input, never committed |

`refresh.py` prunes cached files the manifest no longer tracks, so a rename
upstream cannot leave a stale copy behind pretending to be current.

## Why it is not packaged

The runtime `.skill` archive excludes `_sources/` entirely. It is maintainer
input, not skill content: the curated guidance in `references/` is what the agent
loads, and shipping the upstream markdown would cost tokens without adding
anything the references do not already say in their own words.

See `scripts/README.md` for the refresh and curation workflow.
