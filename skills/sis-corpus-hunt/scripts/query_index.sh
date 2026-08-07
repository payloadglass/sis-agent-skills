#!/usr/bin/env bash
set -euo pipefail

sis_bin="${SIS_BIN:-sis}"
name=""; index=""; family=""; group=""; output=""; limit="100"
role=""; value=""; max_depth=""; order="desc"

while (($#)); do
  case "$1" in
    --name) name="${2:?missing value for --name}"; shift 2 ;;
    --index) index="${2:?missing value for --index}"; shift 2 ;;
    --family) family="${2:?missing value for --family}"; shift 2 ;;
    --group) group="${2:?missing value for --group}"; shift 2 ;;
    --output) output="${2:?missing value for --output}"; shift 2 ;;
    --limit) limit="${2:?missing value for --limit}"; shift 2 ;;
    --role) role="${2:?missing value for --role}"; shift 2 ;;
    --value) value="${2:?missing value for --value}"; shift 2 ;;
    --max-depth) max_depth="${2:?missing value for --max-depth}"; shift 2 ;;
    --order) order="${2:?missing value for --order}"; shift 2 ;;
    --sis-bin) sis_bin="${2:?missing value for --sis-bin}"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

[[ -n "$name" && -n "$index" && -n "$family" && -n "$group" && -n "$output" ]] || {
  echo "required: --name --index --family --group --output" >&2
  exit 2
}
[[ "$limit" =~ ^[1-9][0-9]*$ ]] || { echo "--limit must be a positive integer" >&2; exit 2; }
[[ "$order" == "asc" || "$order" == "desc" ]] || { echo "--order must be asc or desc" >&2; exit 2; }
[[ -z "$max_depth" || "$max_depth" =~ ^[0-9]+$ ]] || { echo "--max-depth must be a non-negative integer" >&2; exit 2; }

mkdir -p "$(dirname "$output")"
cmd=("$sis_bin" corpus query "$name" --index "$index" --family "$family" --group "$group" --limit "$limit" --order "$order" --json)
[[ -z "$role" ]] || cmd+=(--role "$role")
[[ -z "$value" ]] || cmd+=(--value "$value")
[[ -z "$max_depth" ]] || cmd+=(--max-depth "$max_depth")

metadata="${output%.json}.command.json"
stdout_log="${output%.json}.stdout.log"
stderr_log="${output%.json}.stderr.log"
version="$($sis_bin --version 2>&1 || true)"
set +e
"${cmd[@]}" >"$stdout_log" 2>"$stderr_log"
exit_code=$?
set -e
if (( exit_code == 0 )); then
  if ! python3 -m json.tool "$stdout_log" >"$output"; then
    echo "SIS query returned invalid JSON; raw stdout preserved at $stdout_log" >&2
    exit_code=2
    rm -f "$output"
  fi
fi

python3 - \
  "$metadata" "$version" "$name" "$index" "$family" "$group" "$role" "$value" \
  "$max_depth" "$order" "$limit" "$exit_code" "${cmd[@]}" <<'PY'
import json
import sys

(
    output,
    version,
    name,
    index,
    family,
    group,
    role,
    value,
    max_depth,
    order,
    limit,
    exit_code,
    *command,
) = sys.argv[1:]
with open(output, "w", encoding="utf-8") as handle:
    json.dump(
        {
            "sis_version": version,
            "corpus_name": name,
            "index": index,
            "family": family,
            "group": group,
            "role": role or None,
            "value": value or None,
            "max_depth": int(max_depth) if max_depth else None,
            "order": order,
            "limit": int(limit),
            "command": command,
            "exit_code": int(exit_code),
        },
        handle,
        indent=2,
    )
    handle.write("\n")
PY
exit "$exit_code"
