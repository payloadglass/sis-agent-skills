#!/usr/bin/env bash
set -euo pipefail

sis_bin="${SIS_BIN:-sis}"
name=""
location=""
index=""
jobs="4"
output_dir=""

while (($#)); do
  case "$1" in
    --name) name="${2:?missing value for --name}"; shift 2 ;;
    --location) location="${2:?missing value for --location}"; shift 2 ;;
    --index) index="${2:?missing value for --index}"; shift 2 ;;
    --jobs) jobs="${2:?missing value for --jobs}"; shift 2 ;;
    --output-dir) output_dir="${2:?missing value for --output-dir}"; shift 2 ;;
    --sis-bin) sis_bin="${2:?missing value for --sis-bin}"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

[[ -n "$name" && -n "$location" && -n "$index" && -n "$output_dir" ]] || {
  echo "required: --name --location --index --output-dir" >&2
  exit 2
}
[[ "$jobs" =~ ^[1-9][0-9]*$ ]] || { echo "--jobs must be a positive integer" >&2; exit 2; }
[[ -d "$location" ]] || { echo "corpus location is not a directory: $location" >&2; exit 2; }

location="$(cd "$location" && pwd -P)"
readarray -t resolved < <(python3 - "$index" "$output_dir" <<'PYRESOLVE'
from pathlib import Path
import sys
for value in sys.argv[1:]:
    print(Path(value).expanduser().resolve())
PYRESOLVE
)
index="${resolved[0]}"
output_dir="${resolved[1]}"
case "$index" in "$location"|"$location"/*) echo "index must be outside corpus location" >&2; exit 2;; esac
case "$output_dir" in "$location"|"$location"/*) echo "output directory must be outside corpus location" >&2; exit 2;; esac
mkdir -p "$(dirname "$index")" "$output_dir"

version="$($sis_bin --version 2>&1 || true)"
started="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
sync_cmd=("$sis_bin" corpus sync "$name" --index "$index" --location "$location" --jobs "$jobs")
set +e
"${sync_cmd[@]}" >"$output_dir/sync.stdout.log" 2>"$output_dir/sync.stderr.log"
sync_exit=$?
status_cmd=("$sis_bin" corpus status "$name" --index "$index")
"${status_cmd[@]}" >"$output_dir/status.txt" 2>"$output_dir/status.stderr.log"
status_exit=$?
set -e
finished="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

python3 - \
  "$output_dir/index-run.json" "$output_dir/index-run.md" "$name" "$location" "$index" "$version" "$jobs" \
  "$started" "$finished" "$sync_exit" "$status_exit" \
  "${sync_cmd[@]}" -- "${status_cmd[@]}" <<'PYJSON'
import json
import re
import sys

(
    output_json,
    output_md,
    name,
    location,
    index,
    version,
    jobs,
    started,
    finished,
    sync_exit,
    status_exit,
    *commands,
) = sys.argv[1:]
separator = commands.index("--")
sync_command = commands[:separator]
status_command = commands[separator + 1 :]
record = {
    "corpus_name": name,
    "location": location,
    "index": index,
    "sis_version": version,
    "jobs": int(jobs),
    "started_utc": started,
    "finished_utc": finished,
    "sync_command": sync_command,
    "sync_exit_code": int(sync_exit),
    "status_command": status_command,
    "status_exit_code": int(status_exit),
}
with open(output_json, "w", encoding="utf-8") as handle:
    json.dump(record, handle, indent=2)
    handle.write("\n")


def md_code(value):
    text = str(value).replace("\r", " ").replace("\n", " ")
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    fence = "`" * max(1, longest + 1)
    return f"{fence}{text}{fence}"


lines = [
    "# SIS corpus index run",
    "",
    f"- Corpus name: {md_code(name)}",
    f"- Location: {md_code(location)}",
    f"- Index: {md_code(index)}",
    f"- SIS version: {md_code(version)}",
    f"- Sync exit: {md_code(sync_exit)}",
    f"- Status exit: {md_code(status_exit)}",
    "",
    "## Status",
    "",
    "`status.txt` contains the exact SIS status output.",
    "",
    "## Constraints",
    "",
    "- A successful command does not by itself prove every item was analysed; review status and sync stderr.",
]
with open(output_md, "w", encoding="utf-8") as handle:
    handle.write("\n".join(lines) + "\n")
PYJSON

if (( sync_exit != 0 )); then exit "$sync_exit"; fi
exit "$status_exit"
