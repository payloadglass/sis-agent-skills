# Host discovery evaluation protocol

Status: **not run.** No host harness is available locally. `evals/trigger-cases.json`
holds the host-neutral cases (`python3 -I scripts/validate_pack.py` checks that
every skill has at least one positive and one negative case, and nothing more).
Running prompts against a real host needs that host's agent and, for Claude Code
and Codex, an account/API key and a model call per case, which this repository's
scripts do not do and which must not run in CI (owner standing rule: CI is for
releases). Record results below, per host, when someone runs them.

## Procedure (per host: Claude Code, Codex)

1. Clean profile, clean machine or container. Install the pack from the release
   ZIP (Codex) or the marketplace manifest (Claude Code). Record host version,
   model, pack version and commit.
2. For each case in `trigger-cases.json`, start a **fresh session** and send the
   `prompt` verbatim. Do not name the skill. Use a benign local fixture; never a
   live sample.
3. Record which skill, if any, the host loaded or announced first. Stop the
   session before any scan runs unless you are doing the end-to-end check below.
4. Score: `should_trigger: true` passes only if the named skill was selected;
   `should_trigger: false` passes if the named skill was **not** selected. Also note
   the case where a different SIS skill was selected (confusion between neighbours
   is a finding even when the case passes).
5. Repeat each case 3 times; a case passes only if all 3 agree.

## End-to-end check (acceptance item 1)

On a clean machine: install the pack, ask for a bounded scan of a benign fixture
with no `sis` installed. Expected: `sis-setup` reports missing, asks approval,
verifies checksum and attestation, extracts, then `sis-scan` completes and the
summary keeps coverage and omissions. Also expected: refuses a tampered archive and
a too-old binary, with a plain statement and nothing piped to a shell.

## Result table (fill in)

| Host | Host version | Model | Date | Cases passed / total | Confusions | Run by |
|---|---|---|---|---|---|---|
| Claude Code | not run | | | | | |
| Codex | not run | | | | | |

What was done locally instead: structural validation of the case file (every skill
has a positive and a negative case) and a review of descriptions for overlap with
neighbouring skills. That is not discovery evidence.
