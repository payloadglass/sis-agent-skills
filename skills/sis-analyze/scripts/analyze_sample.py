#!/usr/bin/env python3
"""Run default and deep SIS scans for one sample and compare raw reports."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import re
from pathlib import Path


def md_code(value: object) -> str:
    text = str(value).replace("\r", " ").replace("\n", " ")
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    fence = "`" * max(1, longest + 1)
    return f"{fence}{text}{fence}"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(binary: str, sample: Path, report: Path, deep: bool, prefix: Path) -> tuple[int, dict | None, str | None]:
    command = [binary, "scan", str(sample)]
    if deep:
        command.append("--deep")
    command += ["--emit", f"json={report}"]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    prefix.with_suffix(".stdout.log").write_text(result.stdout, encoding="utf-8")
    prefix.with_suffix(".stderr.log").write_text(result.stderr, encoding="utf-8")
    if not report.exists():
        return result.returncode, None, "report not produced"
    try:
        value = json.loads(report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return result.returncode, None, str(exc)
    return result.returncode, value if isinstance(value, dict) else None, None


def version(binary: str) -> str:
    result = subprocess.run([binary, "--version"], text=True, capture_output=True, check=False)
    return (result.stdout or result.stderr).strip()


def verdict(report: dict | None) -> dict:
    if not report:
        return {}
    value = report.get("verdict")
    return value if isinstance(value, dict) else {"label": value} if isinstance(value, str) else {}


def findings(report: dict | None) -> list[dict]:
    if not report or not isinstance(report.get("findings"), list):
        return []
    return [item for item in report["findings"] if isinstance(item, dict)]


def kinds(report: dict | None) -> set[str]:
    return {str(item.get("kind")) for item in findings(report) if item.get("kind")}


def coverage(report: dict | None) -> dict:
    value = report.get("analysis_coverage") if report else None
    return value if isinstance(value, dict) else {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("sample", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--sis-bin", default=os.environ.get("SIS_BIN", "sis"))
    args = parser.parse_args()

    sample = args.sample.resolve()
    if not sample.is_file():
        parser.error(f"sample is not a readable file: {sample}")
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)

    baseline_path = output / "baseline-report.json"
    deep_path = output / "deep-report.json"
    base_code, baseline, base_error = run(args.sis_bin, sample, baseline_path, False, output / "baseline")
    deep_code, deep, deep_error = run(args.sis_bin, sample, deep_path, True, output / "deep")

    base_kinds = kinds(baseline)
    deep_kinds = kinds(deep)
    bverdict, dverdict = verdict(baseline), verdict(deep)
    bcov, dcov = coverage(baseline), coverage(deep)
    result = {
        "sample": str(sample),
        "sha256": file_sha256(sample),
        "size": sample.stat().st_size,
        "sis_version": version(args.sis_bin),
        "baseline": {
            "exit_code": base_code,
            "error": base_error,
            "verdict": bverdict,
            "coverage_state": bcov.get("state"),
            "omissions": bcov.get("omissions", []),
            "finding_count": len(findings(baseline)),
            "distinct_finding_kind_count": len(base_kinds),
        },
        "deep": {
            "exit_code": deep_code,
            "error": deep_error,
            "verdict": dverdict,
            "coverage_state": dcov.get("state"),
            "omissions": dcov.get("omissions", []),
            "finding_count": len(findings(deep)),
            "distinct_finding_kind_count": len(deep_kinds),
        },
        "delta": {
            "verdict_changed": bverdict.get("label") != dverdict.get("label"),
            "score_delta": (dverdict.get("score") - bverdict.get("score")) if isinstance(dverdict.get("score"), (int, float)) and isinstance(bverdict.get("score"), (int, float)) else None,
            "finding_kinds_added": sorted(deep_kinds - base_kinds),
            "finding_kinds_removed": sorted(base_kinds - deep_kinds),
            "coverage_changed": bcov.get("state") != dcov.get("state") or bcov.get("omissions", []) != dcov.get("omissions", []),
        },
        "analyst_hypotheses": [],
        "recommended_actions": [],
    }
    if base_error or deep_error:
        result["recommended_actions"].append({"priority": "P1", "action": "Investigate the failed scan posture before drawing comparative conclusions."})
    if result["delta"]["verdict_changed"]:
        result["recommended_actions"].append({"priority": "P1", "action": "Trace the verdict change to coverage, evidence, correlation, or policy using the raw reports."})
    if not result["recommended_actions"]:
        result["recommended_actions"].append({"priority": "P2", "action": "Review material deep-only evidence and preserve both reports with the case."})
    (output / "analysis.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# SIS sample analysis",
        "",
        "## Sample identity",
        "",
        f"- Path: {md_code(sample)}",
        f"- SHA-256: {md_code(result['sha256'])}",
        f"- Size: {md_code(result['size'])} bytes",
        f"- SIS version: {md_code(result['sis_version'] or 'unknown')}",
        "",
        "## Baseline result",
        "",
        f"- Exit code: {md_code(base_code)}",
        f"- Verdict: {md_code(bverdict.get('label') or 'unknown')}",
        f"- Coverage: {md_code(bcov.get('state') or 'unknown')}",
        f"- Error: {md_code(base_error or 'none')}",
        "",
        "## Deep result",
        "",
        f"- Exit code: {md_code(deep_code)}",
        f"- Verdict: {md_code(dverdict.get('label') or 'unknown')}",
        f"- Coverage: {md_code(dcov.get('state') or 'unknown')}",
        f"- Error: {md_code(deep_error or 'none')}",
        "",
        "## Material deltas",
        "",
        f"- Verdict changed: {md_code(result['delta']['verdict_changed'])}",
        f"- Score delta: {md_code(result['delta']['score_delta'])}",
        f"- Added finding kinds: {md_code(', '.join(result['delta']['finding_kinds_added']) or 'none')}",
        f"- Removed finding kinds: {md_code(', '.join(result['delta']['finding_kinds_removed']) or 'none')}",
        f"- Coverage changed: {md_code(result['delta']['coverage_changed'])}",
        "",
        "## Analyst hypotheses",
        "",
        "- None generated automatically. Attribute deltas using evidence and provider/coverage telemetry.",
        "",
        "## Recommended actions",
        "",
    ]
    lines.extend(f"- {item['priority']}: {item['action']}" for item in result["recommended_actions"])
    (output / "analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0 if baseline is not None or deep is not None else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except OSError as exc:
        print(f"sis-analyze helper failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
