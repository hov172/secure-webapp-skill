#!/usr/bin/env python3
"""Dependency-free validation for the secure-webapp skill package."""

from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


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


def check_required_paths(skill_name: str) -> None:
    required = [
        "SKILL.md",
        "license.txt",
        ".gitignore",
        "agents/openai.yaml",
        "assets/audit-checklist.md",
        "assets/secure-webapp-small.svg",
        "assets/secure-webapp-large.svg",
        "scripts/check_skill.py",
        "scripts/package_skill.py",
        "scripts/release_checksums.py",
        "scripts/refresh.py",
        "scripts/sync_references.py",
        "scripts/manifest.json",
        "scripts/README.md",
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
    ]
    for rel in required:
        if not (ROOT / rel).exists():
            fail(f"missing required path: {rel}")

    skill_text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    referenced = set(re.findall(r"`((?:references|assets|scripts)/[^`]+)`", skill_text))
    for rel in sorted(referenced):
        if not (ROOT / rel).exists():
            fail(f"SKILL.md references missing path: {rel}")
    for option in ("audit", "quick-check", "harden", "design-review", "maintain"):
        if f"$secure-webapp {option}" not in skill_text:
            fail(f"SKILL.md missing explicit invocation option: {option}")

    openai = (ROOT / "agents/openai.yaml").read_text(encoding="utf-8")
    if f"${skill_name}" not in openai:
        fail("agents/openai.yaml default prompt must mention the skill as $skill-name")
    if "allow_implicit_invocation: true" not in openai:
        fail("agents/openai.yaml should explicitly allow implicit invocation")
    for expected in (
        'icon_small: "./assets/secure-webapp-small.svg"',
        'icon_large: "./assets/secure-webapp-large.svg"',
        'brand_color: "#2563EB"',
    ):
        if expected not in openai:
            fail(f"agents/openai.yaml missing {expected}")


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
            if re.search(r"uses:\s+[^@\s]+@v\d", text):
                fail(f"{path.relative_to(ROOT)} should not pin actions by floating version tags")
    refresh_workflow = ROOT / ".github/workflows/refresh-owasp.yml"
    if refresh_workflow.exists():
        text = refresh_workflow.read_text(encoding="utf-8")
        for expected in (
            "cron: \"0 9 * * 1\"",
            "scripts/refresh.py --quiet",
            "scripts/sync_references.py",
            "scripts/package_skill.py",
            "scripts/release_checksums.py",
            "gh pr merge",
            "refresh/owasp-sources",
            "_sources/**",
            "references/**",
            "secure-webapp.skill",
            "SHA256SUMS",
            "deterministic reference updates",
        ):
            if expected not in text:
                fail(f"refresh workflow missing {expected}")
    release_workflow = ROOT / ".github/workflows/release.yml"
    if release_workflow.exists():
        text = release_workflow.read_text(encoding="utf-8")
        for expected in ("tags:", "scripts/package_skill.py", "scripts/release_checksums.py", "scripts/sync_references.py", "secure-webapp.skill", "SHA256SUMS"):
            if expected not in text:
                fail(f"release workflow missing {expected}")
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
        f"{prefix}license.txt",
        f"{prefix}agents/openai.yaml",
        f"{prefix}scripts/check_skill.py",
        f"{prefix}scripts/package_skill.py",
        f"{prefix}scripts/release_checksums.py",
        f"{prefix}scripts/refresh.py",
        f"{prefix}assets/audit-checklist.md",
        f"{prefix}assets/secure-webapp-small.svg",
        f"{prefix}assets/secure-webapp-large.svg",
    ):
        if needed not in names:
            fail(f"package missing {needed}")
    for name in names:
        if name.startswith(f"{prefix}_sources/"):
            fail("package must not include _sources maintenance cache")
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


def main() -> None:
    values = frontmatter()
    skill_name = values["name"]
    check_required_paths(skill_name)
    check_manifest()
    check_hygiene()
    check_package(skill_name)
    print(f"OK: {skill_name} skill validation passed")


if __name__ == "__main__":
    main()
