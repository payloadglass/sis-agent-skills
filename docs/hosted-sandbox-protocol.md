# Hosted-sandbox measurement protocol

Question (PG-008): can a hosted agent sandbox obtain and run `sis`? ADR-0010 says
a host that cannot is unsupported and the skills must say so rather than degrade
to a hosted path. This file holds the protocol, what is already known from a local
binary, and what only the owner can measure.

## What a local binary tells us (SIS v0.70.0, Linux x86_64)

| Property | Measured |
|---|---|
| Archive size | 37.5 MB (Linux aarch64), 40.9 MB (Linux x86_64), 42.9 MB (Windows zip), 76.0 MB (macOS universal) |
| Extracted size | `sis` 65.7 MB + `sis-cdr-worker` 42.1 MB (108 MB on disk) |
| Dynamic dependencies | `libz`, `libgcc_s`, `libm`, `libc`; highest glibc symbol used on this build: 2.35; release notes state glibc 2.36 or newer |
| Runtime memory | about 34 MB peak resident for a tiny PDF scan (not a bound for large inputs) |
| Needs a network to scan? | No. `env -i sis --version` and scans run with no network access |
| Needs network to install? | Yes: `github.com` release assets (and an attestation lookup via `gh` for provenance) |
| Needs root? | No, extracts and runs from any writable directory |
| Execute permission | Needs a writable, non-`noexec` directory to run an unpacked binary |

Not measured here, because it needs a hosted sandbox: whether outbound access to
`github.com` / `objects.githubusercontent.com` is allowed, whether `gh` exists,
whether the filesystem is `noexec`, disk and memory limits, glibc version, CPU
architecture, wall-clock limits, and whether files can persist between turns.

## Protocol for the owner (per hosted agent product)

Use a benign fixture only. In a fresh session of the hosted agent, ask it to run
these in order and paste raw output; do not ask it to install anything beyond this:

```bash
uname -sm; cat /etc/os-release | head -2; ldd --version | head -1
df -h /tmp "$HOME" 2>&1 | head -5; mount | grep -E ' /tmp | / ' | head -3   # noexec?
curl -sI https://github.com | head -1                                       # outbound reachability
curl -sI https://objects.githubusercontent.com | head -1
command -v gh python3 tar sha256sum
```

Then, with approval, the setup skill's own flow: download, `install_verified.sh`,
`sis --version`, and a scan of a benign file. Record, per product: reachable (y/n)
per host above, install completed (y/n and exit code), `gh` available (y/n),
attestation verified (y/n), scan completed (y/n), and any refusal wording.

## Result table (owner to fill in)

| Hosted product | Date | Outbound GitHub | Executes unpacked binary | `gh` present | Verified install | Scan runs | Notes |
|---|---|---|---|---|---|---|---|
| (none measured) | | | | | | | |

## What the listing says until measured

The listing states the requirement without a prevalence claim: hosted sandboxes
that cannot download or run a native binary are unsupported, and the skills never
fall back to upload.
