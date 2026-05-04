#!/usr/bin/env python3
"""
refresh.py — pull upstream OWASP source material for the secure-webapp skill.

What this does:
  1. Reads scripts/manifest.json (the list of upstream files to track).
  2. Downloads each file into _sources/<source-name>/<filename>.
  3. Compares against the previously stored copy and writes _sources/CHANGES.md
     listing what changed since the last run.
  4. Updates _sources/_state.json with current content hashes.

What this does NOT do:
  - It does NOT auto-rewrite the reference files in references/.
    The references are curated and opinionated — mechanical regeneration would
    lose what makes the skill useful. Instead, after running this script:
      * Open _sources/CHANGES.md to see what's changed upstream.
      * Decide which changes warrant updating which references.
      * Make those updates by hand, or paste CHANGES.md to Claude and ask for help.

Usage:
    python scripts/refresh.py             # standard refresh
    python scripts/refresh.py --quiet     # minimal output
    python scripts/refresh.py --dry-run   # show what would be fetched, fetch nothing
    python scripts/refresh.py --offline   # use cached _sources/ only, regenerate CHANGES from disk

Exits 0 on success, non-zero on network errors or manifest problems.

Recommended cadence: quarterly, or on demand when OWASP announces a major release
(new Top 10 edition, new ASVS version, etc.).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
SOURCES_DIR = REPO_ROOT / "_sources"
MANIFEST_PATH = SCRIPTS_DIR / "manifest.json"
STATE_PATH = SOURCES_DIR / "_state.json"
CHANGES_PATH = SOURCES_DIR / "CHANGES.md"

USER_AGENT = "secure-webapp-skill-refresh/1.0 (+https://github.com/OWASP)"
TIMEOUT_SECONDS = 30
RETRY_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 2


def log(msg: str, *, quiet: bool = False) -> None:
    if not quiet:
        print(msg, flush=True)


def sha256_of(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        sys.exit(f"❌ Manifest not found at {MANIFEST_PATH}")
    try:
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"❌ Manifest is not valid JSON: {e}")


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {"sources": {}, "last_run": None}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        # Corrupted state - treat as empty, will regenerate
        return {"sources": {}, "last_run": None}


def save_state(state: dict) -> None:
    SOURCES_DIR.mkdir(exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def fetch_url(url: str, *, timeout: int = TIMEOUT_SECONDS) -> str:
    """Fetch a URL with retries. Returns text content."""
    last_err: Exception | None = None
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status != 200:
                    raise urllib.error.HTTPError(
                        url, resp.status, f"HTTP {resp.status}", resp.headers, None
                    )
                charset = resp.headers.get_content_charset() or "utf-8"
                return resp.read().decode(charset, errors="replace")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
            last_err = e
            if attempt < RETRY_ATTEMPTS:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)
    raise RuntimeError(f"failed to fetch {url} after {RETRY_ATTEMPTS} attempts: {last_err}")


def diff_summary(old: str | None, new: str) -> str:
    """Cheap, human-readable summary of differences. Avoids a full unified diff
    (would balloon CHANGES.md); instead reports add/remove line counts and
    optionally a short snippet of headings that changed."""
    if old is None:
        return f"NEW (added: {new.count(chr(10)) + 1} lines)"
    if old == new:
        return "unchanged"
    old_lines = old.splitlines()
    new_lines = new.splitlines()
    added = len(set(new_lines) - set(old_lines))
    removed = len(set(old_lines) - set(new_lines))
    # Pick out new headings (lines starting with #) for a quick glimpse
    old_headings = {ln for ln in old_lines if ln.startswith("#")}
    new_headings = [ln for ln in new_lines if ln.startswith("#") and ln not in old_headings]
    summary = f"changed (+{added}/-{removed} unique lines)"
    if new_headings:
        snippet = "; ".join(new_headings[:3])
        if len(new_headings) > 3:
            snippet += f"; +{len(new_headings) - 3} more"
        summary += f" • new headings: {snippet}"
    return summary


def refresh(*, quiet: bool, dry_run: bool, offline: bool) -> int:
    manifest = load_manifest()
    state = load_state()
    new_state: dict = {"sources": {}, "last_run": datetime.now(timezone.utc).isoformat()}

    sources = manifest.get("sources", {})
    if not sources:
        sys.exit("❌ Manifest has no sources defined.")

    SOURCES_DIR.mkdir(exist_ok=True)

    # Per-source results, used to render CHANGES.md
    results: dict[str, dict] = {}
    network_errors: list[str] = []

    for source_name, source_def in sources.items():
        if source_name.startswith("_"):
            continue
        label = source_def.get("label", source_name)
        base_url = source_def["base_url"]
        repository_url = source_def.get("repository_url")
        files = source_def.get("files", [])
        log(f"\n📥 {label}", quiet=quiet)
        log(f"   {base_url}", quiet=quiet)
        log(f"   {len(files)} files", quiet=quiet)

        source_dir = SOURCES_DIR / source_name
        source_dir.mkdir(exist_ok=True)

        prev_files = state.get("sources", {}).get(source_name, {}).get("files", {})
        new_files: dict[str, dict] = {}
        per_file_results: list[dict] = []

        for filename in files:
            url = base_url + filename
            local_path = source_dir / filename
            old_text: str | None = None
            if local_path.exists():
                try:
                    old_text = local_path.read_text(encoding="utf-8")
                except Exception:
                    old_text = None

            if dry_run:
                log(f"   [dry-run] would fetch {url}", quiet=quiet)
                continue

            if offline:
                if old_text is None:
                    per_file_results.append({"filename": filename, "summary": "missing (offline)"})
                else:
                    new_files[filename] = {"sha256": sha256_of(old_text)}
                    per_file_results.append({"filename": filename, "summary": "cached only"})
                continue

            try:
                new_text = fetch_url(url)
            except Exception as e:
                msg = f"⚠️  {filename}: {e}"
                log(f"   {msg}", quiet=quiet)
                network_errors.append(f"{source_name}/{filename}: {e}")
                # Keep prior content (if any) in state so next run can still diff
                if filename in prev_files:
                    new_files[filename] = prev_files[filename]
                per_file_results.append({"filename": filename, "summary": "fetch failed (kept cached)"})
                continue

            new_hash = sha256_of(new_text)
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_text(new_text, encoding="utf-8")
            new_files[filename] = {"sha256": new_hash}

            old_hash = prev_files.get(filename, {}).get("sha256")
            if old_hash == new_hash:
                summary = "unchanged"
            else:
                summary = diff_summary(old_text, new_text)
            per_file_results.append({"filename": filename, "summary": summary})
            log(f"   ✓ {filename} — {summary}", quiet=quiet)

        new_state["sources"][source_name] = {
            "label": label,
            "repository_url": repository_url,
            "base_url": base_url,
            "files": new_files,
        }
        results[source_name] = {
            "label": label,
            "repository_url": repository_url,
            "files": per_file_results,
        }

    # Write CHANGES.md
    if not dry_run:
        write_changes_md(results, network_errors, prev_run=state.get("last_run"))
        save_state(new_state)
        log(f"\n📝 Wrote {CHANGES_PATH.relative_to(REPO_ROOT)}", quiet=quiet)
        log(f"💾 Updated {STATE_PATH.relative_to(REPO_ROOT)}", quiet=quiet)

    if network_errors:
        log(f"\n⚠️  {len(network_errors)} fetch error(s). See CHANGES.md for details.", quiet=quiet)
        return 1
    log("\n✅ Refresh complete.", quiet=quiet)
    log("   Review _sources/CHANGES.md, then update references/ as needed.", quiet=quiet)
    return 0


def write_changes_md(results: dict, network_errors: list[str], prev_run: str | None) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = []
    lines.append(f"# Upstream Source Changes")
    lines.append("")
    lines.append(f"Last refreshed: **{now}**")
    if prev_run:
        lines.append(f"Previous refresh: {prev_run}")
    lines.append("")
    lines.append("This file is auto-generated by `scripts/refresh.py`. It summarizes what")
    lines.append("changed in upstream OWASP source material since the last refresh. Use it")
    lines.append("to decide which reference files in `references/` need updating.")
    lines.append("")
    lines.append("**Triage rules of thumb:**")
    lines.append("- *unchanged* → no action needed.")
    lines.append("- *changed (small)* → skim the file in `_sources/`, decide if guidance shifted.")
    lines.append("- *changed (large)* or *new headings* → likely worth a closer look.")
    lines.append("- *NEW* → a previously untracked file; if relevant, integrate it.")
    lines.append("")

    if network_errors:
        lines.append("## ⚠️ Fetch errors")
        lines.append("")
        lines.append("These files could not be fetched this run. Cached content (if any) was kept.")
        lines.append("")
        for err in network_errors:
            lines.append(f"- `{err}`")
        lines.append("")

    lines.append("## Changes by source")
    lines.append("")
    for source_name, info in results.items():
        lines.append(f"### {info['label']}")
        if info.get("repository_url"):
            lines.append("")
            lines.append(f"Repository: {info['repository_url']}")
        lines.append("")
        any_changes = False
        for entry in info["files"]:
            summary = entry["summary"]
            if summary == "unchanged":
                continue
            any_changes = True
            lines.append(f"- `{entry['filename']}` — {summary}")
        if not any_changes:
            lines.append("_No changes since last refresh._")
        lines.append("")

    CHANGES_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh upstream OWASP source material.")
    parser.add_argument("--quiet", action="store_true", help="minimal output")
    parser.add_argument("--dry-run", action="store_true", help="show what would happen, fetch nothing")
    parser.add_argument("--offline", action="store_true", help="use cached files; regenerate CHANGES from disk")
    args = parser.parse_args()
    if args.dry_run and args.offline:
        sys.exit("❌ --dry-run and --offline are mutually exclusive.")
    sys.exit(refresh(quiet=args.quiet, dry_run=args.dry_run, offline=args.offline))


if __name__ == "__main__":
    main()
