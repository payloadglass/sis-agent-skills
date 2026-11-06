---
name: sis-query
description: "Run ad-hoc `sis query` projections over an analysed file's findings, structure, and content — a specific finding kind, a chain, an object subtree, a stream, or an asset-path selector. Use when an agent needs a targeted, reproducible projection rather than a full scan or triage verdict, including filtering with `--where`, reading saved reports with `--from-report`, or walking the nested asset graph with a selector. Do not use to run an initial scan (use sis-scan) or to produce an operational triage record (use sis-triage); do not use for corpus-wide hunting across many samples (use sis-corpus-hunt)."
compatibility: "Requires SIS CLI 0.71.0 or newer: the unified `sis query` front door (query contract language >= 2), --describe, --contract-version, and --from-report semantic-snapshot validation."
metadata:
  version: "0.2.0"
  runtime: "cli"
  role: "query-analyst"
---

# SIS Query

Project a specific, reproducible slice of SIS's view of a file — findings,
chains, structure, or content — without re-deriving a verdict by hand. The
query result is the evidence; do not recompute a severity, score, or
classification the result does not already state.

## Use this skill when

- the user asks for a specific finding kind, severity, or chain rather than
  the whole report;
- an automation needs one JSON/JSONL/CSV projection to feed a pipeline;
- the user wants to filter with a predicate (`--where`) or walk the nested
  asset graph with a path selector (`**/pe:*`, `**/[format=pe]/text`);
- the user wants to re-query a saved report (`--from-report`) without
  rerunning detectors;
- the user asks what the installed build's query contract version or
  supported fields are (`--describe`, `--contract-version`).

Use `sis-scan` first when no report or live file access exists yet. Use
`sis-triage` when the task is "turn this report into an operational verdict
record," not "answer one specific question about it." Use `sis-corpus-hunt`
for aggregate questions across many samples in a pre-built index, not one file.

## Preconditions

1. Resolve the executable from `SIS_BIN`, falling back to `sis` on `PATH`.
2. Record `sis --version` and `sis query --contract-version` (language/result
   versions) alongside every result — a query answer is only comparable to
   another run with the same contract. If `--contract-version` is rejected
   (`unexpected argument`), the build predates sis 0.71.0: stop and report the
   version mismatch; do not fall back to guessed spellings. The `sis-setup`
   skill covers checking and updating the binary.
3. Confirm the input path exists and is readable, or that the `--from-report`
   target is a single saved report object (not a JSONL capture, workspace, or
   semantic snapshot file).
4. Never execute, render, preview, or open the queried sample.

## Command shape

The query text is either a legacy spelling (`findings`, `chains`, `pages`, an
asset-path selector) or the engine's own pipeline grammar (a root relation,
then `|`-separated stages). Run `sis query --describe --format json` before
writing a pipeline by hand; do not invent relations or fields.

```bash
sis query findings sample.pdf --format json
sis query findings.high sample.pdf --where "confidence == 'Strong'" --format json
sis query chains sample.pdf --chain-summary events --format json
sis query '**/[format=pe]/sha256' bundle.zip --format json
sis query findings --from-report report.json --format json
sis query "items | urls | count urls" sample.pdf --format json
```

With two positionals the **query comes first**, then the input. A single
positional with no source flag is the file, and the query defaults to
`findings`. With `--path` (batch) or `--from-report`, give only the query
positional.

Use [references/query-recipes.md](references/query-recipes.md) for curated
recipes by namespace (findings, chains, PDF structure, asset-path selectors,
streams) and the exit-code/error-code table.

## Preferred execution

```bash
python3 scripts/run_query.py "findings.high" sample.pdf \
  --where "confidence == 'Strong'" \
  --output-dir reports/sis-query/RUN_ID
```

The helper runs one query, preserves the exact command and raw output, and
records the exit code and any structured error (`error_code`,
`excluded_unknown`) without trying to interpret them further. For
`--from-report`, pass `--from-report PATH` instead of a positional input.

## Interpretation sequence

1. Preserve the raw output exactly; do not reformat or truncate a JSON result
   before quoting it.
2. Check the process exit code first: 0 is the only success. Exit 5
   (`ENGINE_ANSWER_INCOMPLETE`) means "answered, but incomplete": report the
   answer as incomplete, never as complete or empty. A structured
   error (`result.status == "error"` with `result.error_code`) is printed in
   every format and the process still exits non-zero — report the
   `error_code`, don't guess at what it means from prose alone.
3. If the envelope carries `excluded_unknown` (count above zero), that many
   distinct subjects were excluded because a filtered field was never
   recorded for them — report this alongside the result count. It is not the
   same as "zero matches" and it is not an error.
4. Cite finding kinds, chain ids, and object refs exactly as emitted; never
   invent or normalise a name that isn't in the result.
5. An empty result list is a real answer ("nothing matched"), not evidence of
   failure — distinguish it from a non-zero exit, which means the query itself
   did not complete.

Use [references/query-recipes.md](references/query-recipes.md)'s "Three-valued
`--where`" section before interpreting any filtered query — absence is not
`false`.

6. Read stderr: a `note:` line says whether a legacy spelling was ported to
   the engine or answered by the legacy implementation, and a `findings_view:
   "filtered"` context means a saved report's findings were filtered after the
   scan. Quote both with the result.

## Required output

- the exact command, `sis query --contract-version` output, and SIS version;
- the unmodified raw result (JSON/JSONL/CSV/text as requested);
- exit code, and `error_code` + `excluded_unknown` when present;
- a short note on what the query answers and does not answer.

Use [assets/query-report.md](assets/query-report.md) when drafting a manual
summary of a query session with several related queries.

## Guardrails

- `--where` is three-valued (true/false/**unknown**): a subject whose
  filtered field was never recorded is excluded from the result and counted
  in `excluded_unknown`, never silently read as `false` or `0`. Do not say
  "no findings have severity X" when the real answer is "N findings have no
  recorded severity at all."
- Do not recompute a verdict, score, or classification from a query result;
  read the value the model already states. For a saved report's verdict use
  `sis explain verdict --from-report report.json --json` (the `verdict`,
  `why`, `tree` and `intent` query spellings were removed and refuse with
  `QUERY_REMOVED`). If the projection does not state it, say so.
- A query result is one projection, not a scan verdict. An empty or low-count
  result does not show the file is safe; keep coverage and omissions from the
  underlying report visible when summarising.
- On a ported spelling `--where` is refused with a named reason; use the
  engine's own `| where` pipeline stage instead of retrying with other flags.
- Do not invent a field, relation, or finding kind not present in
  `sis query --describe`'s registry or in the result itself.
- `/text` and `/bytes` asset-selector terminals need live materialised bytes;
  `/bytes` additionally requires `--extract-to`. Never execute, render, or
  open bytes extracted this way.
- A query that writes files (`--extract-to`, or a PDF extraction query with
  `--where`) refuses outright if any selected subject is unknown rather than
  silently extracting a subset — treat that refusal as correct behaviour, not
  a bug to route around.
- `policy.active` describes the CURRENT process's policy even under
  `--from-report`; it is not the report's own original policy provenance
  (read the report's `policy` field for that).
- Require confirmation before extracting bytes, writing outside the given
  output directory, or treating a selector's result as safe to open.
