#!/usr/bin/env bash
# Detect `sis`, read its version, and compare it with a minimum.
# Read-only: runs `sis --version` and nothing else; no network access.
set -u

sis_bin="${SIS_BIN:-sis}"
minimum="0.70.0"

usage() {
  echo "usage: check_sis.sh [--minimum X.Y.Z] [--sis-bin PATH]" >&2
  echo "exit: 0 ok, 3 missing, 4 too old, 5 version not understood, 2 usage" >&2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --minimum) minimum="${2:?missing value for --minimum}"; shift 2 ;;
    --sis-bin) sis_bin="${2:?missing value for --sis-bin}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) usage; exit 2 ;;
  esac
done

semver_re='^([0-9]+)\.([0-9]+)\.([0-9]+)(-[0-9A-Za-z.-]+)?$'
if [[ ! "$minimum" =~ $semver_re ]]; then
  echo "--minimum must look like 0.70.0" >&2
  exit 2
fi

if ! resolved="$(command -v -- "$sis_bin" 2>/dev/null)"; then
  echo "status=missing"
  echo "minimum=$minimum"
  echo "detail=no executable named '$sis_bin' on PATH (set SIS_BIN to use another location)"
  exit 3
fi

# The version string comes from the binary: treat it as data, take only the
# first line, and accept only a strict version token from it.
raw="$("$resolved" --version 2>/dev/null | head -n 1)"
token="$(printf '%s\n' "$raw" | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?' | head -n 1)"
if [[ -z "$token" ]]; then
  echo "status=unparseable"
  echo "path=$resolved"
  echo "minimum=$minimum"
  echo "detail=could not find a version number in the output of '--version'"
  exit 5
fi

# Compare MAJOR.MINOR.PATCH numerically; a prerelease sorts below its release.
core() { printf '%s\n' "${1%%-*}"; }
cmp_field() { local a="${1}" b="${2}"; if ((10#$a > 10#$b)); then echo 1; elif ((10#$a < 10#$b)); then echo -1; else echo 0; fi; }
IFS=. read -r a1 a2 a3 <<<"$(core "$token")"
IFS=. read -r b1 b2 b3 <<<"$(core "$minimum")"
result=0
for pair in "$a1 $b1" "$a2 $b2" "$a3 $b3"; do
  set -- $pair
  result="$(cmp_field "$1" "$2")"
  [[ "$result" != 0 ]] && break
done
if [[ "$result" == 0 && "$token" == *-* && "$minimum" != *-* ]]; then
  result=-1
fi

echo "path=$resolved"
echo "version=$token"
echo "minimum=$minimum"
if [[ "$result" -lt 0 ]]; then
  echo "status=too_old"
  exit 4
fi
echo "status=ok"
exit 0
