---
name: sis-setup
description: "Check whether a usable, verified `sis` CLI is installed and, only with the user's explicit approval, install or update it from the official release with checksum and attestation verification. Use before the first SIS scan on a machine, when `sis` is not found, when another SIS skill reports a version below its minimum, or when the user asks how to install, verify, or update SIS. Do not use to scan, triage, query, or index files; use the other SIS skills once `sis --version` meets the minimum."
compatibility: "Needs a POSIX shell for the helper scripts (Windows: manual PowerShell steps). Network access only for the downloads the user approves; `gh` is optional but needed to verify build provenance. Targets sis 0.70.0 and newer releases."
metadata:
  version: "0.2.0"
  runtime: "cli"
  role: "setup-and-verification"
---

# SIS Setup

Make sure a working `sis` exists and that you know what it is, before any other
SIS skill runs. SIS is a local scanner: it runs on the user's machine against
local files. This skill never routes a file, report, or path to a hosted
service, and SIS has no telemetry. If a host cannot run or obtain a local
binary, say so and stop; do not look for a hosted alternative.

## Use this skill when

- `sis` is not on `PATH`, or another SIS skill says the installed version is too old;
- the user asks to install, update, or verify SIS;
- you are about to run the first scan in a fresh environment.

## Step 1: detect and compare (read-only, no approval needed)

```bash
scripts/check_sis.sh                    # minimum for the scan/triage/corpus skills (0.70.0)
scripts/check_sis.sh --minimum 0.71.0   # what the sis-query skill needs
```

The helper runs `sis --version` and nothing else. Exit codes: `0` usable,
`3` missing, `4` too old, `5` version output not understood. Resolve the binary
from `SIS_BIN` first, then `PATH`. Report the path and the exact version string.
If the exit code is `0`, you are done: continue with the requested skill.
If not, report the problem and go to step 2 only if the user wants SIS installed.

SIS is pre-1.0: output fields, finding kinds, and verdicts can change between
minor versions, so the minimum matters. Never guess an older flag spelling to
work around an old build.

## Step 2: ask before installing

State what you will do and wait for an explicit yes. Say: which release, which
archive for this platform, where it will be extracted (a new directory the user
approves), that files are fetched from `github.com/payloadglass/sis-release`,
and that nothing is added to `PATH` or run until verification passes. Pin the
version (do not take "latest" silently), and prefer the newest stable release the
user names. Without approval, stop after reporting the problem.

Do **not** use the project's `curl ... | sh` or `irm ... | iex` installers, do
not pipe any download into a shell or interpreter, and do not use `sis update`
from this skill: they fetch and replace the binary without the verification
steps below. If the user asks for one of them, explain that this skill does not
do that and offer the verified path.

## Step 3: download, verify, extract (after approval)

Pick the archive for the platform (table in
[references/install-verification.md](references/install-verification.md)). With
the GitHub CLI, download into a new, empty directory:

```bash
gh release download vX.Y.Z --repo payloadglass/sis-release \
  --pattern SHA256SUMS --pattern 'sis-vX.Y.Z-<target>.tar.gz' --dir NEW_DOWNLOAD_DIR
```

(`curl -fLO` of the two release-asset URLs is equivalent. A download is untrusted
data until the next command passes. Never run, source, or `chmod +x` anything in
that directory by hand.) Then verify and extract in one step:

```bash
scripts/install_verified.sh --archive NEW_DOWNLOAD_DIR/sis-vX.Y.Z-<target>.tar.gz \
  --sums NEW_DOWNLOAD_DIR/SHA256SUMS --dest NEW_INSTALL_DIR
```

The helper checks, in order: the archive's SHA-256 against its exact line in
`SHA256SUMS`; the GitHub build attestation (`gh attestation verify ... --repo
payloadglass/sis-release`); that the archive contains only `sis` and
`sis-cdr-worker`. Only then does it extract into the new directory and run
`sis --version`.

| Exit | Meaning | What you do |
|---|---|---|
| 0 | checksum and attestation verified, extracted, binary runs | go to step 4 |
| 10 | checksum missing, duplicated, or mismatched | **Refuse.** Delete the download; say it did not verify. Do not retry with a different file silently |
| 11 | `gh attestation verify` failed | **Refuse.** Say the provenance check failed; do not use the file |
| 12 | unexpected archive contents | **Refuse** |
| 13 | extracted binary will not run | usually the wrong platform archive; report it, install nothing else |
| 20 | checksum ok, **`gh` not installed so provenance is not verified**; nothing extracted | tell the user plainly; offer to install `gh` and re-run, or, only if the user explicitly accepts a checksum-only install, re-run with `--accept-unattested` and record that in your summary |

State plainly in your summary which checks passed. A checksum from the same
release page shows the file is intact and matches that page; it does not show who
built it. Only the attestation does that. Never describe an unattested install as
"verified" without that qualification, and never proceed past a refusal.

## Step 4: confirm

Run the extracted binary by its full path and confirm the version meets the
minimum:

```bash
scripts/check_sis.sh --sis-bin NEW_INSTALL_DIR/sis
```

Then tell the user how to put the directory on `PATH` (or use `SIS_BIN`); do not
edit shell profiles or system directories without a separate approval. Keep
`sis-cdr-worker` next to `sis`: `sis sanitize release` needs it.

## Platforms

Linux x86_64 and aarch64 (glibc 2.36 or newer), macOS universal (Apple Silicon
and Intel), Windows x86_64. On Windows the helper scripts do not apply; follow
the PowerShell steps in the reference. macOS and Windows binaries are unsigned,
so the first launch may show a Gatekeeper or SmartScreen prompt; that prompt is
the user's decision, not yours.

**Known issue in 0.70.0 (macOS):** `sis sanitize release` fails to start its worker
(`Invalid argument (os error 22)`) and refuses; `sanitize plan` and `sanitize
apply` work, and scanning is unaffected. A refusal is never evidence that a file is
safe. Check the release notes of the version you install for the current status.

## Required output

- the detection result (path, exact version, minimum, status);
- if you installed: release tag, archive name, the checksum value, whether the
  attestation was verified or unavailable, destination directory, final
  `sis --version`;
- any refusal, with its exit code, stated as a refusal.

Use [assets/setup-report.md](assets/setup-report.md) for the layout.

## Guardrails

- No install, download, or `PATH` change without explicit user approval of that step.
- Never pipe or redirect a download into `sh`, `bash`, `iex`, or any interpreter.
- Never run a binary before the checksum and attestation checks have passed
  (or the user has explicitly accepted checksum-only, which you then disclose).
- Refuse a binary that fails verification, and say so. Do not offer to bypass a
  checksum or attestation failure.
- Do not scan, open, or upload any sample as part of setup. SIS is local-only.
- Do not claim SIS, or a clean scan, shows a file is safe.
