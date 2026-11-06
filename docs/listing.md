# Listing material (draft, not published)

Status: **draft for owner review.** Nothing here has been submitted to any
marketplace or directory. Publication waits for the owner's confirmation of
timing (PG-008). Channels in scope are exactly two: Claude Code and Codex skill
ZIPs, free, local-only (ADR-0010). Do not extend this copy to MCP registries or
app directories.

Copy is bound to `EXECUTIVE_OVERVIEW.md` in the SIS repository at tag v0.70.0
(the file marks itself authoritative for positioning and claims). Every claim
below names its source in the table at the end. A claim without a source must be
removed or sourced before publishing.

## Short description (one line)

Check or install a verified `sis` CLI, then scan, triage, query and index
untrusted documents locally with PayloadGlass SIS. Free. Nothing is uploaded.

## Long description

The SIS agent skills teach your coding agent to use the `sis` command-line
scanner, the analysis engine behind PayloadGlass, on files that live on your
machine. They run `sis` locally, keep the machine-readable report, and tell you
what SIS found, what it could not examine, and what it refused to do.

What you can ask for:

- set up: find `sis`, check its version, and, only if you approve, download the
  official release, verify its checksum and build attestation, and unpack it;
- scan a file or folder and keep the JSON report;
- triage a report into a short, evidence-backed summary;
- compare a default and a deep analysis of one suspicious file;
- query one file or saved report for specific findings (needs `sis` 0.71.0 or newer);
- build and search a local corpus index, and evaluate a folder of samples.

What it does not do:

- **Nothing is uploaded and there is no hosted service.** The skills run `sis` on
  your machine against local files. The skills and SIS send no telemetry.
- **A clean result does not show a file is safe.** SIS records evidence and what
  it could and could not examine; the skills keep coverage gaps, omissions and
  refusals in every summary.
- **It never opens or runs your samples.** Agents are told not to execute, render
  or open them.
- It does not install anything without your approval, and it will not run a
  binary that fails verification.

SIS is prerelease software (pre-1.0): output fields, finding kinds and verdicts can
change between minor versions. SIS itself is distributed as compiled binaries from
`github.com/payloadglass/sis-release`; this repository holds the skills only.

## Requirements (state these, do not hide them)

- An agent host that runs on a machine you control and can execute a local binary
  (Claude Code, Codex CLI or a comparable local agent).
- A platform SIS ships for: Linux x86_64 or aarch64 (glibc 2.36 or newer), macOS
  (Apple Silicon or Intel), Windows x86_64.
- `sis` 0.70.0 or newer (0.71.0 or newer for the query skill), or permission for
  the setup skill to fetch it from GitHub.
- The GitHub CLI (`gh`) is recommended: it is what verifies the build attestation.
  Without it the setup skill says release provenance is **not** verified.
- **Hosted agent sandboxes that cannot download or run a native binary are not
  supported.** The skills do not fall back to uploading your file to a service.
  (How common that limit is on each host is the pending measurement in
  `docs/hosted-sandbox-protocol.md`; this requirement text stays regardless.)
- macOS note, SIS 0.70.0: `sis sanitize release` does not start its worker on macOS
  and refuses. Scanning and the other skills are unaffected.

## Install: Claude Code

```text
/plugin marketplace add payloadglass/sis-agent-skills
/plugin install sis-agent-skills@sis-agent-skills
```

Then ask: "Check whether `sis` is installed and verified." Pin to a tagged
release when one exists, and compare the `SHA256SUMS` published with it.

## Install: Codex

Download the pack ZIP (or one skill ZIP) and `SHA256SUMS` from the repository's
GitHub release once it exists, check the ZIP against `SHA256SUMS`, and unpack it
into your Codex skills directory (project-local `.agents/skills/` or your
user-level skills directory). Review the scripts before installing: agent skills
can contain executable code.

## First run

1. "Check whether `sis` is installed and verified." The setup skill reports the
   path and version, and stops there if it is current.
2. If it is missing or too old, it asks before downloading anything and shows what
   it will fetch. It refuses a file that fails the checksum or attestation check.
3. "Scan `./suspicious.pdf` with SIS." The scan skill runs a bounded local scan and
   keeps `report.json`.

## Claim bindings

| Copy | Source |
|---|---|
| "the analysis engine behind PayloadGlass"; `sis` as the CLI name | Overview section 2.3: PayloadGlass master brand, SIS permanent engine identity, `sis` permanent CLI; "Powered by the SIS analysis engine" |
| analyses files on your machine; nothing uploaded | Overview section 2.2: local-first means untrusted file content is analysed in the user's environment; "The CLI and Guardian run locally or in customer-controlled hosts" |
| clean result does not show a file is safe; keeps coverage gaps | Overview header: "SIS does not prove that content is safe, true, authentic, or completely analysed"; section 3 "prove" definition |
| the CLI scans, queries, explains, reports, in machine-readable form | Overview section 7 table: `sis` CLI is SHIPPING (local native analysis, investigation, reporting, querying, explanation, selected sanitisation, machine output, batch/directory scanning) |
| distributed as compiled binaries; skills repository holds skills only | Overview section 2.1 (compiled artifacts; do not call it open source or source available) |
| prerelease, pre-1.0, output can change between minor versions | **Not in the Overview.** SIS v0.70.0 release notes ("We remain pre-1.0 ... can still change between minor versions") |
| no telemetry | **Not in the Overview.** SIS v0.70.0 release notes ("There is no telemetry") and ADR-0010 (no telemetry that identifies content). Owner: add to the Overview or confirm wording before publishing |
| macOS `sanitize release` known issue | SIS v0.70.0 release notes, "Known issues and limitations" |
| glibc 2.36, platforms, `SHA256SUMS`, attestations | SIS v0.70.0 release notes and release assets; verified with `gh attestation verify` |

Two source problems for the owner: the Overview at v0.70.0 still says the "current
public release line" is 0.6.8 with a 2026-09-20 baseline, so version statements are
sourced from release notes instead; and the two rows marked "Not in the Overview"
need a home there if the Overview is to remain the single source for claims.

## Wording constraints applied

No "open source", "source available" or licence statements; no "safe", "certified"
or "proof"; no raw detector or format counts; no maturity words outside the
sanctioned vocabulary; the single public product name PayloadGlass and the engine
name SIS only; no MCP, app-directory or hosted claim. The copy was run through the
website's claim rules (`scripts/check/claims.mjs`, rule set only, offline).
