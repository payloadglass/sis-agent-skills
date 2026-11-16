#!/usr/bin/env python3
"""Run SIS once, preserve JSON/logs, and create a conservative summary."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def md_code(value: object) -> str:
    text = str(value).replace("\r", " ").replace("\n", " ")
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    fence = "`" * max(1, longest + 1)
    return f"{fence}{text}{fence}"


def get_version(binary: str) -> str:
    result = subprocess.run([binary, "--version"], text=True, capture_output=True, check=False)
    return (result.stdout or result.stderr).strip()


# sis 0.71 ranks labels in enum order; Anomalous (not fully examined) is below Suspicious.
LABEL_RANK = {"clean": 0, "anomalous": 1, "suspicious": 2, "malicious": 3}


def batch_entries(report: dict) -> list[dict]:
    """Directory scans emit a batch report: per-file `entries`, no top-level verdict."""
    value = report.get("entries")
    return [e for e in value if isinstance(e, dict)] if isinstance(value, list) else []


def coverage_summary(report: dict) -> tuple[str | None, list[dict]]:
    if "entries" in report:
        incomplete = []
        entries = batch_entries(report)
        for entry in entries:
            scope = entry.get("assurance_scope") if isinstance(entry.get("assurance_scope"), dict) else {}
            # Missing coverage data is unknown, not complete.
            if (entry.get("coverage_withheld") or scope.get("coverage") != "complete"
                    or not isinstance(entry.get("verdict_label"), str)):
                incomplete.append({
                    "path": entry.get("path"),
                    "coverage": scope.get("coverage"),
                    "coverage_withheld": bool(entry.get("coverage_withheld")),
                    "gaps": scope.get("gaps", []),
                })
        # Files that failed at batch level are in `errors`, not `entries`: never examined.
        errors = report.get("errors") if isinstance(report.get("errors"), list) else []
        for error in errors:
            incomplete.append({"path": error.get("path") if isinstance(error, dict) else None,
                               "coverage": "not examined", "error": error})
        if not entries and not errors:
            return "incomplete (batch report has no entries)", incomplete
        if not incomplete:
            return "complete", incomplete
        return f"incomplete ({len(incomplete) - len(errors)} of {len(entries)} entries partial; {len(errors)} failed)", incomplete
    coverage = report.get("analysis_coverage") or {}
    state = coverage.get("state") if isinstance(coverage, dict) else None
    omissions = coverage.get("omissions", []) if isinstance(coverage, dict) else []
    return state, omissions if isinstance(omissions, list) else []


def verdict_summary(report: dict) -> tuple[str | None, object, object]:
    if "entries" in report:
        # An entry without a string label is an unread verdict: report it as "unknown" (worst).
        labels = [e["verdict_label"] if isinstance(e.get("verdict_label"), str) else "unknown"
                  for e in batch_entries(report)]
        worst = max(labels, key=lambda l: LABEL_RANK.get(l.lower(), len(LABEL_RANK)))  # unknown label: worst, never hidden if labels else None
        return worst, None, None
    verdict = report.get("verdict")
    if isinstance(verdict, dict):
        return verdict.get("label"), verdict.get("score"), verdict.get("confidence")
    if isinstance(verdict, str):
        return verdict, None, None
    summary = report.get("summary")
    if isinstance(summary, dict):
        return summary.get("worst_verdict") or summary.get("verdict"), None, None
    return None, None, None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--deep", action="store_true")
    parser.add_argument("--fail-on", choices=("suspicious", "anomalous", "malicious"))
    parser.add_argument("--sis-bin", default=os.environ.get("SIS_BIN", "sis"))
    args = parser.parse_args()

    source = args.input.resolve()
    if not source.exists():
        parser.error(f"input does not exist: {source}")
    output = args.output_dir.resolve()
    if source.is_dir() and (output == source or source in output.parents):
        parser.error("output directory must not be inside the scanned directory")
    output.mkdir(parents=True, exist_ok=True)

    report_path = output / "report.json"
    command = [args.sis_bin, "scan", str(source)]
    if args.deep:
        command.append("--deep")
    command += ["--emit", f"json={report_path}"]
    if args.fail_on:
        command += ["--fail-on", args.fail_on]

    started = dt.datetime.now(dt.timezone.utc)
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    finished = dt.datetime.now(dt.timezone.utc)
    (output / "sis.stdout.log").write_text(result.stdout, encoding="utf-8")
    (output / "sis.stderr.log").write_text(result.stderr, encoding="utf-8")

    report = None
    parse_error = None
    if report_path.exists():
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            parse_error = str(exc)

    label = score = confidence = coverage_state = None
    omissions: list[dict] = []
    findings_count = None
    if isinstance(report, dict):
        label, score, confidence = verdict_summary(report)
        coverage_state, omissions = coverage_summary(report)
        findings = report.get("findings")
        if isinstance(findings, list):
            findings_count = len(findings)
        elif isinstance(report.get("summary"), dict):
            findings_count = report["summary"].get("total", report["summary"].get("findings_count"))

    summary = {
        "input": str(source),
        "input_type": "directory" if source.is_dir() else "file",
        "sha256": sha256(source),
        "sis_version": get_version(args.sis_bin),
        "mode": "deep" if args.deep else "default",
        "command": command,
        "started_utc": started.isoformat(),
        "finished_utc": finished.isoformat(),
        "exit_code": result.returncode,
        "gate_threshold": args.fail_on,
        "report_present": report_path.exists(),
        "report_parse_error": parse_error,
        "verdict": label,
        "score": score,
        "confidence": confidence,
        "coverage_state": coverage_state,
        "omission_count": len(omissions),
        "omissions": omissions,
        "findings_count": findings_count,
    }
    (output / "scan-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# SIS scan summary",
        "",
        f"- Input: {md_code(source)}",
        f"- SIS version: {md_code(summary['sis_version'] or 'unknown')}",
        f"- Mode: {md_code(summary['mode'])}",
        f"- Exit code: {md_code(result.returncode)}",
        f"- Report present: {md_code(summary['report_present'])}",
        f"- Verdict: {md_code(label or 'unknown')}",
        f"- Score: {md_code(score if score is not None else 'unknown')}",
        f"- Confidence: {md_code(confidence or 'unknown')}",
        f"- Coverage: {md_code(coverage_state or 'unknown')}",
        f"- Omissions: {md_code(len(omissions))}",
        f"- Findings: {md_code(findings_count if findings_count is not None else 'unknown')}",
        "",
        "## Constraints",
        "",
    ]
    if parse_error:
        lines.append(f"- SIS produced a report that could not be parsed: {md_code(parse_error)}")
    if not report_path.exists():
        lines.append("- SIS did not produce the requested JSON report; inspect stderr before interpreting the exit code.")
    if omissions:
        lines.append("- Coverage was incomplete; Clean here means nothing found in what sis examined, not that the input is safe. Report what was not examined.")
    if label and label.lower() == "anomalous":
        lines.append("- Anomalous means not fully examined; it is a coverage statement, not evidence of a threat.")
    if result.returncode != 0 and args.fail_on and report_path.exists():
        lines.append("- A non-zero result may be the requested verdict gate; confirm against the report and stderr.")
    if len(lines) == 16:
        lines.append("- No additional constraint was derived by the helper; inspect the raw report.")
    (output / "scan-summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    if not report_path.exists() or parse_error:
        return 2
    return result.returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except OSError as exc:
        print(f"sis-scan helper failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
