#!/usr/bin/env python3
"""Build deterministic complete-pack and per-skill ZIP release assets."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = [
    "sis-scan",
    "sis-triage",
    "sis-analyze",
    "sis-corpus-index",
    "sis-corpus-hunt",
    "sis-corpus-evaluate",
]
EXCLUDED_PARTS = {"dist", "__pycache__", ".git"}
FIXED_TIME = (2020, 1, 1, 0, 0, 0)


def iter_files(base: Path):
    for path in sorted(base.rglob("*")):
        if not path.is_file() or any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        yield path


def add_file(zf: zipfile.ZipFile, source: Path, archive_name: str) -> None:
    info = zipfile.ZipInfo(archive_name, FIXED_TIME)
    mode = 0o755 if os.access(source, os.X_OK) else 0o644
    info.external_attr = (mode & 0xFFFF) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    zf.writestr(info, source.read_bytes())


def write_zip(destination: Path, base: Path, prefix: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for source in iter_files(base):
            relative = source.relative_to(base).as_posix()
            add_file(zf, source, f"{prefix}/{relative}" if prefix else relative)


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()

    subprocess.run([sys.executable, str(ROOT / "scripts/validate_pack.py")], check=True)
    output = args.output.resolve()
    if output.exists():
        shutil.rmtree(output)
    (output / "skills").mkdir(parents=True)

    pack_zip = output / f"sis-agent-skills-{args.version}.zip"
    write_zip(pack_zip, ROOT, "sis-agent-skills")

    assets = [pack_zip]
    for skill in SKILLS:
        destination = output / "skills" / f"{skill}-{args.version}.zip"
        write_zip(destination, ROOT / "skills" / skill, skill)
        assets.append(destination)

    sums = output / "SHA256SUMS"
    sums.write_text(
        "".join(f"{checksum(path)}  {path.relative_to(output).as_posix()}\n" for path in assets),
        encoding="utf-8",
    )
    print(f"built {len(assets)} ZIP assets in {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
