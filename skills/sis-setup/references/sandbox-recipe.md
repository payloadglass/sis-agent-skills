# Recipe: scan untrusted files inside an OS sandbox

`sis scan` never executes the file it reads, but it does parse hostile bytes, and a
parser bug in any program is a way in. An operating-system sandbox around one run of
sis limits what such a bug could reach: no network, the input read-only, one writable
output directory. The scanner does not sandbox itself. This recipe makes the wrapper
config with the installed binary and leaves running it to the user.

Requires sis 0.72.0 or newer (`sis sandbox config` is not in 0.71.0). Check with
`sis sandbox config --help`; if the subcommand is missing, say so and stop.

## Rules

1. **Call `sis sandbox config --for <wrapper>`; never write or paste a config by hand
   or from memory.** The command quotes paths for the wrapper, refuses names the
   wrapper cannot carry, and prints what the config does and does not enforce. A
   config saved in a file or a chat message goes stale: regenerate it per run.
2. **The command prints; it does not run.** Show the user the config, then run it
   only with their go-ahead, the same way as any other command that writes files.
3. **Never run `sis sandbox eval` outside an OS sandbox.** `sis sandbox eval`
   EXECUTES the file's JavaScript in an embedded interpreter inside the sis process,
   which is not an operating-system sandbox. It is never needed for a scan and no
   SIS skill runs it. If the user asks for it, run it only through a wrapper from
   this recipe, on a machine without credentials, and say it is dynamic analysis.
4. **A sandbox is a limit on a parser bug, not a statement about the file.** Do not
   describe a sandboxed Clean scan as safe; report the verdict with its scope and
   what was not examined, as `sis-scan` does.

## Pick the wrapper for the platform

| Platform | Use | Notes |
|---|---|---|
| Linux, bubblewrap installed (0.8 or later) | `--for bwrap` | No memory/CPU/process limits of its own: run it under `systemd-run --user --scope -p MemoryMax=...`, or use `systemd` |
| Linux with a systemd user manager | `--for systemd` | Adds `MemoryMax`, `CPUQuota`, `TasksMax` and a syscall allow-list; needs unprivileged user namespaces |
| Linux or macOS with a container engine and an image you trust | `--for podman` (rootless, preferred) or `--for docker` | `--image` is required and is not guessed: the image must provide `sis` on `PATH`, or pass `--sis-bin` with its path inside the image |
| macOS | `--for macos` | `sandbox-exec`, which Apple has deprecated; it may stop working in a future macOS |
| Windows (Pro, Enterprise or Education) | `--for windows-sandbox` | Preview, not yet verified; `--sis-bin` is the Windows path of `sis.exe` |

Detect the platform with `uname -s` (Linux, Darwin; on Windows, use the PowerShell
steps) and probe for the wrapper (`command -v bwrap`, `command -v systemd-run`,
`command -v podman`). Prefer the first row that matches. If none is available, say
that no OS sandbox is available on this machine and let the user decide; do not
substitute a hand-written wrapper.

## Verification status

What the sis 0.72.0 release was exercised on, from the project's live runs. Treat
"not verified" as a statement about the project's testing, not about your machine.

| Wrapper | Status |
|---|---|
| bwrap | verified live (Linux) |
| systemd | verified live (Linux) |
| podman | verified live (Linux, rootless) |
| docker | verified live on Linux with SELinux enforcing, using the relabelled mounts; read the config header, which says whether your build relabels |
| macos | verified live (macOS); `sandbox-exec` is deprecated by Apple |
| windows-sandbox | preview, not yet verified |

## Generate and run

```bash
mkdir -p NEW_OUTPUT_DIR
sis sandbox config --for bwrap --input SAMPLE --output NEW_OUTPUT_DIR > sis-sandbox.sh
sed -n 1,4p sis-sandbox.sh      # read the header before running anything
sh sis-sandbox.sh               # the report is written to NEW_OUTPUT_DIR/report.json
```

`--input` (a file or directory) is mounted read-only; `--output` is the only
directory the run may write and must already exist. Put it outside the scanned
directory. After `--` you may give your own sis arguments; `{input}` and `{output}`
become the in-sandbox paths. The default is `scan {input} --emit json={output}/report.json`.
`--memory` (default 4G), `--cpu-percent` (default 100) and `--pids` (default 256) set
limits where the wrapper has them. For macOS save the profile as `sis.sb`; for
Windows Sandbox save it as `sis.wsb`; both print how to start them in the header.

Use the report that lands in the output directory as the scan's raw report
(`sis-scan` preserves it unchanged). Exit codes from the wrapper are the wrapper's:
a non-zero exit with no `report.json` is a failed run, not a clean scan.

## Read the header

Line 1 is `sis-sandbox-config/1 target=<wrapper> sis=<version>`: the format
identifier and the sis version that printed it. Compare it with the binary you are
about to run; if they differ, regenerate.

Line 2 starts `# Enforces:` and lists what the wrapper confines. Line 3 starts
`# Does NOT enforce:` and lists what it leaves open (for example: bwrap sets no
memory limit, `/usr` stays readable; macOS leaves file names and sizes readable; docker
and podman trust the image you named). Report both lines to the user in your own
words, and do not claim a protection the "Does NOT enforce" line excludes. Line 4
points to `sis docs sandbox`, which has the per-wrapper table.

## When it fails

- A path the wrapper cannot carry safely (a control character, `%` for systemd and
  Windows Sandbox, `,` for docker and podman) is refused with the reason: copy the
  file to a plainly named path and retry. Do not strip the check.
- `--image is required`: ask the user which image they trust; never invent one.
- A wrapper that cannot start (no user namespaces, SELinux denying a mount, no
  engine running): report the error as it is. Do not fall back to an unsandboxed scan
  without the user saying so.
