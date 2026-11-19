#!/usr/bin/env python3
"""Assert that every command in compatibility.json's sis.tested_contract exists in a real sis.

For each entry the check reads, from the installed binary only:
  * the command path (`sis explain format ...`): each word must be listed as a
    subcommand by its parent's `--help` (the top level is `sis --help`);
  * every `--flag` the entry names must appear in that command's `--help`;
  * for `--flag a|b|c` every alternative must appear in that same help.

Placeholders (INPUT, PATH, [FILE], ...) and values are not checked. The binary comes
from --sis-bin or the SIS_BIN environment variable. Nothing is scanned: only `--help`
and `--version` are run. Exit 0 no drift, 1 drift found, 2 usage or unusable binary.
Standard library only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORD = re.compile(r"^[a-z][a-z0-9-]*$")
FLAG = re.compile(r"--[a-z][a-z0-9-]*")
FLAG_VALUES = re.compile(r"(--[a-z][a-z0-9-]*)\s+([A-Za-z0-9_-]+(?:\|[A-Za-z0-9_-]+)+)")


def help_text(binary: str, path: list[str]) -> str:
    result = subprocess.run([binary, *path, "--help"], text=True, capture_output=True, check=False, timeout=60)
    if result.returncode != 0:
        raise ValueError(f"`{' '.join(['sis', *path, '--help'])}` exited {result.returncode}: {result.stderr.strip()[:200]}")
    return result.stdout


def subcommands(text: str) -> set[str]:
    """Names listed under a `Commands:` heading of clap-style help."""
    names: set[str] = set()
    in_commands = False
    for line in text.splitlines():
        if line.strip() == "Commands:":
            in_commands = True
            continue
        if in_commands:
            if not line.strip():
                break
            match = re.match(r"^\s{2}([a-z][a-z0-9-]*)\b", line)
            if match:
                names.add(match.group(1))
    return names


def has_flag(text: str, flag: str) -> bool:
    return re.search(rf"(?<![\w-]){re.escape(flag)}(?![\w-])", text) is not None


def has_word(text: str, word: str) -> bool:
    return re.search(rf"(?<![\w-]){re.escape(word)}(?![\w-])", text) is not None


def split_entry(entry: str) -> tuple[list[str], str]:
    tokens = entry.split()
    if not tokens or tokens[0] != "sis":
        raise ValueError(f"tested_contract entry does not start with `sis`: {entry!r}")
    path: list[str] = []
    index = 1
    while index < len(tokens) and WORD.match(tokens[index]):
        path.append(tokens[index])
        index += 1
    return path, " ".join(tokens[index:])


def check_entry(binary: str, entry: str, cache: dict[tuple[str, ...], str]) -> list[str]:
    problems: list[str] = []
    path, rest = split_entry(entry)

    def cached(p: list[str]) -> str:
        key = tuple(p)
        if key not in cache:
            cache[key] = help_text(binary, p)
        return cache[key]

    for depth, word in enumerate(path):
        parent = cached(path[:depth])
        if word not in subcommands(parent):
            problems.append(f"`{entry}`: `{' '.join(['sis', *path[:depth + 1]])}` is not a subcommand in `{' '.join(['sis', *path[:depth], '--help'])}`")
            return problems
    own_help = cached(path)
    # `--version` is printed by the top-level help as `-V, --version`.
    for flag in sorted(set(FLAG.findall(rest))):
        if not has_flag(own_help, flag):
            problems.append(f"`{entry}`: flag {flag} is not in `{' '.join(['sis', *path, '--help'])}`")
    for flag, values in FLAG_VALUES.findall(rest):
        for value in values.split("|"):
            if not has_word(own_help, value):
                problems.append(f"`{entry}`: value `{value}` for {flag} is not in `{' '.join(['sis', *path, '--help'])}`")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sis-bin", default=os.environ.get("SIS_BIN"),
                        help="path to the sis binary (default: $SIS_BIN)")
    parser.add_argument("--compat", type=Path, default=ROOT / "compatibility.json")
    args = parser.parse_args()
    if not args.sis_bin:
        print("SIS_BIN is not set and --sis-bin was not given; drift check not run.", file=sys.stderr)
        return 2

    compat = json.loads(args.compat.read_text(encoding="utf-8"))
    entries = compat.get("sis", {}).get("tested_contract")
    if not isinstance(entries, list) or not entries:
        print(f"{args.compat}: sis.tested_contract is missing or empty", file=sys.stderr)
        return 2

    try:
        version = subprocess.run([args.sis_bin, "--version"], text=True, capture_output=True, check=False, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"cannot run {args.sis_bin}: {exc}", file=sys.stderr)
        return 2
    print(f"checking {len(entries)} contract entries against: {(version.stdout or version.stderr).strip()}")

    problems: list[str] = []
    cache: dict[tuple[str, ...], str] = {}
    for entry in entries:
        try:
            problems += check_entry(args.sis_bin, entry, cache)
        except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
            problems.append(f"`{entry}`: {exc}")
    for problem in problems:
        print(f"DRIFT: {problem}", file=sys.stderr)
    if problems:
        print(f"{len(problems)} drift problem(s) in tested_contract", file=sys.stderr)
        return 1
    print("no drift: every tested_contract command and flag is present in the installed sis")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
