# CLI contract

The skill targets SIS CLI 0.71.0 or newer (commands below re-run against the 0.72.0 binary on benign files).

## Single file or directory

```bash
sis scan INPUT --emit json=REPORT_PATH
```

`INPUT` may be a file or directory. Directory scanning produces a batch JSON
report. Keep the output path outside the scanned directory.

## Deep analysis

```bash
sis scan INPUT --deep --emit json=REPORT_PATH
```

Deep mode is more expensive and may enable additional detectors. It must not be
used as a silent default when the user requested a quick scan.

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
withheld ranks as Anomalous. Verified on 0.71.0 (and the exit-0 results for a Clean-labelled benign PDF re-run on 0.72.0) with a committed fixture that reads
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

## Running the scan inside an OS sandbox (sis 0.72.0 and newer)

`sis sandbox config --for WRAPPER --input INPUT --output DIR` prints a wrapper
config for one run (`bwrap`, `systemd`, `docker`, `podman`, `macos`,
`windows-sandbox`); it does not run it. Verified on 0.72.0: the bwrap config for a
benign text file, run, wrote `DIR/report.json`. The recipe is in the `sis-setup`
skill. `sis sandbox eval` is dynamic analysis (it executes JavaScript) and is not
part of any scan.

## Optional: write the scan into a corpus index (sis 0.71.0 and newer)

`sis scan INPUT --index CORPUS_OR_INDEX_PATH` is opt-in; a scan is never indexed
implicitly. A new index file is created only with `--create-index`; without it a
missing path is refused (exit 3). A new index path must end in `.db`, `.sqlite` or `.sqlite3` (otherwise sis takes it for a corpus name and refuses). It stores the unfiltered report in the
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
