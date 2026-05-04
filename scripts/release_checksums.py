#!/usr/bin/env python3
"""Generate release checksums and optionally GPG-sign them."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate SHA-256 checksums for release artifacts.")
    parser.add_argument("artifacts", nargs="*", help="Artifacts to checksum. Defaults to secure-webapp.skill.")
    parser.add_argument("--sign", action="store_true", help="GPG-sign the checksum file if gpg is available.")
    parser.add_argument("--output", default="SHA256SUMS", help="Checksum output filename.")
    args = parser.parse_args()

    artifacts = [ROOT / p for p in (args.artifacts or ["secure-webapp.skill"])]
    missing = [str(p) for p in artifacts if not p.exists()]
    if missing:
        sys.exit(f"Missing artifact(s): {', '.join(missing)}")

    lines = [f"{sha256(path)}  {path.name}" for path in artifacts]
    output = ROOT / args.output
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {output}")

    if args.sign:
        gpg = shutil.which("gpg")
        if not gpg:
            sys.exit("gpg not found; checksum file was written but not signed")
        subprocess.run([gpg, "--detach-sign", "--armor", str(output)], check=True)
        print(f"Wrote {output}.asc")


if __name__ == "__main__":
    main()
