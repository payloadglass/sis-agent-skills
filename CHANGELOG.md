# Changelog

## 0.4.0

DRAFT for PO review; not released. Reshapes the pack from eight skills to five.
Verified against the released sis 0.71.0 binary (SHA256SUMS and `gh attestation
verify` checked; only `--help`, `docs`, `explain`, `doctor`, `assess`, `extract`,
`query` and scans of self-authored benign fixtures were run). The minimum stays 0.71.0.

Skills (the six folded skills are removed; their helpers moved):

- `sis-setup`: gains `sis doctor` and `sis docs`.
- `sis-scan` absorbs `sis-analyze`: `--analysis-profile quick|standard|deep|strict` is an
  explicit parameter, the posture is recorded from the report (`posture_id`,
  `scan_options_digest`, `deep_scan`, `option.*` omissions, AI-ingestion lane), and the
  resource limits `--max-decode-bytes`, `--max-total-decoded-bytes`, `--timeout-per-file`,
  `--max-recursion-depth` are passed with documented defaults. `analyze_sample.py` compares
  two postures.
- `sis-investigate` = `sis-query` + `sis explain verdict|finding|members|graph|claim|detection|format`
  + the triage method. `render_triage.py` is removed: `explain verdict` and `explain members`
  cover it. New `run_explain.py`.
- `sis-assess` (new): `sis assess --for ai-ingest`, `--fail-on-axis ingest-unsafe`, the exit-code
  modes (exit 5 indeterminate is NOT safe), `sis extract --safe`/`--profile ai-ingest-safe`.
- `sis-corpus` = index + hunt + evaluate.

Safety across all five (`references/safety.md`, identical copies, checked by the validator):
text extracted from a sample is untrusted data and never followed; run sis inside `bwrap`
(Linux, recipe verified) or `sandbox-exec` (macOS, untested); passwords only via
`--password-file`; extracted bytes in a quarantine path outside any scanned directory;
`sis sandbox eval`, `sis explain claim` and `--dynamic-analysis-policy sandboxed` execute
script and need explicit approval (`explain claim` requests a runtime posture).

Drift check: `scripts/check_contract_drift.py` asserts every `tested_contract` command and
flag exists in the binary named by `SIS_BIN`; `validate_pack.py` runs it when `SIS_BIN` is set.

Not claimed (requires sis 0.72 or newer, not in 0.71.0): `sis sandbox config --for bwrap`,
`sis query --describe`/`--contract-version`, the query pipeline grammar.

Drift found while verifying (0.71.0): `sis assess --safe-text` prints `safe_text...` lines before
its JSON; `explain claim` runs at a runtime posture; `explain verdict FILE` re-analyses at
`deep` breadth, so compare a verdict with a scan only through `--from-report`;
`analysis_posture.scan_profile_id` reads `production_default` for every profile.

## 0.3.1

Accuracy release, verified against the released sis 0.71.0 binary (SHA256SUMS and
`gh attestation verify` checked; only `--help`, `docs`, `explain` and scans of
self-authored benign fixtures were run).

- Adds `sis-query` (the eighth skill), reconciled to 0.71.0. Drift fixed relative to the
  held draft: 0.71.0 has no `sis query --contract-version` or `--describe` (the helper now
  gates on `sis --version` and records the answer's `contract` object); the query pipeline
  grammar and `--format dot` are rejected; `--where` works on `findings` spellings;
  `policy.active`, `catalog`, `trailer`, `verdict`, `why`, `tree` and `intent` are removed
  (`QUERY_REMOVED`, exit 3); exit 5 is not documented for `sis query`.
- `sis explain-format` is now `sis explain format` everywhere (the canonical form).
- The release workflow no longer runs on pull requests; it runs for a pushed `v*` tag
  or a manual dispatch only.

## 0.3.0

Verified against the released sis 0.71.0 (minimum and tested against 0.71.0). 0.71
changed what a report means; an agent following 0.2.0 would have misread it. Nothing
is published by this repository until a tag is pushed.

Changed (report semantics, from sis 0.71.0 docs and verified on the binary):

- A file sis could not fully examine reads **Anomalous**, not Clean. It is a coverage
  statement, not evidence of a threat, and not a pass. Encrypted PDFs: streams sis
  cannot decrypt are not examined. The text report starts with a `Verdict:` line;
  omission reasons are typed (`stream:decode_failed`, `detector_cost_excluded`, ...).
- `--fail-on` accepts `none|suspicious|anomalous|malicious` and ranks Clean <
  Anomalous < Suspicious < Malicious (0.70.0 ordered them differently), a
  coverage-withheld Clean ranking as Anomalous. Verified: `--fail-on anomalous` is
  the lowest threshold that trips on not-fully-examined input; `suspicious` does not.
- Scoped assurance (ADR-0011) restated where the labels are explained
  (sis-scan, sis-triage, sis-analyze, sis-corpus-evaluate, helper output): Clean
  means nothing found in what sis examined, never safe; always report what was not
  examined.
- Corpus skills: `sis scan --index` and `sis corpus correlate` are now verified on
  a published binary (no longer "documented, not verified"). A new index requires
  `--create-index`; the old "a mistyped path may create an index" note is removed.
  `correlate` refuses when it skipped everything; `--allow-skips` overrides.
- `compatibility.json` minimum and tested_against 0.71.0, with the verified commands.
  `check_sis.sh` defaults to 0.71.0.

Fixed (helpers):

- `run_scan.py` read nothing from a directory (batch) report: it reported verdict
  and coverage as unknown. It now reports the worst `entries[].verdict_label`,
  coverage from `assurance_scope`/`coverage_withheld`, files that failed at batch
  level (`errors[]`) as not examined, and the count from `summary.total`; it also
  accepts `--fail-on anomalous`.
- `evaluate_corpus.py` read coverage only from `analysis_coverage`, absent from batch
  entries; it now uses `assurance_scope` and `coverage_withheld` and lists Anomalous
  entries as review candidates.
- `render_triage.py` states the Anomalous and scoped-assurance caveats.
- Smoke test fake emits the real 0.71 batch shape, including `errors[]`.

Known limits:

- sis 0.70.0 and 0.71.0 on macOS: `sis sanitize release` refuses (F4520, fix planned
  for 0.71.1). Scanning, `doctor` and `sanitize apply` work.

## 0.2.0

For sis 0.70.0 (minimum 0.70.0, tested against 0.70.0). Nothing is published by this repository until a tag is pushed.

Added:

- `sis-setup`: detect `sis`, compare its version with `compatibility.json`, and, only
  with explicit user approval, install a release archive after verifying its SHA-256
  against `SHA256SUMS` and its GitHub build attestation (`gh attestation verify`).
  It refuses a failed check, states plainly when `gh` is unavailable and provenance
  is therefore unverified, never pipes a download into a shell, and runs nothing
  before verification. Helpers: `check_sis.sh`, `install_verified.sh` (verify and
  extract only; the agent performs the approved download).
- Trigger cases for `sis-setup`, host discovery protocol (`evals/discovery-protocol.md`,
  not run), hosted-sandbox protocol and draft listing copy under `docs/`.

Changed:

- Minimum sis version is 0.70.0 (was 0.6.6) for all skills, declared in
  `compatibility.json`. `validate_pack.py` checks each skill states that minimum.
- `compatibility.json` now lists the commands verified against sis 0.70.0
  (`tested_contract`) separately from 0.71.0 behaviour that is documented but not
  yet verified against a published binary.
- Corpus skills: verified every command against 0.70.0 and added version-guarded
  notes: `sis scan --index` (0.71.0 and newer, opt-in) and `sis corpus correlate`
  (0.70.0 can report zero clusters for input it did not recognise; from 0.71.0 it
  fails non-zero when it skipped everything, and `--allow-skips` overrides). Added
  `sync --prune`, `--manifest`, `--reports`, `corpus extract --location` and the
  `--meta-key` filter. Nothing documented was found to be removed in 0.70.0.
- `sis-scan`: gate on `--fail-on suspicious`; 0.70.0's `--fail-on anomalous` does not
  trip on a Suspicious verdict. A `Clean` verdict does not show a file is safe.
- `sis-triage` helper no longer prints "unknown" for a version the report does not
  record; it says where to take it from.
- Removed a committed `__pycache__/*.pyc`; added `.gitignore`.
- CI workflow: default pack version 0.2.0; shell syntax check covers the new helpers.

Known limits:

- The 0.71.0-guarded notes in the corpus skills have not been verified against a published 0.71.0 binary.
- sis 0.70.0 on macOS: `sis sanitize release` does not start its worker (upstream
  known issue).

## 0.1.0

Initial CLI-only pack with six normalized skills:

- `sis-scan`
- `sis-triage`
- `sis-analyze`
- `sis-corpus-index`
- `sis-corpus-hunt`
- `sis-corpus-evaluate`

Also includes structural validation, behavioral smoke tests, deterministic release
ZIP generation, trigger evaluation cases, a Claude Code marketplace manifest,
and GitHub workflows for OpenAI/Codex-compatible ZIP assets.
