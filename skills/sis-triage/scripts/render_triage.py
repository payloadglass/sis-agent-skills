#!/usr/bin/env python3
"""Render observed SIS report fields into conservative triage artefacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


def md_code(value: object) -> str:
    text = str(value).replace("\r", " ").replace("\n", " ")
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    fence = "`" * max(1, longest + 1)
    return f"{fence}{text}{fence}"


SEVERITY = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
CONFIDENCE = {"certain": 6, "strong": 5, "probable": 4, "tentative": 3, "weak": 2, "unknown": 1}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rank(finding: dict) -> tuple[int, int, str]:
    return (
        SEVERITY.get(str(finding.get("severity", "")).lower(), 0),
        CONFIDENCE.get(str(finding.get("confidence", "")).lower(), 0),
        str(finding.get("kind", "")),
    )


def verdict(report: dict) -> dict:
    value = report.get("verdict")
    if isinstance(value, dict):
        return {k: value.get(k) for k in ("label", "score", "confidence", "profile")}
    return {"label": value if isinstance(value, str) else None, "score": None, "confidence": None, "profile": None}


def coverage(report: dict) -> dict:
    value = report.get("analysis_coverage")
    if isinstance(value, dict):
        return {"state": value.get("state"), "omissions": value.get("omissions", [])}
    return {"state": None, "omissions": []}


def finding_view(item: dict) -> dict:
    return {
        "id": item.get("id"),
        "kind": item.get("kind"),
        "severity": item.get("severity"),
        "confidence": item.get("confidence"),
        "impact": item.get("impact"),
        "title": item.get("title"),
        "objects": item.get("objects", []),
        "evidence_count": len(item.get("evidence", [])) if isinstance(item.get("evidence"), list) else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args()

    report_path = args.report.resolve()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        parser.error("report root must be a JSON object")
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)

    findings = report.get("findings", [])
    findings = [item for item in findings if isinstance(item, dict)] if isinstance(findings, list) else []
    prioritized = [finding_view(item) for item in sorted(findings, key=rank, reverse=True)[: args.top]]
    cov = coverage(report)
    observed = {
        "report": str(report_path),
        "report_sha256": digest(report_path),
        "sis_version": report.get("engine_version") or report.get("sis_version") or report.get("version"),
        "verdict": verdict(report),
        "coverage": cov,
        "findings_count": len(findings),
        "top_findings": prioritized,
        "provider_participation": report.get("provider_participation"),
        "asset_graph_present": isinstance(report.get("asset_graph"), dict),
        "recommended_actions": [
            {"priority": "P1", "action": "Review material findings and their evidence/asset context."},
            {"priority": "P1", "action": "Resolve material analysis omissions before relying on negative conclusions."} if cov["omissions"] else {"priority": "P2", "action": "Preserve the report with the case record."},
        ],
        "analyst_hypotheses": [],
    }
    (output / "triage.json").write_text(json.dumps(observed, indent=2) + "\n", encoding="utf-8")

    v = observed["verdict"]
    lines = [
        "# SIS triage",
        "",
        "## Scan identity",
        "",
        f"- Report: {md_code(report_path)}",
        f"- Report SHA-256: {md_code(observed['report_sha256'])}",
        f"- SIS version: {md_code(observed['sis_version'] or 'unknown')}",
        f"- Verdict: {md_code(v.get('label') or 'unknown')}",
        f"- Score: {md_code(v.get('score') if v.get('score') is not None else 'unknown')}",
        f"- Confidence: {md_code(v.get('confidence') or 'unknown')}",
        f"- Coverage: {md_code(cov.get('state') or 'unknown')}",
        f"- Findings: {md_code(len(findings))}",
        "",
        "## Material SIS findings",
        "",
    ]
    if prioritized:
        for item in prioritized:
            lines.append(f"- {md_code(item.get('kind') or 'unknown')} — {md_code(item.get('severity') or 'unknown')} / {md_code(item.get('confidence') or 'unknown')} — {md_code(item.get('title') or '')}")
    else:
        lines.append("- No findings were present in the report. This is not, by itself, a safety conclusion.")
    lines += ["", "## Analysis gaps", ""]
    omissions = cov.get("omissions") or []
    if omissions:
        for item in omissions:
            if isinstance(item, dict):
                capability = item.get("capability_id") or item.get("kind") or "unknown"
                reason = item.get("reason_id") or item.get("reason") or "unspecified"
            else:
                capability, reason = "unknown", item
            lines.append(f"- {md_code(capability)} — {md_code(reason)}")
    else:
        lines.append("- No `analysis_coverage.omissions` entries were present; inspect other completeness surfaces before asserting full coverage.")
    lines += [
        "",
        "## Analyst hypotheses",
        "",
        "- None generated automatically. Add only evidence-backed hypotheses and label them explicitly.",
        "",
        "## Actions",
        "",
    ]
    for action in observed["recommended_actions"]:
        lines.append(f"- {action['priority']}: {action['action']}")
    (output / "triage.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"sis-triage helper failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
