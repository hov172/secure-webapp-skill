#!/usr/bin/env python3
"""Dependency-free validation for the secure-webapp skill package."""

from __future__ import annotations

import json
import os
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The upstream cache is refreshed weekly. Anything older than this means the
# refresh pipeline is broken and nobody noticed — which is exactly what happened
# for five weeks in July 2026, so it is now a build failure, not a surprise.
MAX_SOURCE_AGE_DAYS = int(os.environ.get("SKILL_MAX_SOURCE_AGE_DAYS", "30"))


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def frontmatter() -> dict[str, str]:
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    if not match:
        fail("SKILL.md is missing YAML frontmatter")
    values: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    if not values.get("name"):
        fail("SKILL.md frontmatter is missing name")
    if not values.get("description"):
        fail("SKILL.md frontmatter is missing description")
    if len(values["description"].split()) > 120:
        fail("SKILL.md description should stay concise for trigger metadata")
    return values


def declared_modes(skill_name: str, skill_text: str) -> list[str]:
    """The invocation modes SKILL.md actually documents, in order.

    Derived rather than hardcoded: three copies of this list live in the
    installers, and a hardcoded fourth copy here is how `report`, `remediate`
    and `update` shipped without the validator ever noticing.
    """
    modes: list[str] = []
    for match in re.finditer(rf"^- `\${re.escape(skill_name)} ([a-z-]+)`", skill_text, re.M):
        if match.group(1) not in modes:
            modes.append(match.group(1))
    if not modes:
        fail("SKILL.md documents no `$secure-webapp <mode>` invocation options")
    return modes


def check_mode_consistency(skill_name: str, skill_text: str) -> None:
    """Every documented mode must be advertised everywhere users discover it."""
    modes = declared_modes(skill_name, skill_text)

    # The installers write a discovery block into AGENTS.md / GEMINI.md that
    # lists the modes. If SKILL.md gains a mode, those lists must gain it too.
    consumers = {
        "bin/install.js": (ROOT / "bin/install.js").read_text(encoding="utf-8"),
        "scripts/install.sh": (ROOT / "scripts/install.sh").read_text(encoding="utf-8"),
        "scripts/install.ps1": (ROOT / "scripts/install.ps1").read_text(encoding="utf-8"),
        "AGENTS.md": (ROOT / "AGENTS.md").read_text(encoding="utf-8"),
        "GEMINI.md": (ROOT / "GEMINI.md").read_text(encoding="utf-8"),
        "README.md": (ROOT / "README.md").read_text(encoding="utf-8"),
    }
    for name, text in consumers.items():
        for mode in modes:
            if mode not in text:
                fail(f"{name} does not mention the `${skill_name} {mode}` mode documented in SKILL.md")

    # Every mode that routes to an asset must have that asset present.
    for rel in re.findall(r"`(assets/[^`]+)`", skill_text):
        if not (ROOT / rel).exists():
            fail(f"SKILL.md routes to a missing asset: {rel}")


def check_required_paths(skill_name: str) -> None:
    required = [
        "SKILL.md",
        "AGENTS.md",
        "GEMINI.md",
        "VERSION",
        "LICENSE.txt",
        ".gitignore",
        "agents/openai.yaml",
        "agents/gemini.yaml",
        "agents/claude.yaml",
        "assets/audit-checklist.md",
        "assets/secure-webapp-small.svg",
        "assets/secure-webapp-large.svg",
        "assets/remediate-checklist.md",
        "assets/report-template.md",
        "scripts/check_skill.py",
        "scripts/package_skill.py",
        "scripts/release_checksums.py",
        "scripts/refresh.py",
        "scripts/eval_skill.py",
        "scripts/curate_references.py",
        "scripts/manifest.json",
        "scripts/reference_map.json",
        "tests/expectations.json",
        "tests/README.md",
        "scripts/README.md",
        "scripts/setup-auto-update.js",
        "scripts/install.ps1",
        ".github/workflows/validate.yml",
        ".github/workflows/refresh-owasp.yml",
        ".github/workflows/release.yml",
        ".github/dependabot.yml",
        "references/apis-and-files.md",
        "references/auth-and-sessions.md",
        "references/authorization.md",
        "references/data-and-crypto.md",
        "references/frontend-and-headers.md",
        "references/input-handling.md",
        "references/insecure-design.md",
        "references/logging-and-errors.md",
        "references/secrets-and-config.md",
        "references/secure-coding.md",
        "references/supply-chain.md",
        "references/tokens-and-oauth.md",
        "references/ai-and-llm.md",
    ]
    for rel in required:
        if not (ROOT / rel).exists():
            fail(f"missing required path: {rel}")

    skill_text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    referenced = set(re.findall(r"`((?:references|assets|scripts)/[^`]+)`", skill_text))
    for rel in sorted(referenced):
        if not (ROOT / rel).exists():
            fail(f"SKILL.md references missing path: {rel}")
    check_mode_consistency(skill_name, skill_text)

    for agent_manifest in ("agents/openai.yaml", "agents/gemini.yaml", "agents/claude.yaml"):
        manifest_text = (ROOT / agent_manifest).read_text(encoding="utf-8")
        if f"${skill_name}" not in manifest_text:
            fail(f"{agent_manifest} default prompt must mention the skill as $skill-name")
        if "allow_implicit_invocation: true" not in manifest_text:
            fail(f"{agent_manifest} should explicitly allow implicit invocation")
        for expected in (
            'icon_small: "./assets/secure-webapp-small.svg"',
            'icon_large: "./assets/secure-webapp-large.svg"',
            'brand_color: "#2563EB"',
        ):
            if expected not in manifest_text:
                fail(f"{agent_manifest} missing {expected}")

    for agent_doc in ("AGENTS.md", "GEMINI.md"):
        doc_text = (ROOT / agent_doc).read_text(encoding="utf-8")
        if skill_name not in doc_text:
            fail(f"{agent_doc} must name the {skill_name} skill")
        if f"${skill_name}" not in doc_text:
            fail(f"{agent_doc} should document the ${skill_name} invocation modes")

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not version:
        fail("VERSION file is empty")
    pkg_path = ROOT / "package.json"
    if pkg_path.exists():
        pkg_version = json.loads(pkg_path.read_text(encoding="utf-8")).get("version")
        if pkg_version != version:
            fail(f"package.json version ({pkg_version}) does not match VERSION ({version})")
    installer = (ROOT / "bin/install.js").read_text(encoding="utf-8")
    for token in (".codex", ".gemini", "VERSION", "--force", "--check"):
        if token not in installer:
            fail(f"bin/install.js missing platform/version handling: {token}")
    autoupdate = (ROOT / "scripts/setup-auto-update.js").read_text(encoding="utf-8")
    for token in ("darwin", "win32", "launchd", "schtasks", "--disable", "--check"):
        if token not in autoupdate:
            fail(f"scripts/setup-auto-update.js missing platform handling: {token}")


def check_manifest() -> None:
    manifest_path = ROOT / "scripts/manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"scripts/manifest.json is invalid JSON: {exc}")
    sources = manifest.get("sources") or {}
    for name in ("top10_2025", "asvs_5_0", "cheatsheets", "wstg_selected"):
        if name not in sources:
            fail(f"manifest missing source: {name}")
    for name, source in sources.items():
        if name.startswith("_"):
            continue
        for key in ("label", "repository_url", "base_url", "license", "license_url"):
            if key not in source:
                fail(f"manifest source {name} missing {key}")
        if not source.get("files"):
            fail(f"manifest source {name} has no files")


def check_source_freshness() -> None:
    """Fail if the upstream OWASP cache has gone stale.

    Skipped when _sources/ is absent — the release workflow deliberately removes
    it before packaging, and a fresh clone may not have refreshed yet.
    """
    state_path = ROOT / "_sources/_state.json"
    if not state_path.exists():
        return
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"_sources/_state.json is invalid JSON: {exc}")
    last_run = state.get("last_run")
    if not last_run:
        fail("_sources/_state.json has no last_run; run scripts/refresh.py")
    try:
        when = datetime.fromisoformat(last_run)
    except ValueError:
        fail(f"_sources/_state.json last_run is not an ISO timestamp: {last_run}")
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    age_days = (datetime.now(timezone.utc) - when).days
    if age_days > MAX_SOURCE_AGE_DAYS:
        fail(
            f"upstream OWASP cache is {age_days} days old (limit {MAX_SOURCE_AGE_DAYS}); "
            "the weekly refresh is not landing — run scripts/refresh.py and check "
            ".github/workflows/refresh-owasp.yml"
        )
    errors = state.get("fetch_errors") or []
    if errors:
        print(f"WARN: {len(errors)} upstream file(s) could not be fetched on the last refresh:")
        for err in errors:
            print(f"  - {err}")
        print("      Update scripts/manifest.json if a file was renamed upstream.")


def check_reference_map() -> None:
    """Every reference must be grounded in real, tracked upstream sources.

    An entry pointing at a file the manifest no longer fetches means curation
    would silently skip that reference forever.
    """
    map_path = ROOT / "scripts/reference_map.json"
    try:
        data = json.loads(map_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"scripts/reference_map.json is invalid JSON: {exc}")
    mapping = data.get("references") or {}
    if not mapping:
        fail("scripts/reference_map.json declares no references")

    manifest = json.loads((ROOT / "scripts/manifest.json").read_text(encoding="utf-8"))
    tracked = {
        f"{source}/{filename}"
        for source, definition in manifest.get("sources", {}).items()
        if not source.startswith("_")
        for filename in definition.get("files", [])
    }

    on_disk = {p.name for p in (ROOT / "references").glob("*.md")}
    for name in sorted(on_disk - set(mapping)):
        fail(f"references/{name} has no entry in scripts/reference_map.json")
    for name, sources in mapping.items():
        if not (ROOT / "references" / name).exists():
            fail(f"reference_map.json maps {name}, which does not exist in references/")
        if not sources:
            fail(f"reference_map.json maps {name} to no sources")
        for source in sources:
            if source not in tracked:
                fail(f"reference_map.json maps {name} to untracked source: {source}")


def check_hygiene() -> None:
    forbidden_names = {"__pycache__", ".package-build", ".skill-restore"}
    forbidden_suffixes = {".pyc", ".pyo"}
    for path in ROOT.rglob("*"):
        rel = path.relative_to(ROOT).as_posix()
        if any(part in forbidden_names for part in path.parts):
            fail(f"generated/local artifact present: {rel}")
        if path.suffix in forbidden_suffixes:
            fail(f"generated Python artifact present: {rel}")
    readme = ROOT / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        for expected in (
            "Install for Claude: all projects",
            "Install for Claude: one project",
            "Install for Codex: all projects",
            "Install for Codex: one project",
            "Install for Gemini CLI: all projects",
            "Install for Gemini CLI: one project",
            "Install for other AI agents",
            "Install on Windows",
            "Automatic Updates",
            "Verify installation",
        ):
            if expected not in text:
                fail(f"README.md missing installation section: {expected}")
    workflow = ROOT / ".github/workflows/validate.yml"
    if workflow.exists():
        text = workflow.read_text(encoding="utf-8")
        if "permissions:\n      contents: read" not in text:
            fail("validate workflow should use read-only contents permission")
        if "persist-credentials: false" not in text:
            fail("validate workflow checkout should disable persisted credentials")
    workflows = ROOT / ".github/workflows"
    if workflows.exists():
        for path in workflows.glob("*.yml"):
            text = path.read_text(encoding="utf-8")
            rel = path.relative_to(ROOT)
            if re.search(r"uses:\s+[^@\s]+@v\d", text):
                fail(f"{rel} should not pin actions by floating version tags")
            # Every third-party action must be pinned to a full commit SHA and
            # annotated with the release it corresponds to. Without the comment
            # Dependabot cannot tell which release you are on, so it follows the
            # action's default branch instead — which is how this repo briefly
            # ended up running an untagged upstream commit in CI.
            for line in text.splitlines():
                match = re.search(r"uses:\s+(\S+)", line)
                if not match:
                    continue
                ref = match.group(1)
                if "@" not in ref:
                    fail(f"{rel} has an unpinned action: {ref}")
                pin = ref.split("@", 1)[1]
                if not re.fullmatch(r"[0-9a-f]{40}", pin):
                    fail(f"{rel} must pin actions to a full 40-char commit SHA: {ref}")
                if not re.search(r"#\s*v\d+\.\d+\.\d+", line):
                    fail(
                        f"{rel} pin is missing its '# vX.Y.Z' release comment: {ref} "
                        "(without it Dependabot tracks the default branch, not releases)"
                    )
    refresh_workflow = ROOT / ".github/workflows/refresh-owasp.yml"
    if refresh_workflow.exists():
        text = refresh_workflow.read_text(encoding="utf-8")
        for expected in (
            "cron: \"0 9 * * 1\"",
            "scripts/refresh.py",
            "scripts/package_skill.py",
            "scripts/release_checksums.py",
            "refresh/owasp-sources",
            "_sources/**",
            "secure-webapp.skill",
            "SHA256SUMS",
            "gh issue",
        ):
            if expected not in text:
                fail(f"refresh workflow missing {expected}")
        # Upstream content must not reach a shipped artifact unreviewed. This is
        # the invariant that matters — not whether references/ is committed.
        if "gh pr merge" in text:
            fail("refresh workflow must not auto-merge; upstream changes need human review")
        add_paths = re.search(r"add-paths:\s*\|\n((?:\s{12}\S.*\n)+)", text)
        if not add_paths:
            fail("refresh workflow has no add-paths block")
        # references/ may be committed by the refresh only when the curation step
        # produced it. A workflow that commits references without curating them
        # is the old blind-sync failure mode returning.
        if "references/" in add_paths.group(1) and "scripts/curate_references.py" not in text:
            fail(
                "refresh workflow commits references/ without running "
                "scripts/curate_references.py; references must never be written blindly"
            )
    release_workflow = ROOT / ".github/workflows/release.yml"
    if release_workflow.exists():
        text = release_workflow.read_text(encoding="utf-8")
        for expected in (
            "tags:",
            "scripts/package_skill.py",
            "scripts/release_checksums.py",
            "scripts/eval_skill.py --check",
            "secure-webapp.skill",
            "SHA256SUMS",
        ):
            if expected not in text:
                fail(f"release workflow missing {expected}")
    agent_workflow = ROOT / ".github/workflows/curate-agent.yml"
    if agent_workflow.exists():
        text = agent_workflow.read_text(encoding="utf-8")
        # This workflow hands a model write access to the checkout. It is only
        # acceptable while it stays manual, bounded, and reviewed.
        if re.search(r"^\s*schedule:", text, re.M):
            fail("curate-agent workflow must stay manual (workflow_dispatch only), never scheduled")
        if "workflow_dispatch:" not in text:
            fail("curate-agent workflow must be triggered by workflow_dispatch")
        if "scripts/verify_agent_changes.py" not in text:
            fail("curate-agent workflow must verify the agent stayed within references/")
        if "gh pr merge" in text or "--auto" in text:
            fail("curate-agent workflow must not auto-merge; agent edits need human review")

    validate_workflow = ROOT / ".github/workflows/validate.yml"
    if validate_workflow.exists():
        text = validate_workflow.read_text(encoding="utf-8")
        if "scripts/eval_skill.py --check" not in text:
            fail("validate workflow must run the detection-corpus gate")
    # Installers must verify what they download; this is a security skill.
    for rel, needles in (
        ("scripts/install.sh", ("SHA256SUMS", "verify_checksum")),
        ("scripts/install.ps1", ("SHA256SUMS", "Get-FileHash")),
    ):
        text = (ROOT / rel).read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                fail(f"{rel} must verify the downloaded archive ({needle} missing)")
    dependabot = ROOT / ".github/dependabot.yml"
    if dependabot.exists():
        text = dependabot.read_text(encoding="utf-8")
        if 'package-ecosystem: "github-actions"' not in text:
            fail("dependabot should track GitHub Actions updates")


def check_package(skill_name: str) -> None:
    package = ROOT / f"{skill_name}.skill"
    if not package.exists():
        return
    try:
        with zipfile.ZipFile(package) as zf:
            names = set(zf.namelist())
    except zipfile.BadZipFile:
        fail(f"{package.name} is not a valid zip archive")
    prefix = f"{skill_name}/"
    for needed in (
        f"{prefix}SKILL.md",
        f"{prefix}AGENTS.md",
        f"{prefix}GEMINI.md",
        f"{prefix}VERSION",
        f"{prefix}LICENSE.txt",
        f"{prefix}agents/openai.yaml",
        f"{prefix}agents/gemini.yaml",
        f"{prefix}agents/claude.yaml",
        f"{prefix}scripts/check_skill.py",
        f"{prefix}scripts/package_skill.py",
        f"{prefix}scripts/release_checksums.py",
        f"{prefix}scripts/refresh.py",
        f"{prefix}scripts/setup-auto-update.js",
        f"{prefix}scripts/manifest.json",
        f"{prefix}scripts/reference_map.json",
        f"{prefix}assets/audit-checklist.md",
        f"{prefix}assets/remediate-checklist.md",
        f"{prefix}assets/report-template.md",
        f"{prefix}assets/secure-webapp-small.svg",
        f"{prefix}assets/secure-webapp-large.svg",
        f"{prefix}references/ai-and-llm.md",
        f"{prefix}LICENSE",
    ):
        if needed not in names:
            fail(f"package missing {needed}")

    # An npx install and a released archive must produce the same tree.
    installer = (ROOT / "bin/install.js").read_text(encoding="utf-8")
    for top_level in ("references", "assets", "agents", "scripts"):
        if f"'{top_level}'" not in installer:
            fail(f"bin/install.js does not copy {top_level}/; npx installs would diverge from the .skill archive")

    for name in names:
        if name.startswith(f"{prefix}_sources/"):
            fail("package must not include _sources maintenance cache")
        if name.startswith(f"{prefix}tests/"):
            fail("package must not include the detection corpus")
        if name.startswith(f"{prefix}bin/") or name in {
            f"{prefix}scripts/install.sh",
            f"{prefix}scripts/install.ps1",
        }:
            fail(f"package must not include installer-only file: {name}")
        if name == f"{prefix}README.md":
            fail("package must not include GitHub-facing README.md")
        if name == f"{prefix}.gitignore":
            fail("package must not include source-control-only .gitignore")
        if name == f"{prefix}scripts/README.md":
            fail("package must not include maintainer-only scripts/README.md")
        if name in {f"{prefix}SHA256SUMS", f"{prefix}SHA256SUMS.asc"}:
            fail("package must not include release checksum/signature files")
        if "__pycache__" in name or name.endswith((".pyc", ".pyo")):
            fail(f"package includes generated Python artifact: {name}")


def is_source_checkout() -> bool:
    """True in the repository, false in an installed copy of the skill.

    The package ships these scripts, but they validate a *source tree* — they
    need .github/, tests/, .gitignore and friends, none of which belong in a
    runtime install. Without this check the failure is an opaque
    "missing required path: .gitignore" for anyone who runs them from
    ~/.claude/skills/secure-webapp.
    """
    return (ROOT / ".github").is_dir()


def main() -> None:
    if not is_source_checkout():
        print(
            "SKIP: this validator runs against the source repository, not an "
            "installed copy.\n"
            "      Clone https://github.com/hov172/secure-webapp-skill and run it there."
        )
        return
    values = frontmatter()
    skill_name = values["name"]
    check_required_paths(skill_name)
    check_manifest()
    check_reference_map()
    check_source_freshness()
    check_hygiene()
    check_package(skill_name)
    print(f"OK: {skill_name} skill validation passed")


if __name__ == "__main__":
    main()
