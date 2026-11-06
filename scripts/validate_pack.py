#!/usr/bin/env python3
"""Validate the SIS Agent Skills package using only the Python standard library."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "sis-scan",
    "sis-triage",
    "sis-analyze",
    "sis-query",
    "sis-corpus-index",
    "sis-corpus-hunt",
    "sis-corpus-evaluate",
}
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def fail(message: str) -> None:
    raise ValueError(message)


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail(f"{path}: missing YAML frontmatter")
    try:
        _, raw, body = text.split("---\n", 2)
    except ValueError as exc:
        fail(f"{path}: malformed YAML frontmatter: {exc}")
    meta: dict[str, str] = {}
    for line in raw.splitlines():
        if not line.strip() or line.startswith(" "):
            continue
        if ":" not in line:
            fail(f"{path}: malformed frontmatter line: {line!r}")
        key, value = line.split(":", 1)
        value = value.strip().strip('"').strip("'")
        meta[key.strip()] = value
    return meta, body


def validate_links(path: Path, body: str) -> None:
    for target in LINK_RE.findall(body):
        target = target.split("#", 1)[0]
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        resolved = (path.parent / target).resolve()
        try:
            resolved.relative_to(path.parent.parent.resolve())
        except ValueError:
            fail(f"{path}: link escapes the skill directory: {target}")
        if not resolved.exists():
            fail(f"{path}: missing linked file: {target}")


def main() -> int:
    skills_root = ROOT / "skills"
    actual = {p.name for p in skills_root.iterdir() if p.is_dir()}
    if actual != EXPECTED:
        fail(f"skill set mismatch: expected {sorted(EXPECTED)}, got {sorted(actual)}")

    for skill in sorted(EXPECTED):
        skill_dir = skills_root / skill
        entry = skill_dir / "SKILL.md"
        if not entry.is_file():
            fail(f"{skill}: missing SKILL.md")
        if (skill_dir / "SKILLS.md").exists():
            fail(f"{skill}: non-standard SKILLS.md present")
        meta, body = parse_frontmatter(entry)
        if meta.get("name") != skill:
            fail(f"{entry}: frontmatter name must equal directory name")
        if not NAME_RE.fullmatch(skill) or len(skill) > 64:
            fail(f"{entry}: invalid skill name")
        description = meta.get("description", "")
        if not description or len(description) > 1024:
            fail(f"{entry}: description must be 1..1024 characters")
        compatibility_text = meta.get("compatibility", "")
        if len(compatibility_text) > 500:
            fail(f"{entry}: compatibility must be at most 500 characters")
        if len(body.splitlines()) > 500:
            fail(f"{entry}: SKILL.md body exceeds the recommended 500-line limit")
        if not body.strip():
            fail(f"{entry}: empty skill body")
        validate_links(entry, body)
        scripts = skill_dir / "scripts"
        if scripts.exists():
            for script in scripts.iterdir():
                if script.is_file() and not os.access(script, os.X_OK):
                    fail(f"{script}: helper script is not executable")

    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    if set(manifest.get("skills", [])) != EXPECTED:
        fail("manifest.json does not list exactly the normalized skills")

    compatibility = json.loads((ROOT / "compatibility.json").read_text(encoding="utf-8"))
    if compatibility.get("runtime_option") != "cli-only":
        fail("compatibility.json must declare the CLI-only runtime option")
    if compatibility.get("pack_version") != manifest.get("version"):
        fail("manifest and compatibility pack versions differ")
    minimum = compatibility.get("sis", {}).get("minimum")
    if minimum != "0.6.6":
        fail("CLI pack must declare SIS 0.6.6 as its minimum supported version")

    marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
    plugins = marketplace.get("plugins", [])
    if len(plugins) != 1:
        fail("marketplace must expose one unambiguous SIS skill bundle")
    listed = {Path(p).name for p in plugins[0].get("skills", [])}
    if listed != EXPECTED:
        fail("marketplace skill list does not match the pack")
    plugin = plugins[0]
    if plugin.get("source") != "./" or plugin.get("strict") is not False:
        fail("marketplace must expose the repository root as a strict=false curated plugin")

    cases = json.loads((ROOT / "evals/trigger-cases.json").read_text(encoding="utf-8"))
    for skill in EXPECTED:
        outcomes = {case.get("should_trigger") for case in cases if case.get("skill") == skill}
        if outcomes != {True, False}:
            fail(f"{skill}: trigger evals require at least one positive and one negative case")

    workflow = ROOT / ".github/workflows/release.yml"
    if not workflow.is_file():
        fail("missing mirror-ready release workflow")
    for helper in ("build_release.py", "smoke_test.py", "validate_pack.py"):
        path = ROOT / "scripts" / helper
        if not path.is_file() or not os.access(path, os.X_OK):
            fail(f"missing executable pack helper: scripts/{helper}")

    print(f"validated {len(EXPECTED)} SIS Agent Skills")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
