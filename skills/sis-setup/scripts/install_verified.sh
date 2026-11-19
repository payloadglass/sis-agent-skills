#!/usr/bin/env bash
# Verify a downloaded sis release archive, then extract it into a NEW directory.
# Never downloads anything, never executes a downloaded script, never touches PATH.
#
# Verification, in order. Any failure refuses and leaves nothing extracted:
#   1. the archive's SHA-256 matches its line in SHA256SUMS;
#   2. `gh attestation verify` passes (needs the GitHub CLI). If `gh` is not
#      installed the attestation is NOT verified; the script then stops with
#      exit 20 unless --accept-unattested is given, which the agent may pass
#      only after the user has been told exactly that and has said yes;
#   3. the archive holds only `sis` / `sis-cdr-worker` (`.exe` on Windows),
#      with no path components.
# Only after all three does it run the extracted `sis --version`.
set -u

repo="payloadglass/sis-release"
archive=""
sums=""
dest=""
accept_unattested=0

usage() {
  cat >&2 <<'U'
usage: install_verified.sh --archive FILE --sums SHA256SUMS --dest NEW_DIR [--repo OWNER/REPO] [--accept-unattested]
exit: 0 verified+extracted, 2 usage, 10 checksum refused, 11 attestation refused,
      12 archive contents refused, 13 extracted binary did not run, 20 attestation unavailable (nothing extracted)
U
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --archive) archive="${2:?missing value for --archive}"; shift 2 ;;
    --sums) sums="${2:?missing value for --sums}"; shift 2 ;;
    --dest) dest="${2:?missing value for --dest}"; shift 2 ;;
    --repo) repo="${2:?missing value for --repo}"; shift 2 ;;
    --accept-unattested) accept_unattested=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) usage; exit 2 ;;
  esac
done
[[ -n "$archive" && -n "$sums" && -n "$dest" ]] || { usage; exit 2; }
[[ -f "$archive" && -f "$sums" ]] || { echo "archive or SHA256SUMS not found" >&2; exit 2; }
if [[ -e "$dest" ]]; then
  echo "refusing: destination $dest already exists; give a new directory so nothing is overwritten" >&2
  exit 2
fi

# 1. checksum -------------------------------------------------------------
if command -v sha256sum >/dev/null 2>&1; then
  actual="$(sha256sum -- "$archive" | cut -d' ' -f1)"
elif command -v shasum >/dev/null 2>&1; then
  actual="$(shasum -a 256 -- "$archive" | cut -d' ' -f1)"
else
  echo "REFUSED: no sha256sum or shasum available, so the checksum cannot be verified" >&2
  exit 10
fi
name="$(basename -- "$archive")"
# SHA256SUMS lines are "<hex>  <filename>"; require exactly one exact filename match.
matches="$(awk -v n="$name" '{ f=$2; sub(/^\*/, "", f); if (f == n) print $1 }' "$sums")"
count="$(printf '%s\n' "$matches" | grep -c .)"
if [[ "$count" != 1 ]]; then
  echo "REFUSED: $name appears $count times in $sums (expected exactly once)" >&2
  exit 10
fi
expected="$(printf '%s' "$matches" | tr 'A-F' 'a-f')"
if [[ "$actual" != "$expected" ]]; then
  echo "REFUSED: checksum mismatch for $name" >&2
  echo "  expected $expected" >&2
  echo "  actual   $actual" >&2
  exit 10
fi
echo "checksum=verified sha256=$actual"

# 2. attestation ----------------------------------------------------------
attestation="not-verified"
if command -v gh >/dev/null 2>&1; then
  if gh attestation verify "$archive" --repo "$repo" </dev/null >/dev/null 2>&1; then
    attestation="verified"
  else
    echo "REFUSED: gh attestation verify failed for $name against $repo" >&2
    echo "  Do not use this file. It may be corrupt, from another repository, or tampered with." >&2
    exit 11
  fi
else
  echo "NOTICE: the GitHub CLI (gh) is not installed, so build provenance was NOT verified." >&2
  echo "  The checksum only shows the file matches SHA256SUMS from the same release page." >&2
  if [[ "$accept_unattested" != 1 ]]; then
    echo "  Nothing was extracted. Install gh, or re-run with --accept-unattested after the user agrees." >&2
    echo "checksum=verified attestation=not-verified"
    exit 20
  fi
fi
echo "attestation=$attestation"

# 3. contents -------------------------------------------------------------
case "$name" in
  *.tar.gz) members="$(tar -tzf "$archive" 2>/dev/null)" || { echo "REFUSED: cannot list archive" >&2; exit 12; } ;;
  *.zip)
    command -v unzip >/dev/null 2>&1 || { echo "REFUSED: unzip is needed to list a .zip" >&2; exit 12; }
    members="$(unzip -Z1 "$archive" 2>/dev/null)" || { echo "REFUSED: cannot list archive" >&2; exit 12; } ;;
  *) echo "REFUSED: unsupported archive type: $name" >&2; exit 12 ;;
esac
while IFS= read -r member; do
  case "$member" in
    sis|sis-cdr-worker|sis.exe|sis-cdr-worker.exe) ;;
    *) echo "REFUSED: unexpected archive member: $member" >&2; exit 12 ;;
  esac
done <<<"$members"
[[ -n "$members" ]] || { echo "REFUSED: archive is empty" >&2; exit 12; }

mkdir -p -- "$dest" || exit 2
case "$name" in
  *.tar.gz) tar -xzf "$archive" -C "$dest" ;;
  *.zip) unzip -q "$archive" -d "$dest" ;;
esac

bin="$dest/sis"
[[ -f "$bin" ]] || bin="$dest/sis.exe"
chmod 0755 "$bin" 2>/dev/null || true
if ! output="$("$bin" --version 2>&1)"; then
  echo "REFUSED: the extracted binary did not run (wrong platform archive?)" >&2
  exit 13
fi
version="$(printf '%s\n' "$output" | head -n 1)"
echo "extracted=$dest"
echo "binary=$bin"
echo "version=$version"
echo "checksum=verified attestation=$attestation"
