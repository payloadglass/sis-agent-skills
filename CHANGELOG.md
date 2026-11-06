# Changelog

## 0.2.0

Adds `sis-query`: run a targeted `sis query` projection (findings, chains,
structure, asset-path selectors) against a live file or a saved report,
including the three-valued `--where` predicate semantics and
`excluded_unknown` accounting. Requires SIS CLI 0.71.0 or newer (the unified
`sis query` front door). Updates the manifest, marketplace plugin list,
validator, release builder, and smoke test to seven normalized skills.

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
