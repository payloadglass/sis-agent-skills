# CLI contract

The skill targets SIS CLI 0.71.0 or newer (commands below verified against 0.71.0).

## Single file or directory

```bash
sis scan INPUT --emit json=REPORT_PATH
```

`INPUT` may be a file or directory. Directory scanning produces a batch JSON
report. Keep the output path outside the scanned directory.

## Analysis posture (`--analysis-profile`)

```bash
sis scan INPUT --analysis-profile standard --emit json=REPORT_PATH
```

`--analysis-profile quick|standard|deep|strict` names the posture. Verified on 0.71.0
on a benign fixture:

| Profile | What it does | Recorded in the report |
|---|---|---|
| `quick` | cheap detectors only | omission `option.fast` (`analysis_reduced_by_options`); `ai_ingestion_lane_not_run` |
| `standard` | the default; same finding-set fingerprint as omitting the flag | `deep_scan=false` |
| `deep` | expensive detectors; same as `--deep` | `deep_scan=true` in `scan_context_fingerprint` and `structural_summary.deep_scan` |
| `strict` | deep plus strict parser (and parser-diff) | `deep_scan=true`; expect parser-deviation findings |

Never choose `deep` or `strict` silently. The posture is a different view, not
ground truth. The profile name itself is not stored: the report's
`analysis_posture.scan_profile_id` reads `production_default` for all four. Record
the posture from the report instead: `analysis_posture.posture_id`,
`analysis_posture.scan_options_digest`, `scan_context_fingerprint`,
`structural_summary.deep_scan`, `scan_timeout_reached`, and the `option.*` and
`ai_ingestion_lane_not_run` entries of `analysis_coverage.omissions[]`. The options
digest changes whenever any option changes, including a limit passed at its
default value.

## Resource limits

| Flag | sis 0.71.0 default | Helper default | Effect when reached |
|---|---|---|---|
| `--max-decode-bytes N` | 33554432 (32 MiB) | same | per-stream decode cap |
| `--max-total-decoded-bytes N` | 268435456 (256 MiB) | same | total decode cap per file |
| `--max-recursion-depth N` | 64 | same | nesting cap |
| `--timeout-per-file SECONDS` | none | 120 | scan aborts; `scan_timeout_reached` |

Lowering a limit is recorded as an `option.<name>` omission (verified for
`option.max_decode_bytes`); a limit that bites yields coverage `partial` and, with
the verdict gate, can read Anomalous. Raise limits only with the user's approval:
they bound how much hostile data sis expands.

`--password-file FILE` supplies user-vouched passwords (see `references/safety.md`).
`--password VALUE` exists but is not used by this pack.

## Ingestion-axis gate

```bash
sis scan INPUT --analysis-profile standard --fail-on-axis ingest-unsafe --emit json=REPORT_PATH
```

Exits 1 when the AI-ingestion axis is unsafe. It does not replace `sis assess`: a
quick posture does not run the AI-ingestion lane (verified), and errors and timeouts
need separate checking. See the `sis-assess` skill.

## Multiple output formats in one pass

```bash
sis scan INPUT \
  --emit json=report.json \
  --emit sarif=report.sarif
```

Use `--emit` side artefacts rather than running the same hostile input twice.

## Policy gate

```bash
sis scan INPUT --emit json=report.json --fail-on suspicious
```

Accepted thresholds in 0.71.0: `none` (default), `suspicious`, `anomalous`,
`malicious`; there is no `clean`. Labels compare in enum order (`clean` <
`anomalous` < `suspicious` < `malicious`) and a Clean label whose coverage is
withheld ranks as Anomalous. Verified on 0.71.0 with a committed fixture that reads
Anomalous: `--fail-on anomalous` exits 1; `--fail-on suspicious` and `--fail-on
malicious` exit 0. So `anomalous` is the lowest threshold that catches input sis did
not fully examine, and `suspicious` does not. (0.70.0 ranked the labels in a
different order: `--fail-on anomalous` did not trip on Suspicious.) Anomalous is a
coverage statement, not evidence of a threat: gate on it only as an explicit
"require fully examined input" policy.

A gate may return a non-zero policy exit after writing the report. Preserve the
report and distinguish this from a command/configuration failure. Confirm the
accepted threshold using `sis scan --help` on the installed version.

## Text report and JSON shapes (0.71.0)

The text report starts with `Verdict: <label> (<confidence>, coverage <state>)`,
state being `complete`, `partial`, `indeterminate` or `unmeasured` (`not computed`
is never Clean), followed by a `Scope:` line (nodes examined, coverage, gaps).

- Single file JSON: `verdict` (`label`, `score`, `confidence`), `analysis_coverage`
  (`state`, `omissions[]` with `capability_id`, `reason_id`, `scope`), `findings[]`,
  `facts[]`, `summary`.
- Directory (batch) JSON: `summary` (counts only, no verdict), `entries[]` with
  `verdict_label`, `assurance_scope` (`nodes_examined`, `coverage`, `gaps[]`) and
  `coverage_withheld` (present only when true), plus `errors[]` for files that
  failed at batch level and were never examined. No top-level verdict, no per-entry
  findings.

## Optional: write the scan into a corpus index (sis 0.71.0 and newer)

`sis scan INPUT --index CORPUS_OR_INDEX_PATH` is opt-in; a scan is never indexed
implicitly. A new index file is created only with `--create-index`; without it a
missing path is refused (exit 3). It stores the unfiltered report in the
existing corpus index (a corpus name from `~/.config/sis/corpora.toml`, or an index
file path), is idempotent on re-scan of the same content and scanner build, and is
refused with `--stream`. Use it only when the user asked for the result to land in an index;
otherwise keep the JSON report.

## Version and help

Always capture:

```bash
sis --version
sis scan --help
```

If the installed CLI does not expose a required flag, stop and report the
version mismatch instead of guessing an older spelling.
