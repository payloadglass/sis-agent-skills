# SIS Agent Skills

Portable Agent Skills for using the SIS command-line interface to scan, triage,
analyse, index, hunt, and evaluate hostile document content.

This package is deliberately **CLI-only**. It teaches an agent how to use an
installed `sis` binary and how to interpret SIS JSON without executing or
rendering the analysed artefact. A later release may add typed MCP tools without
changing the role boundaries or output contracts defined here.

## Included skills

| Skill | Purpose |
|---|---|
| `sis-setup` | Detect `sis`, check its version, and (with your approval) install it from the official release after checksum and attestation checks. |
| `sis-scan` | Run bounded single-file or directory scans and preserve machine-readable evidence. |
| `sis-triage` | Turn a SIS report into an operational triage decision with explicit uncertainty. |
| `sis-analyze` | Compare baseline and deep analysis for one sample and produce analyst artefacts. |
| `sis-query` | Run a targeted `sis query` projection (findings, chains, structure, asset selectors) against one file or saved report. |
| `sis-corpus-index` | Build, update, and verify a persistent SIS corpus index. |
| `sis-corpus-hunt` | Query an index for findings, metadata, identities, coverage, and reused assets. |
| `sis-corpus-evaluate` | Evaluate a corpus, compare a baseline, and identify regressions and candidates. |

Each skill is self-contained. Its `SKILL.md` references only files inside that
skill directory so that an individual skill ZIP can be installed independently.

## Requirements

- SIS CLI `0.70.0` or newer on `PATH` (`0.71.0` for `sis-query`), or set `SIS_BIN` to the executable. SIS is prerelease (pre-1.0), so output fields and verdicts can change between minor versions. The `sis-setup` skill checks the version and can install a verified binary.
- Python 3.10 or newer for the deterministic helper scripts.
- A POSIX shell for the corpus index and hunt wrappers.
- Local filesystem access to the artefacts and output directory.

The helper scripts use only the Python standard library and shell built-ins.
They do not upload samples or reports, do not make network requests, and send no
telemetry. `sis-setup` never downloads anything itself: when you approve an
install, the agent fetches the release archive and `SHA256SUMS` with explicit
commands, and the helper only verifies and extracts them.

## Validate the pack

```bash
python3 -I scripts/validate_pack.py
python3 -I scripts/smoke_test.py
```

## Build release ZIPs

```bash
python3 -I scripts/build_release.py --version 0.2.0
```

This produces:

- one complete pack ZIP;
- one independently installable ZIP for each skill;
- `SHA256SUMS` covering every release asset.

The workflow in `.github/workflows/release.yml` runs structural validation,
helper smoke tests, and the same packaging steps. On a `v*` tag it attaches the
generated ZIPs to the GitHub release; on manual dispatch it publishes them as a
workflow artefact only.

## Host installation notes

The directory layout follows the Agent Skills standard: each skill is a folder
with a `SKILL.md` entry point and optional `scripts/`, `references/`, and
`assets/` directories.

- **OpenAI/ChatGPT/Codex:** upload one of the per-skill ZIPs generated under
  `dist/skills/`, or install the complete pack where the host supports multiple
  skills in one package.
- **Claude Code:** the mirror-ready marketplace manifest is
  `.claude-plugin/marketplace.json`. Register the package root as a local or
  GitHub marketplace and install the `sis-agent-skills` plugin.
- **Repository-local agents:** copy or link the desired skill directories into
  the host's repository skill directory.

## Safety model

SIS analyses hostile content. Agents using these skills must:

- never execute, render, preview, or open an untrusted sample in its native app;
- use SIS JSON as the evidence source rather than scraping human output;
- report analysis coverage and omissions before drawing negative conclusions;
- separate observed evidence, SIS-derived conclusions, and analyst hypotheses;
- require explicit confirmation for deletion, quarantine, upload, or sharing;
- avoid placing raw secrets or sensitive sample content in summaries.

See `SECURITY.md` and each skill's local guardrails for the full contract.

## Versioning

The pack is versioned independently of SIS. Compatibility is declared in
`compatibility.json`; individual skill frontmatter also states its runtime
requirement. CLI contract changes require a pack compatibility update and a
release note.
