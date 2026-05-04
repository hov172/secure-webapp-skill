#!/usr/bin/env python3
"""Build the .skill archive from the current source tree."""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read_skill_name() -> str:
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    if not match:
        sys.exit("SKILL.md is missing frontmatter")
    for line in match.group(1).splitlines():
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    sys.exit("SKILL.md frontmatter is missing name")


def should_include(path: Path, package_name: str) -> bool:
    rel = path.relative_to(ROOT)
    parts = set(rel.parts)
    if path.is_dir():
        return False
    if parts & {"_sources", ".package-build", ".skill-restore", "__pycache__"}:
        return False
    if path.name in {package_name, ".DS_Store", "SHA256SUMS"}:
        return False
    if path.name.endswith((".asc", ".sig")):
        return False
    if path.suffix in {".pyc", ".pyo"}:
        return False
    if rel.as_posix() in {"scripts/README.md", "scripts/install.sh", "bin/install.js"}:
        return False
    allowed_roots = {"agents", "assets", "references", "scripts"}
    if rel.parts[0] in allowed_roots:
        return True
    return rel.as_posix() in {"SKILL.md", "license.txt"}


def main() -> None:
    skill_name = read_skill_name()
    package_name = f"{skill_name}.skill"
    package_path = ROOT / package_name
    if package_path.exists():
        package_path.unlink()
    with zipfile.ZipFile(package_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(ROOT.rglob("*")):
            if not should_include(path, package_name):
                continue
            rel = path.relative_to(ROOT)
            zf.write(path, f"{skill_name}/{rel.as_posix()}")
    print(f"Built {package_path}")


if __name__ == "__main__":
    main()
