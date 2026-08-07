#!/usr/bin/env python3
"""Run a SIS directory scan and emit a conservative corpus evaluation bundle."""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
import subprocess
import re
import sys
from pathlib import Path


def md_code(value: object) -> str:
    text = str(value).replace("\r", " ").replace("\n", " ")
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    fence = "`" * max(1, longest + 1)
    return f"{fence}{text}{fence}"


def sis_version(binary: str) -> str:
    result = subprocess.run([binary, "--version"], text=True, capture_output=True, check=False)
    return (result.stdout or result.stderr).strip()


def entry_key(entry: dict) -> str | None:
    return entry.get("sha256") or entry.get("path") or entry.get("input") or entry.get("filename")


def entry_verdict(entry: dict):
    value = entry.get("verdict")
    if isinstance(value, dict):
        return value.get("label"), value.get("score")
    return entry.get("verdict_label") or (value if isinstance(value, str) else None), entry.get("score")


def entry_findings(entry: dict) -> set[str]:
    report = entry.get("report") if isinstance(entry.get("report"), dict) else entry
    findings = report.get("findings", []) if isinstance(report, dict) else []
    return {str(item.get("kind")) for item in findings if isinstance(item, dict) and item.get("kind")}


def entry_coverage(entry: dict):
    report = entry.get("report") if isinstance(entry.get("report"), dict) else entry
    value = report.get("analysis_coverage") if isinstance(report, dict) else None
    return value if isinstance(value, dict) else {}


def entries(report: dict) -> list[dict]:
    value = report.get("entries")
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def compare(current: list[dict], baseline: list[dict]) -> list[dict]:
    before = {entry_key(item): item for item in baseline if entry_key(item)}
    regressions = []
    for item in current:
        key = entry_key(item)
        if not key or key not in before:
            continue
        old = before[key]
        old_label, old_score = entry_verdict(old)
        new_label, new_score = entry_verdict(item)
        old_kinds, new_kinds = entry_findings(old), entry_findings(item)
        old_cov, new_cov = entry_coverage(old), entry_coverage(item)
        if old_label != new_label or old_kinds != new_kinds or old_cov != new_cov:
            regressions.append({
                "key": key,
                "old_verdict": old_label,
                "new_verdict": new_label,
                "score_delta": (new_score - old_score) if isinstance(new_score, (int, float)) and isinstance(old_score, (int, float)) else None,
                "finding_kinds_added": sorted(new_kinds - old_kinds),
                "finding_kinds_removed": sorted(old_kinds - new_kinds),
                "coverage_changed": old_cov != new_cov,
                "classification": "candidate",
            })
    return regressions


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus", type=Path)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--deep", action="store_true")
    parser.add_argument("--sis-bin", default=os.environ.get("SIS_BIN", "sis"))
    args = parser.parse_args()

    corpus = args.corpus.resolve()
    if not corpus.is_dir():
        parser.error(f"corpus is not a directory: {corpus}")
    run_id = args.run_id or dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = (args.output_root / run_id).resolve()
    if output == corpus or corpus in output.parents:
        parser.error("output must be outside the corpus directory")
    output.mkdir(parents=True, exist_ok=False)

    batch_path = output / "batch-report.json"
    command = [args.sis_bin, "scan", str(corpus)]
    if args.deep:
        command.append("--deep")
    command += ["--emit", f"json={batch_path}"]
    started = dt.datetime.now(dt.timezone.utc)
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    finished = dt.datetime.now(dt.timezone.utc)
    (output / "sis.stdout.log").write_text(result.stdout, encoding="utf-8")
    (output / "sis.stderr.log").write_text(result.stderr, encoding="utf-8")

    report = {}
    report_error = None
    if batch_path.exists():
        try:
            loaded = json.loads(batch_path.read_text(encoding="utf-8"))
            report = loaded if isinstance(loaded, dict) else {}
        except (OSError, json.JSONDecodeError) as exc:
            report_error = str(exc)
    else:
        report_error = "batch report not produced"

    current_entries = entries(report)
    distribution = collections.Counter(entry_verdict(item)[0] or "unknown" for item in current_entries)
    errors = []
    for item in current_entries:
        status = str(item.get("status", "")).lower()
        if item.get("error") or status in {"error", "failed", "parse_failed"}:
            errors.append({"key": entry_key(item), "status": item.get("status"), "error": item.get("error")})
    if report_error:
        errors.append({"key": None, "status": "report_error", "error": report_error})

    regressions = []
    baseline_path = args.baseline.resolve() if args.baseline else None
    if baseline_path:
        baseline_report = json.loads(baseline_path.read_text(encoding="utf-8"))
        regressions = compare(current_entries, entries(baseline_report if isinstance(baseline_report, dict) else {}))

    hotspots = []
    for item in current_entries:
        runtime = item.get("runtime_ms") or item.get("duration_ms")
        if isinstance(runtime, (int, float)):
            hotspots.append({"key": entry_key(item), "runtime_ms": runtime})
    hotspots.sort(key=lambda item: item["runtime_ms"], reverse=True)
    hotspots = hotspots[:20]

    candidates = []
    for item in current_entries:
        label, _ = entry_verdict(item)
        if str(label).lower() in {"suspicious", "malicious"}:
            candidates.append({"key": entry_key(item), "verdict": label, "finding_kinds": sorted(entry_findings(item))})

    summary = {
        "run_id": run_id,
        "timestamp_utc": finished.isoformat(),
        "started_utc": started.isoformat(),
        "sis_version": sis_version(args.sis_bin),
        "corpus_path": str(corpus),
        "mode": "deep" if args.deep else "default",
        "command": command,
        "exit_code": result.returncode,
        "report_error": report_error,
        "files_scanned": len(current_entries),
        "files_failed": len(errors),
        "verdict_distribution": dict(sorted(distribution.items())),
        "runtime_hotspots": len(hotspots),
        "regression_count": len(regressions),
        "candidate_count": len(candidates),
        "baseline": str(baseline_path) if baseline_path else None,
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (output / "hotspots.json").write_text(json.dumps(hotspots, indent=2) + "\n", encoding="utf-8")
    (output / "errors.json").write_text(json.dumps(errors, indent=2) + "\n", encoding="utf-8")
    (output / "regressions.json").write_text(json.dumps(regressions, indent=2) + "\n", encoding="utf-8")

    candidate_lines = ["# Case-study candidates", "", "These are review candidates, not established ground truth.", ""]
    if candidates:
        for item in candidates[:50]:
            candidate_lines.append(f"- {md_code(item['key'] or 'unknown')} — {md_code(item['verdict'])} — kinds: {md_code(', '.join(item['finding_kinds']) or 'none exposed')}")
    else:
        candidate_lines.append("- No suspicious or malicious entries were available in the parsed batch entries.")
    (output / "case-study-candidates.md").write_text("\n".join(candidate_lines) + "\n", encoding="utf-8")

    lines = [
        "# SIS corpus evaluation",
        "",
        f"- Run ID: {md_code(run_id)}",
        f"- Corpus: {md_code(corpus)}",
        f"- SIS version: {md_code(summary['sis_version'] or 'unknown')}",
        f"- Mode: {md_code(summary['mode'])}",
        f"- Exit code: {md_code(result.returncode)}",
        f"- Parsed entries: {md_code(len(current_entries))}",
        f"- Recorded errors: {md_code(len(errors))}",
        f"- Regression candidates: {md_code(len(regressions))}",
        f"- Case-study candidates: {md_code(len(candidates))}",
        "",
        "## Verdict distribution",
        "",
    ]
    lines.extend(f"- {md_code(label)}: {md_code(count)}" for label, count in sorted(distribution.items()))
    lines += [
        "",
        "## Constraints",
        "",
        "- Corpus membership and verdict distribution are not sufficient ground truth.",
        "- Regression entries are candidates until run identity, coverage, and oracle authority are reviewed.",
    ]
    if report_error:
        lines.append(f"- Batch report constraint: {md_code(report_error)}")
    (output / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    return 0 if batch_path.exists() and not report_error else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"sis-corpus-evaluate helper failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
