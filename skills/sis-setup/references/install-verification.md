# Install and verification reference

Source of truth for assets: `https://github.com/payloadglass/sis-release/releases`.
Facts below were checked against release v0.70.0.

## Release assets

Each release has `SHA256SUMS` (lines of `<hex>  <archive name>`) and one archive
per platform. Every archive holds exactly `sis` and `sis-cdr-worker`
(`sis.exe` and `sis-cdr-worker.exe` on Windows).

| Platform | Archive |
|---|---|
| Linux x86_64 (glibc 2.36+) | `sis-vX.Y.Z-x86_64-unknown-linux-gnu.tar.gz` |
| Linux aarch64 (glibc 2.36+) | `sis-vX.Y.Z-aarch64-unknown-linux-gnu.tar.gz` |
| macOS, Apple Silicon and Intel | `sis-vX.Y.Z-universal-apple-darwin.tar.gz` |
| Windows x86_64 | `sis-vX.Y.Z-x86_64-pc-windows-msvc.zip` |

Releases also publish GitHub build attestations for the archives, and a container
image `ghcr.io/payloadglass/sis:vX.Y.Z` (pinned tags only; there is no `latest`).
A container run is an alternative for a host that can run containers; use
`--network none` and mount the sample read-only. This skill does not pull images.

## Detect the platform

```bash
uname -s   # Linux | Darwin
uname -m   # x86_64 | aarch64 | arm64
```

`arm64` on Darwin still uses the universal archive. On Linux, `ldd --version`
should report glibc 2.36 or newer; older systems are not a supported target.

## Linux and macOS

Use `scripts/install_verified.sh` as described in `SKILL.md`. The same checks by hand:

```bash
sha256sum -c --ignore-missing SHA256SUMS          # macOS: shasum -a 256 -c --ignore-missing SHA256SUMS
gh attestation verify ARCHIVE --repo payloadglass/sis-release
tar -tzf ARCHIVE                                  # expect only: sis, sis-cdr-worker
```

`sha256sum -c` prints `ARCHIVE: OK` for a match. `gh attestation verify` exits
non-zero on failure and prints nothing when it succeeds without a terminal.

## Windows (PowerShell, manual)

The helper scripts are POSIX shell. On Windows do the same checks by hand and stop
at the first failure:

```powershell
$a = "sis-vX.Y.Z-x86_64-pc-windows-msvc.zip"
(Get-FileHash $a -Algorithm SHA256).Hash.ToLower()          # compare with the line in SHA256SUMS
Select-String -Path SHA256SUMS -Pattern ([regex]::Escape($a))
gh attestation verify $a --repo payloadglass/sis-release     # skip only if gh is absent; then say provenance is unverified
Expand-Archive $a -DestinationPath NEW_DIR                   # expect only sis.exe and sis-cdr-worker.exe
& NEW_DIR\sis.exe --version
```

The Windows binary is unsigned; SmartScreen may prompt on first launch.

## Why the project installers are not used here

`install.sh` / `install.ps1` are shown as `curl ... | sh` and `irm ... | iex`.
Piping a remote script into a shell runs unreviewed code before any check; this
pack's rule is that nothing is executed until the archive has been verified.
`sis update` replaces the binary in place; this skill cannot show the user the
checks it performs, so it does not use it. A user who wants either may run it
themselves; that is their decision, not something this skill does for them.

## Limits of the checks

- The checksum proves the file matches `SHA256SUMS` fetched from the same release.
  It guards against corruption and mix-ups, not against a compromised release page.
- The attestation ties the archive to a build in `payloadglass/sis-release`.
  It is the check that supports a provenance statement. Without `gh` it is not run.
- Neither check says anything about the files SIS later scans. A clean scan does
  not show a file is safe.

## Version and compatibility

`compatibility.json` at the pack root declares the minimum: 0.70.0 for the scan,
triage, analyze and corpus skills, 0.71.0 for `sis-query`. `scripts/check_sis.sh`
defaults to the former. SIS is prerelease (pre-1.0); minor versions can change
output fields, finding kinds, and verdicts.
