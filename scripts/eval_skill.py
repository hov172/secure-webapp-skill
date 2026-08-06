#!/usr/bin/env python3
"""
eval_skill.py — does the skill still catch what it claims to catch?

check_skill.py validates the package's *shape* (files present, strings present).
This validates its *effect*: every Always-On Watchlist item in SKILL.md has a
deliberately vulnerable fixture in tests/fixtures/, and an agent's audit of that
corpus can be graded for recall.

Modes:
    --check            structural gate, no model required (this is what CI runs):
                       every watchlist item has a fixture, every fixture is
                       declared, every declared file exists, fixtures parse.
    --prompt           print the audit prompt to hand to the agent under test.
    --grade FILE.json  grade an agent's findings against tests/expectations.json.

Grading input format (a JSON list; anything extra is ignored):
    [{"file": "w01_idor_order_route.js", "severity": "high",
      "title": "...", "detail": "..."}, ...]

Exit codes: 0 pass, 1 fail.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"
EXPECTATIONS = ROOT / "tests" / "expectations.json"
SKILL = ROOT / "SKILL.md"

SEVERITY_ORDER = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}

problems: list[str] = []


def problem(message: str) -> None:
    problems.append(message)


def load_expectations() -> list[dict]:
    try:
        data = json.loads(EXPECTATIONS.read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"FAIL: missing {EXPECTATIONS.relative_to(ROOT)}")
    except json.JSONDecodeError as exc:
        sys.exit(f"FAIL: {EXPECTATIONS.relative_to(ROOT)} is invalid JSON: {exc}")
    fixtures = data.get("fixtures")
    if not fixtures:
        sys.exit("FAIL: expectations.json declares no fixtures")
    return fixtures


def watchlist_items() -> dict[int, str]:
    """Parse the numbered Always-On Watchlist out of SKILL.md."""
    text = SKILL.read_text(encoding="utf-8")
    match = re.search(r"^## Always-On Watchlist\n(.*?)(?=^## )", text, re.S | re.M)
    if not match:
        sys.exit("FAIL: SKILL.md has no '## Always-On Watchlist' section")
    items: dict[int, str] = {}
    for line in match.group(1).splitlines():
        entry = re.match(r"^(\d+)\.\s+(.*)$", line)
        if entry:
            items[int(entry.group(1))] = entry.group(2).strip()
    if not items:
        sys.exit("FAIL: SKILL.md watchlist has no numbered items")
    return items


# Fixtures must look insecure to a reviewer without looking like a real
# credential to a secret scanner. A realistic provider key format here gets the
# repository blocked by GitHub push protection — and lands in every fork.
SCANNER_BAIT = (
    ("sk_live_", "Stripe live secret key prefix"),
    ("sk_test_", "Stripe test secret key prefix"),
    ("ghp_", "GitHub personal access token prefix"),
    ("github_pat_", "GitHub fine-grained PAT prefix"),
    ("xoxb-", "Slack bot token prefix"),
    ("xoxp-", "Slack user token prefix"),
    ("AKIA", "AWS access key id prefix"),
    ("ASIA", "AWS temporary access key id prefix"),
    ("AIza", "Google API key prefix"),
    ("-----BEGIN RSA PRIVATE KEY-----", "PEM private key block"),
    ("-----BEGIN OPENSSH PRIVATE KEY-----", "OpenSSH private key block"),
)


def scanner_bait(text: str) -> str | None:
    for needle, label in SCANNER_BAIT:
        if needle in text:
            return (
                f"contains a {label} ({needle!r}); use an obvious placeholder instead "
                "so secret scanners do not flag the repository"
            )
    return None


def parses_cleanly(path: Path) -> str | None:
    """Syntax-check a fixture without emitting bytecode next to it."""
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".py":
        try:
            compile(text, str(path), "exec")
        except SyntaxError as exc:
            return f"python syntax error: {exc}"
    elif path.suffix == ".json":
        try:
            json.loads(text)
        except json.JSONDecodeError as exc:
            return f"json parse error: {exc}"
    if not text.strip():
        return "fixture is empty"
    return None


def run_check() -> int:
    # The detection corpus lives in the repository, not in a runtime install.
    if not FIXTURES.is_dir():
        print(
            "SKIP: the detection corpus ships with the source repository, not an "
            "installed copy.\n"
            "      Clone https://github.com/hov172/secure-webapp-skill and run it there."
        )
        return 0
    fixtures = load_expectations()
    watchlist = watchlist_items()

    declared_files = {f["file"] for f in fixtures}
    covered = {f.get("watchlist") for f in fixtures}

    # 1. Every watchlist item is exercised by at least one fixture.
    for number, title in sorted(watchlist.items()):
        if number not in covered:
            problem(f"watchlist item {number} has no fixture: {title[:70]}")

    # 2. No fixture claims a watchlist item that no longer exists.
    for number in sorted(n for n in covered if n is not None):
        if number not in watchlist:
            problem(f"expectations reference watchlist item {number}, which SKILL.md no longer has")

    # 3. Declared fixtures exist, parse, and carry usable expectations.
    for entry in fixtures:
        path = FIXTURES / entry["file"]
        if not path.exists():
            problem(f"declared fixture is missing on disk: tests/fixtures/{entry['file']}")
            continue
        err = parses_cleanly(path)
        if err:
            problem(f"tests/fixtures/{entry['file']}: {err}")
        bait = scanner_bait(path.read_text(encoding="utf-8"))
        if bait:
            problem(f"tests/fixtures/{entry['file']}: {bait}")
        if not entry.get("must_mention"):
            problem(f"tests/fixtures/{entry['file']}: expectations list no must_mention terms")
        sev = str(entry.get("min_severity", "")).lower()
        if sev not in SEVERITY_ORDER:
            problem(f"tests/fixtures/{entry['file']}: min_severity '{sev}' is not a known severity")

    # 4. No orphan fixtures sitting on disk undeclared.
    on_disk = {p.name for p in FIXTURES.glob("*") if p.is_file() and p.name != ".gitkeep"}
    for name in sorted(on_disk - declared_files):
        problem(f"tests/fixtures/{name} exists but is not declared in expectations.json")

    if problems:
        print("FAIL: detection corpus is out of sync with SKILL.md")
        for item in problems:
            print(f"  - {item}")
        return 1

    print(
        f"OK: detection corpus covers all {len(watchlist)} watchlist items "
        f"across {len(fixtures)} fixtures"
    )
    return 0


PROMPT = """\
Run `$secure-webapp audit` against every file in `tests/fixtures/`.

Treat each file as production code from a real web application. Report every
security finding you would normally report — do not assume a file is a test
fixture, and do not stop at one finding per file.

Return ONLY a JSON array, no prose, in this shape:

[
  {{"file": "<fixture filename>", "severity": "critical|high|medium|low|info",
   "title": "<short finding title>", "detail": "<evidence and fix>"}}
]

Then grade it:

    python3 scripts/eval_skill.py --grade findings.json

Fixtures ({count} files):
{files}
"""


def run_prompt() -> int:
    fixtures = load_expectations()
    listing = "\n".join(f"  - tests/fixtures/{f['file']}" for f in fixtures)
    print(PROMPT.format(count=len(fixtures), files=listing))
    return 0


def run_grade(results_path: Path) -> int:
    fixtures = load_expectations()
    try:
        findings = json.loads(results_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"FAIL: no such results file: {results_path}")
    except json.JSONDecodeError as exc:
        sys.exit(f"FAIL: results file is not valid JSON: {exc}")
    if not isinstance(findings, list):
        sys.exit("FAIL: results file must be a JSON array of findings")

    by_file: dict[str, list[dict]] = {}
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        # Tolerate full or partial paths in the reported filename.
        name = Path(str(finding.get("file", ""))).name
        by_file.setdefault(name, []).append(finding)

    detected = 0
    rows: list[tuple[str, str, str]] = []
    for entry in fixtures:
        name = entry["file"]
        floor = SEVERITY_ORDER[str(entry["min_severity"]).lower()]
        terms = [t.lower() for t in entry["must_mention"]]
        candidates = by_file.get(name, [])

        matched = None
        for finding in candidates:
            haystack = " ".join(
                str(finding.get(k, "")) for k in ("title", "detail", "description", "impact", "fix")
            ).lower()
            if not any(term in haystack for term in terms):
                continue
            sev = SEVERITY_ORDER.get(str(finding.get("severity", "")).lower(), -1)
            if sev < floor:
                matched = ("UNDER", f"reported {finding.get('severity')}, expected ≥ {entry['min_severity']}")
                continue
            matched = ("PASS", str(finding.get("title", ""))[:60])
            break

        if matched is None:
            status, note = ("MISS", "no matching finding" if candidates else "file not reported")
        else:
            status, note = matched
        if status == "PASS":
            detected += 1
        rows.append((status, name, note))

    total = len(fixtures)
    recall = detected / total if total else 0.0
    width = max(len(name) for _, name, _ in rows)
    print(f"{'':<6}{'fixture':<{width}}  note")
    for status, name, note in rows:
        print(f"{status:<6}{name:<{width}}  {note}")
    print(f"\nRecall: {detected}/{total} ({recall:.0%})")

    # A security skill that misses a watchlist item it advertises is a
    # regression, not a rounding error.
    if detected < total:
        print("FAIL: at least one advertised watchlist item was not detected")
        return 1
    print("OK: every advertised watchlist item was detected")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="structural corpus gate (no model needed)")
    group.add_argument("--prompt", action="store_true", help="print the audit prompt for the agent under test")
    group.add_argument("--grade", metavar="FILE", help="grade an agent's findings JSON")
    args = parser.parse_args()

    if args.check:
        sys.exit(run_check())
    if args.prompt:
        sys.exit(run_prompt())
    sys.exit(run_grade(Path(args.grade)))


if __name__ == "__main__":
    main()
