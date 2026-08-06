#!/usr/bin/env python3
"""
verify_agent_changes.py — bound what an agent run is allowed to have changed.

`curate_references.py` is safe by construction: the model never touches the
filesystem, so "only references/ can change" is a property of the code. The
agent variant gives a model real write access, so that guarantee has to be
re-established after the fact — which is exactly what this does.

Run it after an agent-driven curation, before anything is committed or proposed:

    python3 scripts/verify_agent_changes.py
    python3 scripts/verify_agent_changes.py --allow references _sources

It fails if the working tree contains changes outside the allowlist, if nothing
changed at all, or if the repository no longer validates. On failure, nothing is
reverted automatically — the run is inspected by a human — but the workflow that
calls this will not open a pull request.

Exit codes: 0 changes are in bounds and the tree validates, 1 otherwise.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# What an agent curation run is legitimately allowed to touch. Everything else —
# workflows, scripts, the installers, the packaged archive, VERSION — is out of
# bounds, because a curation run has no business changing how the skill is built,
# validated, or shipped.
DEFAULT_ALLOWLIST = ("references/",)

# Paths that are never acceptable, even if someone widens the allowlist. These
# are the ones where a rogue edit would be both high impact and easy to miss in
# a large diff.
ALWAYS_FORBIDDEN = (
    ".github/",
    "scripts/",
    "bin/",
    "agents/",
    "package.json",
    "VERSION",
    "secure-webapp.skill",
    "SHA256SUMS",
    "SKILL.md",
)


def changed_paths() -> list[str]:
    """Every path git reports as modified, added, deleted, or untracked."""
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        sys.exit(f"FAIL: could not read git status: {exc}")

    paths: list[str] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip().strip('"')
        if " -> " in path:  # rename: judge the destination
            path = path.split(" -> ", 1)[1]
        paths.append(path)
    return sorted(paths)


def validates() -> bool:
    ok = True
    for script, label in (
        ("scripts/check_skill.py", "package validation"),
        ("scripts/eval_skill.py", "detection corpus"),
    ):
        args = [sys.executable, script]
        if script.endswith("eval_skill.py"):
            args.append("--check")
        result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
        detail = (result.stdout.strip() or result.stderr.strip()).splitlines()
        line = detail[-1] if detail else "no output"
        if result.returncode != 0:
            print(f"FAIL: {label}: {line}")
            ok = False
        else:
            print(f"  ok: {label}: {line}")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Bound what an agent run changed.")
    parser.add_argument(
        "--allow",
        nargs="*",
        default=list(DEFAULT_ALLOWLIST),
        help="path prefixes the run may touch (default: references/)",
    )
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="treat 'nothing changed' as success instead of failure",
    )
    args = parser.parse_args()

    allow = tuple(a if a.endswith("/") or "." in Path(a).name else a + "/" for a in args.allow)
    paths = changed_paths()

    if not paths:
        if args.allow_empty:
            print("OK: no changes (allowed).")
            return 0
        print("FAIL: the agent run changed nothing at all.")
        print("      Either there was no work to do, or the run did not do it.")
        return 1

    print(f"Agent run touched {len(paths)} path(s):")
    out_of_bounds: list[str] = []
    for path in paths:
        forbidden = any(path == f or path.startswith(f) for f in ALWAYS_FORBIDDEN)
        allowed = any(path.startswith(a) for a in allow) and not forbidden
        marker = "  ok " if allowed else "  ✗  "
        print(f"{marker} {path}")
        if not allowed:
            out_of_bounds.append(path)

    if out_of_bounds:
        print(f"\nFAIL: {len(out_of_bounds)} path(s) outside the allowlist {allow}.")
        print("      A curation run may not change how the skill is built, validated, or shipped.")
        return 1

    print("\nAll changes are within bounds. Validating the tree...")
    if not validates():
        return 1

    print("OK: agent changes are in bounds and the repository validates.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
