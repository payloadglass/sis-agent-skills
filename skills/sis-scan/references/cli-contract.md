# CLI contract

The skill targets SIS CLI 0.6.6 or newer.

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

A gate may return a non-zero policy exit after writing the report. Preserve the
report and distinguish this from a command/configuration failure. Confirm the
accepted threshold using `sis scan --help` on the installed version.

## Version and help

Always capture:

```bash
sis --version
sis scan --help
```

If the installed CLI does not expose a required flag, stop and report the
version mismatch instead of guessing an older spelling.
