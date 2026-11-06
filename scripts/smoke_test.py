#!/usr/bin/env python3
"""Exercise every bundled helper against a deterministic fake SIS CLI."""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FAKE_SIS = r'''#!/usr/bin/env python3
import json
import pathlib
import sys

args = sys.argv[1:]
if args == ["--version"]:
    print("sis 0.6.6-smoke`\n## injected")
    raise SystemExit(0)
if args and args[0] == "scan":
    source = pathlib.Path(args[1])
    deep = "--deep" in args
    emit = next((item.split("=", 1)[1] for item in args if item.startswith("json=")), None)
    if not emit:
        raise SystemExit(2)
    if source.is_dir():
        report = {
            "entries": [
                {
                    "path": str(source / "a.pdf"),
                    "status": "ok",
                    "verdict_label": "Clean",
                    "score": 0.0,
                    "findings": [],
                    "analysis_coverage": {"state": "complete", "omissions": []},
                    "runtime_ms": 10,
                },
                {
                    "path": "hostile`\n## injected",
                    "status": "ok",
                    "verdict_label": "Suspicious",
                    "score": 0.7,
                    "findings": [
                        {
                            "kind": "pdf:test`\n## injected",
                            "severity": "High",
                            "confidence": "Strong",
                        }
                    ],
                    "analysis_coverage": {
                        "state": "partial",
                        "omissions": [
                            {"capability_id": "detector.test", "reason_id": "fast_excluded"}
                        ],
                    },
                    "runtime_ms": 30,
                },
            ],
            "summary": {"worst_verdict": "Suspicious", "findings_count": 1},
        }
    else:
        report = {
            "engine_version": "0.6.6-smoke",
            "verdict": {
                "label": "Suspicious" if deep else "Anomalous",
                "score": 0.7 if deep else 0.4,
                "confidence": "Strong",
            },
            "analysis_coverage": {
                "state": "complete" if deep else "partial",
                "omissions": []
                if deep
                else [{"capability_id": "detector.js_sandbox", "reason_id": "fast_excluded"}],
            },
            "findings": [
                {
                    "id": "f1",
                    "kind": "pdf:test`\n## injected",
                    "severity": "High" if deep else "Medium",
                    "confidence": "Strong",
                    "title": "title`\n## injected",
                    "objects": ["1 0 obj"],
                    "evidence": [],
                }
            ],
        }
        if deep:
            report["findings"].append(
                {
                    "id": "f2",
                    "kind": "js:test_deep",
                    "severity": "High",
                    "confidence": "Probable",
                    "title": "deep",
                    "objects": ["2 0 obj"],
                    "evidence": [],
                }
            )
    target = pathlib.Path(emit)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report), encoding="utf-8")
    raise SystemExit(0)
if args[:2] == ["corpus", "sync"]:
    print("synced 2 items")
    raise SystemExit(0)
if args[:2] == ["corpus", "status"]:
    print("items=2 occurrences=2 observations=3")
    raise SystemExit(0)
if args[:2] == ["corpus", "query"]:
    print(json.dumps({"unit": "distinct_items", "groups": [{"key": "pdf:test", "count": 1}]}))
    raise SystemExit(0)
if args[:2] == ["query", "--contract-version"]:
    print("language=2 result=4")
    raise SystemExit(0)
if args[:1] == ["query"]:
    fmt = next((args[i + 1] for i, a in enumerate(args) if a == "--format"), "text")
    where = next((args[i + 1] for i, a in enumerate(args) if a == "--where"), None)
    if fmt not in ("json", "jsonl"):
        print("1 finding (text mode, see --format json for structure)")
        raise SystemExit(0)
    envelope = {
        "file": "sample`hostile.pdf",
        "query": args[1],
        "contract": {"language": 2, "result": 4},
        "result": [
            {
                "id": "f1",
                "kind": "pdf:test`\n## injected",
                "severity": "High",
                "confidence": "Strong",
            }
        ],
    }
    if where:
        envelope["excluded_unknown"] = 1
    print(json.dumps(envelope))
    raise SystemExit(0)
print(f"unsupported fake SIS invocation: {args}", file=sys.stderr)
raise SystemExit(2)
'''


def run(command: list[str], *, expected: int = 0) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode != expected:
        raise RuntimeError(
            f"command returned {result.returncode}, expected {expected}: {command}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"expected JSON object: {path}")
    return value


def assert_markdown_safe(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "\n## injected\n" in text:
        raise AssertionError(f"untrusted report text escaped Markdown code quoting: {path}")


def check_setup_scripts(tmp: Path, fake_sis: Path) -> None:
    """Exercise sis-setup: version detection, checksum/attestation/contents refusals."""
    scripts = ROOT / "skills/sis-setup/scripts"
    check = scripts / "check_sis.sh"
    install = scripts / "install_verified.sh"
    work = tmp / "setup"
    work.mkdir()

    # --- check_sis.sh: fake binary reports 0.6.6-smoke
    old = run([str(check), "--sis-bin", str(fake_sis), "--minimum", "0.70.0"], expected=4)
    if "status=too_old" not in old.stdout:
        raise AssertionError("check_sis.sh did not report a too-old binary")
    run([str(check), "--sis-bin", str(fake_sis), "--minimum", "0.6.6"], expected=4)  # prerelease < release
    run([str(check), "--sis-bin", str(work / "nope")], expected=3)

    modern = work / "modern" / "sis"
    modern.parent.mkdir()
    modern.write_text("#!/bin/sh\necho 'sis 0.71.0'\n", encoding="utf-8")
    modern.chmod(0o755)
    run([str(check), "--sis-bin", str(modern), "--minimum", "0.70.0"])
    run([str(check), "--sis-bin", str(modern), "--minimum", "0.71.0"])
    run([str(check), "--sis-bin", str(modern), "--minimum", "0.72.0"], expected=4)
    garbled = work / "garbled" / "sis"
    garbled.parent.mkdir()
    garbled.write_text("#!/bin/sh\necho 'hello`\n## injected'\n", encoding="utf-8")
    garbled.chmod(0o755)
    run([str(check), "--sis-bin", str(garbled)], expected=5)

    # --- install_verified.sh with a synthetic archive
    def make_archive(name: str, members: dict[str, bytes]) -> Path:
        path = work / name
        with tarfile.open(path, "w:gz") as tar:
            for member, data in members.items():
                info = tarfile.TarInfo(member)
                info.size = len(data)
                info.mode = 0o755
                tar.addfile(info, io.BytesIO(data))
        return path

    def write_sums(archive: Path, digest: str | None = None, label: str = "good") -> Path:
        digest = digest or hashlib.sha256(archive.read_bytes()).hexdigest()
        sums = work / f"SHA256SUMS.{label}.{archive.name}"
        sums.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
        return sums

    good = make_archive(
        "sis-v9.9.9-test.tar.gz",
        {"sis": b"#!/bin/sh\necho 'sis 9.9.9'\n", "sis-cdr-worker": b"#!/bin/sh\n"},
    )
    good_sums = write_sums(good)

    # fake `gh` (passes / fails) and a tools-only PATH without gh
    tool_dir = work / "tools"
    tool_dir.mkdir()
    for tool in ("sha256sum", "shasum", "tar", "gzip", "awk", "grep", "cut", "tr", "basename", "head", "chmod", "mkdir", "cat", "sh", "bash", "env"):
        found = shutil.which(tool)
        if found:
            (tool_dir / tool).symlink_to(found)
    gh_dir = work / "gh-ok"
    gh_dir.mkdir()
    (gh_dir / "gh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    (gh_dir / "gh").chmod(0o755)
    gh_bad = work / "gh-bad"
    gh_bad.mkdir()
    (gh_bad / "gh").write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    (gh_bad / "gh").chmod(0o755)

    def with_path(*dirs: Path) -> dict[str, str]:
        return {**os.environ, "PATH": os.pathsep.join(str(d) for d in dirs)}

    def run_install(archive: Path, sums: Path, dest: str, env: dict[str, str], *extra: str, expected: int):
        result = subprocess.run(
            [str(install), "--archive", str(archive), "--sums", str(sums), "--dest", str(work / dest), *extra],
            text=True, capture_output=True, check=False, env=env,
        )
        if result.returncode != expected:
            raise AssertionError(f"install_verified.sh {dest}: exit {result.returncode}, expected {expected}\n{result.stdout}\n{result.stderr}")
        return result

    ok = run_install(good, good_sums, "dest-ok", with_path(gh_dir, tool_dir), expected=0)
    if "attestation=verified" not in ok.stdout or not (work / "dest-ok/sis").is_file():
        raise AssertionError("verified install did not extract")
    run_install(good, good_sums, "dest-ok", with_path(gh_dir, tool_dir), expected=2)  # never overwrite
    run_install(good, write_sums(good, "0" * 64, "bad"), "dest-badsum", with_path(gh_dir, tool_dir), expected=10)
    other = work / "SHA256SUMS.other"
    other.write_text("0" * 64 + "  some-other-archive.tar.gz\n", encoding="utf-8")
    run_install(good, other, "dest-noline", with_path(gh_dir, tool_dir), expected=10)
    run_install(good, good_sums, "dest-badatt", with_path(gh_bad, tool_dir), expected=11)
    if (work / "dest-badatt").exists() or (work / "dest-badsum").exists():
        raise AssertionError("a refused archive was extracted")
    nogh = run_install(good, good_sums, "dest-nogh", with_path(tool_dir), expected=20)
    if "NOT verified" not in nogh.stderr or (work / "dest-nogh").exists():
        raise AssertionError("missing gh must be stated plainly and extract nothing")
    accepted = run_install(good, good_sums, "dest-accepted", with_path(tool_dir), "--accept-unattested", expected=0)
    if "attestation=not-verified" not in accepted.stdout:
        raise AssertionError("an unattested install must not be reported as verified")
    evil = make_archive("sis-v9.9.9-evil.tar.gz", {"sis": b"#!/bin/sh\n", "../escape": b"x"})
    run_install(evil, write_sums(evil), "dest-evil", with_path(gh_dir, tool_dir), expected=12)
    if (work / "escape").exists() or (work / "dest-evil").exists():
        raise AssertionError("an archive with an unexpected member was extracted")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="sis-agent-skills-") as tmp_raw:
        tmp = Path(tmp_raw)
        binary = tmp / "bin" / "sis"
        binary.parent.mkdir()
        binary.write_text(FAKE_SIS, encoding="utf-8")
        binary.chmod(0o755)

        check_setup_scripts(tmp, binary)

        sample = tmp / "sample`hostile.pdf"
        sample.write_bytes(b"sample")
        corpus = tmp / "corpus"
        corpus.mkdir()
        (corpus / "a.pdf").write_bytes(b"a")
        (corpus / "b.pdf").write_bytes(b"b")
        output = tmp / "output"
        output.mkdir()

        run([
            sys.executable,
            str(ROOT / "skills/sis-scan/scripts/run_scan.py"),
            str(sample),
            "--output-dir",
            str(output / "scan"),
            "--sis-bin",
            str(binary),
        ])
        run([
            sys.executable,
            str(ROOT / "skills/sis-triage/scripts/render_triage.py"),
            str(output / "scan/report.json"),
            "--output-dir",
            str(output / "triage"),
        ])
        run([
            sys.executable,
            str(ROOT / "skills/sis-analyze/scripts/analyze_sample.py"),
            str(sample),
            "--output-dir",
            str(output / "analyze"),
            "--sis-bin",
            str(binary),
        ])
        run([
            sys.executable,
            str(ROOT / "skills/sis-query/scripts/run_query.py"),
            "findings.high",
            str(sample),
            "--where",
            "confidence == 'Strong'",
            "--output-dir",
            str(output / "query"),
            "--sis-bin",
            str(binary),
        ])
        old_binary = tmp / "old" / "sis"
        old_binary.parent.mkdir()
        old_binary.write_text(
            "#!/usr/bin/env python3\nimport sys\n"
            "if sys.argv[1:] == ['--version']:\n    print('sis 0.70.0')\n    raise SystemExit(0)\n"
            "print('error: unexpected argument', file=sys.stderr)\nraise SystemExit(2)\n",
            encoding="utf-8",
        )
        old_binary.chmod(0o755)
        run([
            sys.executable,
            str(ROOT / "skills/sis-query/scripts/run_query.py"),
            "findings",
            str(sample),
            "--output-dir",
            str(output / "query-old"),
            "--sis-bin",
            str(old_binary),
        ], expected=2)
        if load(output / "query-old/query-summary.json")["status"] != "unsupported_sis_version":
            raise AssertionError("query helper ran against a sis build without a query contract version")
        run([
            str(ROOT / "skills/sis-corpus-index/scripts/sync_index.sh"),
            "--name",
            "test` corpus",
            "--location",
            str(corpus),
            "--index",
            str(tmp / "index/test db.sis"),
            "--jobs",
            "2",
            "--output-dir",
            str(output / "index out"),
            "--sis-bin",
            str(binary),
        ])
        run([
            str(ROOT / "skills/sis-corpus-hunt/scripts/query_index.sh"),
            "--name",
            "test",
            "--index",
            str(tmp / "index/test db.sis"),
            "--family",
            "finding",
            "--group",
            "kind",
            "--value",
            "ACME O'Reilly",
            "--output",
            str(output / "hunt/result.json"),
            "--sis-bin",
            str(binary),
        ])
        run([
            sys.executable,
            str(ROOT / "skills/sis-corpus-evaluate/scripts/evaluate_corpus.py"),
            str(corpus),
            "--output-root",
            str(output / "evaluate"),
            "--run-id",
            "run1",
            "--sis-bin",
            str(binary),
        ])

        if load(output / "analyze/analysis.json")["deep"]["finding_count"] != 2:
            raise AssertionError("deep finding count was not preserved")
        if load(output / "index out/index-run.json")["sync_command"][1:3] != ["corpus", "sync"]:
            raise AssertionError("index command was not preserved as an argv array")
        hunt = load(output / "hunt/result.command.json")
        if hunt["value"] != "ACME O'Reilly" or hunt["command"][0] != str(binary):
            raise AssertionError("hunt metadata lost command arguments")
        if load(output / "evaluate/run1/summary.json")["files_scanned"] != 2:
            raise AssertionError("batch entries were not counted")
        query_summary = load(output / "query/query-summary.json")
        if query_summary["exit_code"] != 0 or query_summary["excluded_unknown"] != 1:
            raise AssertionError("query helper lost excluded_unknown accounting")
        if load(output / "query/query-result.json")["result"][0]["kind"] != "pdf:test`\n## injected":
            raise AssertionError("query helper did not preserve the raw result verbatim")

        for path in [
            output / "scan/scan-summary.md",
            output / "triage/triage.md",
            output / "analyze/analysis.md",
            output / "query/query-summary.md",
            output / "index out/index-run.md",
            output / "evaluate/run1/summary.md",
        ]:
            assert_markdown_safe(path)

        missing = run([
            sys.executable,
            str(ROOT / "skills/sis-scan/scripts/run_scan.py"),
            str(sample),
            "--output-dir",
            str(output / "missing"),
            "--sis-bin",
            str(tmp / "missing-sis"),
        ], expected=2)
        if "Traceback" in missing.stderr:
            raise AssertionError("missing CLI produced a Python traceback")

    print("smoke-tested all eight SIS Agent Skills helpers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
