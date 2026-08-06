#!/usr/bin/env python3
"""
curate_references.py — propose reference edits from real upstream OWASP diffs.

This is the automation that replaced `sync_references.py`. The difference is
what it works from: the old script pattern-matched substrings in the cache and
emitted a fixed bullet list, so it never propagated an actual guidance change.
This one reads the *diff* of what moved upstream, hands it to a model along with
the current reference, and asks for a targeted edit — then puts the result in a
pull request for a human to review. Nothing it writes reaches a shipped artifact
unreviewed.

Run it after `refresh.py`, while the upstream changes are still uncommitted in
the working tree — that diff is the input.

    python3 scripts/refresh.py
    python3 scripts/curate_references.py --dry-run     # what would be curated
    ANTHROPIC_API_KEY=sk-... python3 scripts/curate_references.py

Without ANTHROPIC_API_KEY it reports what it would do and exits 0, so the
no-key refresh path keeps working exactly as before.

Guardrails, because this edits security guidance:
  - Only references whose mapped sources actually changed are considered.
  - Only files under references/ are ever written.
  - A proposal is rejected if it drops the title, collapses the file, guts the
    content, or reintroduces the old generated-section marker.
  - Every write is reported with a rationale for the reviewer.
  - Per-run caps on references touched and diff size sent.

Exit codes: 0 nothing to do / proposals written, 1 hard failure (bad config,
API error, unparseable response).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "_sources"
REFERENCES = ROOT / "references"
MAP_PATH = ROOT / "scripts/reference_map.json"

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-opus-5"

# Cost and blast-radius caps for one scheduled run.
MAX_REFERENCES_PER_RUN = int(os.environ.get("CURATION_MAX_REFERENCES", "4"))
MAX_DIFF_CHARS = int(os.environ.get("CURATION_MAX_DIFF_CHARS", "60000"))
MAX_TOKENS = 16000
TIMEOUT_SECONDS = 300

# A proposal that shrinks a reference below this fraction of its original length
# is treated as a truncation/refusal artifact, not an edit.
MIN_LENGTH_RATIO = 0.75

SYSTEM_PROMPT = """\
You maintain the curated reference files for `secure-webapp`, an OWASP-grounded \
security skill loaded by coding agents. Each reference is opinionated prose \
written for an engineer who is about to write or review code — not a summary of \
the standard, and not a list of requirement numbers.

You are given one reference file and the unified diff of the upstream OWASP \
material that grounds it. Decide whether the upstream change means the guidance \
in the reference is now wrong, incomplete, or outdated — and if so, make the \
smallest edit that fixes it.

Change the reference ONLY when the upstream diff represents a real shift in \
security guidance: a changed recommendation, a newly deprecated or newly \
preferred algorithm/parameter/API, a new attack class, a materially new \
defense. Do NOT edit for upstream typo fixes, link changes, formatting, \
reordering, wording that carries the same meaning, or new material that the \
reference already covers in its own words.

When you do edit:
- Preserve the file's voice, structure, heading levels, and level of detail.
- Keep it practical and code-first. Match the existing code-sample style.
- Do not add a changelog, a "recently updated" note, or attribution text.
- Do not cite OWASP requirement identifiers; this skill deliberately omits them.
- Do not add a machine-generated summary section of any kind.
- Keep the closing checklist in sync if the change affects it.
- Return the COMPLETE file, not a fragment or a diff.

Default to no change. A reference that stays accurate is the normal outcome, \
and an unnecessary edit costs a human a review for nothing."""

TOOL = {
    "name": "propose_reference_update",
    "description": "Report whether the reference needs an edit, and supply the full updated file if so.",
    "input_schema": {
        "type": "object",
        "properties": {
            "needs_update": {
                "type": "boolean",
                "description": "True only if the upstream diff represents a real shift in security guidance.",
            },
            "rationale": {
                "type": "string",
                "description": "One or two sentences a reviewer can check: what changed upstream, and what you changed (or why nothing changed).",
            },
            "updated_content": {
                "type": "string",
                "description": "The complete updated reference file. Required when needs_update is true; omit otherwise.",
            },
        },
        "required": ["needs_update", "rationale"],
    },
}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def load_map() -> dict[str, list[str]]:
    try:
        data = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing {MAP_PATH.relative_to(ROOT)}")
    except json.JSONDecodeError as exc:
        fail(f"{MAP_PATH.relative_to(ROOT)} is invalid JSON: {exc}")
    references = data.get("references")
    if not references:
        fail("reference_map.json declares no references")
    return references


def changed_sources() -> set[str]:
    """Upstream files modified in the working tree, as <source>/<file> paths.

    The refresh writes into _sources/ without committing, so git's view of the
    working tree is exactly 'what moved upstream this run'.
    """
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain", "--", "_sources"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        fail(f"could not read git status for _sources: {exc}")

    changed: set[str] = set()
    for line in out.splitlines():
        path = line[3:].strip().strip('"')
        # Renames appear as "old -> new"; take the destination.
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if not path.startswith("_sources/"):
            continue
        rel = path[len("_sources/") :]
        # Real sources always live at <source-name>/<file>. Top-level entries are
        # refresh.py's own bookkeeping (_state.json, CHANGES.md, CURATION.md).
        if "/" not in rel:
            continue
        changed.add(rel)
    return changed


def diff_for(paths: list[str]) -> str:
    args = ["git", "diff", "--unified=3", "--"] + [f"_sources/{p}" for p in paths]
    try:
        out = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        fail(f"could not diff sources: {exc}")
    if len(out) > MAX_DIFF_CHARS:
        out = out[:MAX_DIFF_CHARS] + "\n\n[diff truncated at the configured size cap]\n"
    return out


def call_model(model: str, api_key: str, reference_name: str, reference_text: str, diff: str) -> dict:
    prompt = (
        f"Reference file: `references/{reference_name}`\n\n"
        "=== CURRENT REFERENCE ===\n"
        f"{reference_text}\n"
        "=== END CURRENT REFERENCE ===\n\n"
        "=== UPSTREAM OWASP DIFF SINCE LAST REFRESH ===\n"
        f"{diff}\n"
        "=== END UPSTREAM DIFF ===\n\n"
        "Call propose_reference_update with your decision."
    )
    payload = json.dumps(
        {
            "model": model,
            "max_tokens": MAX_TOKENS,
            "system": SYSTEM_PROMPT,
            "tools": [TOOL],
            "tool_choice": {"type": "tool", "name": "propose_reference_update"},
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": API_VERSION,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        fail(f"API request failed ({exc.code}): {detail}")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        fail(f"API request failed: {exc}")

    for block in body.get("content", []):
        if block.get("type") == "tool_use" and block.get("name") == TOOL["name"]:
            return block.get("input", {})
    fail(f"model returned no {TOOL['name']} call for {reference_name}")
    return {}


def validate_proposal(original: str, proposed: str) -> str | None:
    """Reject proposals that look like truncation, refusal, or regression."""
    if not proposed.strip():
        return "proposed content is empty"
    original_title = original.lstrip().splitlines()[0]
    if not proposed.lstrip().startswith(original_title):
        return f"proposed content does not start with the original title ({original_title!r})"
    if len(proposed) < len(original) * MIN_LENGTH_RATIO:
        return (
            f"proposed content is {len(proposed)} chars vs {len(original)} original "
            f"(below the {MIN_LENGTH_RATIO:.0%} floor) — looks truncated"
        )
    if "OWASP source sync" in proposed:
        return "proposed content reintroduces the removed generated-section marker"
    if proposed == original:
        return "proposal is identical to the current file"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Propose reference edits from upstream OWASP diffs.")
    parser.add_argument("--dry-run", action="store_true", help="report what would be curated; call no API")
    parser.add_argument("--reference", metavar="NAME", help="curate only this reference (e.g. auth-and-sessions.md)")
    parser.add_argument("--model", default=os.environ.get("CURATION_MODEL", DEFAULT_MODEL))
    args = parser.parse_args()

    reference_map = load_map()
    changed = changed_sources()
    if not changed:
        print("No upstream source changes in the working tree; nothing to curate.")
        return 0

    candidates: list[tuple[str, list[str]]] = []
    for name, sources in reference_map.items():
        if args.reference and name != args.reference:
            continue
        hits = sorted(s for s in sources if s in changed)
        if hits:
            candidates.append((name, hits))

    unmapped = changed - {s for sources in reference_map.values() for s in sources}
    if unmapped:
        print(f"Note: {len(unmapped)} changed source(s) ground no reference: {', '.join(sorted(unmapped))}")

    if not candidates:
        print(f"{len(changed)} upstream file(s) changed, but none ground a curated reference.")
        return 0

    # Most-affected references first, so the cap keeps the highest-signal work.
    candidates.sort(key=lambda item: len(item[1]), reverse=True)
    if len(candidates) > MAX_REFERENCES_PER_RUN:
        dropped = [name for name, _ in candidates[MAX_REFERENCES_PER_RUN:]]
        print(
            f"Capping at {MAX_REFERENCES_PER_RUN} reference(s) this run; "
            f"not curated: {', '.join(dropped)}"
        )
        candidates = candidates[:MAX_REFERENCES_PER_RUN]

    print(f"{len(changed)} upstream file(s) changed; {len(candidates)} reference(s) in scope:")
    for name, hits in candidates:
        print(f"  - references/{name}  ({len(hits)} changed source(s))")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if args.dry_run or not api_key:
        reason = "--dry-run" if args.dry_run else "ANTHROPIC_API_KEY is not set"
        print(f"\nStopping before any model call ({reason}).")
        print("The refresh itself is unaffected; references simply stay as they are.")
        return 0

    updated: list[tuple[str, str]] = []
    unchanged: list[tuple[str, str]] = []
    rejected: list[tuple[str, str]] = []

    for name, hits in candidates:
        path = REFERENCES / name
        original = path.read_text(encoding="utf-8")
        print(f"\nCurating references/{name} against {len(hits)} changed source(s)...")
        result = call_model(args.model, api_key, name, original, diff_for(hits))
        rationale = str(result.get("rationale", "")).strip() or "(no rationale given)"

        if not result.get("needs_update"):
            print(f"  no change — {rationale}")
            unchanged.append((name, rationale))
            continue

        proposed = str(result.get("updated_content") or "")
        problem = validate_proposal(original, proposed)
        if problem:
            print(f"  REJECTED — {problem}")
            rejected.append((name, problem))
            continue

        if not proposed.endswith("\n"):
            proposed += "\n"
        path.write_text(proposed, encoding="utf-8")
        print(f"  updated — {rationale}")
        updated.append((name, rationale))

    print("\n=== Curation summary ===")
    print(f"updated: {len(updated)}  unchanged: {len(unchanged)}  rejected: {len(rejected)}")
    for name, rationale in updated:
        print(f"  [updated]  references/{name} — {rationale}")
    for name, problem in rejected:
        print(f"  [rejected] references/{name} — {problem}")

    # Written for the PR body so a reviewer sees the reasoning next to the diff.
    curation_report = ROOT / "_sources" / "CURATION.md"
    if not (updated or rejected) and curation_report.exists():
        curation_report.unlink()
        print("\nRemoved stale _sources/CURATION.md (nothing curated this run).")
    if updated or rejected:
        report = ["## Reference curation", ""]
        report.append(f"Model: `{args.model}`")
        report.append("")
        for name, rationale in updated:
            report.append(f"- **`references/{name}`** — {rationale}")
        for name, problem in rejected:
            report.append(f"- `references/{name}` — proposal **rejected** by a guardrail: {problem}")
        report.append("")
        report.append("Model-proposed edits grounded in the upstream diff. Review them as you would any PR.")
        (ROOT / "_sources" / "CURATION.md").write_text("\n".join(report) + "\n", encoding="utf-8")
        print("\nWrote _sources/CURATION.md for the pull request body.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
