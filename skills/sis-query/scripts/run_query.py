#!/usr/bin/env python3
"""Run one `sis query` invocation, preserve raw output/logs, and summarize it
conservatively: exit code, structured error code, and excluded_unknown — never
a recomputed verdict or severity."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def md_code(value: object) -> str:
    text = str(value).replace("\r", " ").replace("\n", " ")
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    fence = "`" * max(1, longest + 1)
    return f"{fence}{text}{fence}"


def get_text(binary: str, *args: str) -> str:
    result = subprocess.run([binary, *args], text=True, capture_output=True, check=False)
    return (result.stdout or result.stderr).strip()


def extract_envelope(stdout: str, fmt: str) -> tuple[dict | None, str | None]:
    """Parse a json/jsonl result envelope. Returns (envelope, parse_error)."""
    if fmt not in ("json", "jsonl"):
        return None, None
    text = stdout.strip()
    if not text:
        return None, None
    try:
        if fmt == "jsonl":
            lines = [json.loads(line) for line in text.splitlines() if line.strip()]
            return (lines[0] if len(lines) == 1 else {"lines": lines}), None
        value = json.loads(text)
        return value if isinstance(value, dict) else {"value": value}, None
    except json.JSONDecodeError as exc:
        return None, str(exc)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="query string, e.g. 'findings.high'")
    parser.add_argument("input", nargs="?", help="input file path (omit with --from-report or --path)")
    parser.add_argument("--from-report", dest="from_report")
    parser.add_argument("--path", dest="batch_path")
    parser.add_argument("--where")
    parser.add_argument("--format", default="json", choices=("text", "json", "jsonl", "yaml", "yml", "csv"))
    parser.add_argument("--deep", action="store_true")
    parser.add_argument("--chain-summary", choices=("minimal", "events", "full"))
    parser.add_argument("--extract-to")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--sis-bin", default=None)
    args = parser.parse_args()

    sis_bin = args.sis_bin or os.environ.get("SIS_BIN", "sis")

    if not args.input and not args.from_report and not args.batch_path:
        parser.error("one of INPUT, --from-report, or --path is required")

    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)

    command = [sis_bin, "query", args.query]
    if args.input:
        command.append(str(Path(args.input).resolve()))
    if args.from_report:
        command += ["--from-report", str(Path(args.from_report).resolve())]
    if args.batch_path:
        command += ["--path", str(Path(args.batch_path).resolve())]
    command += ["--format", args.format]
    if args.where:
        command += ["--where", args.where]
    if args.deep:
        command.append("--deep")
    if args.chain_summary:
        command += ["--chain-summary", args.chain_summary]
    if args.extract_to:
        command += ["--extract-to", str(Path(args.extract_to).resolve())]

    sis_version = get_text(sis_bin, "--version")
    probe = subprocess.run([sis_bin, "query", "--contract-version"], text=True, capture_output=True, check=False)
    if probe.returncode != 0:
        # A build before the unified `sis query` front door (0.71.0) has no
        # --contract-version. Stop rather than run a query whose shape and
        # semantics this skill does not describe.
        message = (
            "This sis build does not report a query contract version "
            "(`sis query --contract-version` failed). sis-query needs sis 0.71.0 or newer; "
            "no query was run."
        )
        (output / "query-summary.json").write_text(
            json.dumps(
                {
                    "status": "unsupported_sis_version",
                    "sis_version": sis_version,
                    "contract_probe_exit_code": probe.returncode,
                    "contract_probe_stderr": probe.stderr.strip(),
                    "message": message,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(message, file=sys.stderr)
        return 2
    contract_version = (probe.stdout or probe.stderr).strip()

    started = dt.datetime.now(dt.timezone.utc)
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    finished = dt.datetime.now(dt.timezone.utc)

    (output / "sis.stdout.log").write_text(result.stdout, encoding="utf-8")
    (output / "sis.stderr.log").write_text(result.stderr, encoding="utf-8")

    envelope, parse_error = extract_envelope(result.stdout, args.format)
    result_field = envelope.get("result") if isinstance(envelope, dict) else None
    error_code = None
    excluded_unknown = None
    envelope_contract = envelope.get("contract") if isinstance(envelope, dict) else None
    findings_view = None
    if isinstance(envelope, dict) and isinstance(envelope.get("context"), dict):
        findings_view = envelope["context"].get("findings_view")
    if isinstance(result_field, dict):
        if result_field.get("status") == "error":
            error_code = result_field.get("error_code")
        excluded_unknown = result_field.get("excluded_unknown")
    if isinstance(envelope, dict) and excluded_unknown is None:
        excluded_unknown = envelope.get("excluded_unknown")

    summary = {
        "command": command,
        "sis_version": sis_version,
        "contract_version": contract_version,
        "started_utc": started.isoformat(),
        "finished_utc": finished.isoformat(),
        "exit_code": result.returncode,
        "format": args.format,
        "where": args.where,
        "envelope_parse_error": parse_error,
        "error_code": error_code,
        "excluded_unknown": excluded_unknown,
        "envelope_contract": envelope_contract,
        "findings_view": findings_view,
    }
    (output / "query-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if envelope is not None:
        (output / "query-result.json").write_text(json.dumps(envelope, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# SIS query summary",
        "",
        f"- Command: {md_code(' '.join(command))}",
        f"- SIS version: {md_code(sis_version or 'unknown')}",
        f"- Contract version: {md_code(contract_version or 'unknown')}",
        f"- Exit code: {md_code(result.returncode)}",
        f"- Error code: {md_code(error_code or 'none')}",
        f"- Excluded (unknown subjects): {md_code(excluded_unknown if excluded_unknown is not None else 'n/a')}",
        "",
        "## Constraints",
        "",
    ]
    constraints = 0
    if parse_error:
        constraints += 1
        lines.append(f"- The result could not be parsed as {args.format}: {md_code(parse_error)}")
    if error_code:
        constraints += 1
        lines.append("- The query returned a structured error; see error_code above before interpreting the result.")
    if result.returncode == 5:
        constraints += 1
        lines.append(
            "- Exit 5 means the query was answered but the answer is incomplete "
            "(`ENGINE_ANSWER_INCOMPLETE`). Report it as incomplete, never as a clean or empty result."
        )
    if findings_view == "filtered":
        constraints += 1
        lines.append(
            "- The saved report's findings were filtered after the scan (`findings_view: filtered`); "
            "answers reflect the filtered view, not the full finding set."
        )
    if excluded_unknown:
        constraints += 1
        lines.append(
            "- Some subjects were excluded because a filtered field was never recorded for them "
            "(unknown, not false/zero) — this is not the same as zero matches."
        )
    if result.returncode == 0 and not error_code and not parse_error:
        constraints += 1
        lines.append("- Exit 0 with no structured error: the query completed. An empty result is a real answer about this projection; it is not evidence that the file is safe.")
    if constraints == 0:
        lines.append("- No additional constraint was derived by the helper; inspect the raw result.")
    (output / "query-summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    return result.returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except OSError as exc:
        print(f"sis-query helper failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
