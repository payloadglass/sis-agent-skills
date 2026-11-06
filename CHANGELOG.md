# Changelog

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
