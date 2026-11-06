# CLI contract

The skill targets SIS CLI 0.70.0 or newer (commands below verified against 0.70.0).

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

Gate on `suspicious` (or `malicious`). In 0.70.0 `--fail-on anomalous` does not
trip on a Suspicious verdict because the gate orders the labels differently from
the verdict; read `verdict.label` in the JSON if you need the exact label.

A gate may return a non-zero policy exit after writing the report. Preserve the
report and distinguish this from a command/configuration failure. Confirm the
accepted threshold using `sis scan --help` on the installed version.

## Optional: write the scan into a corpus index (sis 0.71.0 and newer)

`sis scan INPUT --index CORPUS_OR_INDEX_PATH` is opt-in and does not exist in
0.70.0; a scan is never indexed implicitly. It stores the unfiltered report in the
existing corpus index (a corpus name from `~/.config/sis/corpora.toml`, or an index
file path), is idempotent on re-scan of the same content and scanner build, and is
refused with `--stream`. Check the path: a mistyped index path may create a new,
empty index. Use it only when the user asked for the result to land in an index;
otherwise keep the JSON report.

## Version and help

Always capture:

```bash
sis --version
sis scan --help
```

If the installed CLI does not expose a required flag, stop and report the
version mismatch instead of guessing an older spelling.
