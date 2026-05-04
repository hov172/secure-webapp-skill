# Cached upstream OWASP source material

This directory is populated by `scripts/refresh.py`. It holds raw upstream OWASP markdown fetched from the official GitHub repositories listed in `scripts/manifest.json`.

Purpose:

- Keep a local, reviewable cache of upstream OWASP files
- Make it easy to inspect what changed between refreshes
- Feed the maintenance workflow without loading these files into the runtime skill package

The runtime `.skill` package intentionally excludes `_sources/` so token usage stays low.

See `scripts/README.md` for the refresh workflow.
