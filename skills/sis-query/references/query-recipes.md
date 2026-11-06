# `sis query` recipes and contract notes

Grounded in `docs/builtin/query.md` and `sis query --help`/`--describe` on the
installed build. When the installed build disagrees with this file, trust the
installed build — run `sis query --describe` and `sis query --contract-version`
first and defer to their output.

## Command shape

```bash
sis query findings sample.html --format json
sis query sample.html                              # bare file -> findings
sis query findings --path intake --glob '*.html' --format jsonl
sis query findings --from-report report.json --format json
```

`--format` accepts `text`, `json`, `jsonl`, `yaml`/`yml`, `csv`, `dot`;
`--json` is a shorthand for `--format json`. JSON results use
`{ "file", "query", "result", "contract", ... }`; findings are under
`.result[]`.

## The unified language and ported spellings

The query text may be the engine's pipeline grammar directly:

```bash
sis query "items | pdf_swfs | project pdf_swfs" sample.pdf --format json
sis query "items | urls | count urls" sample.pdf --format json
sis query --describe --format json     # every relation, field, operator the build admits
```

Older dotted spellings (`findings`, `swf.count`, `urls.count`, ...) still work,
in two kinds, announced once on stderr: **ported** (answered by the engine; a
`note:` names the native form; `--where`, `--show-lineage`, `--report-verbosity`
and `--chain-summary` are refused with a named reason — use `| where` in the
pipeline) and **not yet ported** (answered by the legacy implementation,
unchanged). Every JSON/JSONL/YAML answer carries `contract: {language, result}`;
fail clearly on a mismatch with the contract you recorded.

## Exit codes and structured errors

Exit 0 is the only success, even when the result is an empty list. A
structured error is printed in EVERY output format as
`result.status == "error"` with `result.error_code`, and the process exits
non-zero:

| Exit | Meaning |
|---|---|
| 0 | success (including an empty, correctly-filtered result) |
| 2 | bad query / report that doesn't parse / mode can't provide the projection (`QUERY_SYNTAX_ERROR`, `REPORT_PARSE_ERROR`, `UNSUPPORTED_IN_REPORT_MODE`, `REQUIRES_REPORT_MODE`, `ASSET_SELECTOR_ERROR`, `QUERY_SCOPE_ERROR`, `PERSISTED_ANALYSIS_REFUSED`) |
| 3 | another execution failure |
| 5 | answered but incomplete (`ENGINE_ANSWER_INCOMPLETE`, a ported spelling): report as incomplete |
| 4 | unreadable report (`FILE_READ_ERROR`) |

Keep stderr diagnostics separate from the result; an empty collection is not
the same thing as an error or an unavailable projection.

## Multi-format namespaces (work on any root format)

```bash
sis query findings sample.html --format json
sis query findings.composite sample.html --format json
sis query chains sample.html --chain-summary events --format json
sis query correlations sample.html --format json
sis query urls sample.html --format json
sis query iocs sample.html --format json
sis query policy.active sample.html --format json
```

`chains` is the general detector-chain surface. Some aggregations are
PDF-specific even though their base namespace is multi-format
(`urls.telemetry`, `iocs.count.unique.by_family`) — expect `QUERY_SCOPE_ERROR`
on another root rather than a silently-empty result.

## Saved-report projections (`--from-report`)

```bash
sis query findings --from-report report.json --format json
sis explain verdict --from-report report.json --json
sis explain members --from-report report.json
sis query shape --from-report report.json --format json
```

- `verdict`/`why`/`tree`/`intent` spellings were REMOVED from `sis query` and
  refuse with `QUERY_REMOVED`. Use `sis explain verdict --from-report` /
  `sis explain members --from-report` instead.
- The input must be one report object, not a JSONL capture, workspace, or
  semantic-snapshot file.
- `--from-report` first validates the report's embedded `semantic_snapshot`
  (version, `source_report_id`/`input_sha256` binding, a recompute of every
  interpretation id) and refuses with `PERSISTED_ANALYSIS_REFUSED` (exit 2)
  rather than silently reading a missing/invalid section as "no analysis."
  Reports from older builds have no such section and must be rescanned.
- If the report's findings were filtered after the scan (`--focused-triage`),
  the query still answers; the result carries a top-level `context` with
  `findings_view: "filtered"`, and stderr notes that answers reflect the
  filtered view.
- Unsupported live-only namespaces return `UNSUPPORTED_IN_REPORT_MODE`.
- `policy.active` is an exception: it always describes the CURRENT process's
  policy, even with `--from-report`. For the report's own original
  provenance, read the report's `policy` field directly.

## PDF-only namespaces (need a live PDF object graph)

```bash
sis query pages sample.pdf
sis query catalog sample.pdf
sis query trailer sample.pdf
sis query 'object 45 0' sample.pdf
sis query xref.sections sample.pdf
sis query revisions.detail sample.pdf --where "meta.revision.anomaly_score >= 4"
sis query actions.chains sample.pdf --chain-summary events --format json
```

On a non-PDF root these fail with a structured `QUERY_SCOPE_ERROR` — inspect
it rather than treating a non-PDF input as a bug. `actions.chains` is the PDF
structural action graph (PathFinder); it is a DIFFERENT surface from the
multi-format `chains`.

## Three-valued `--where`

`--where` supports `==`, `!=`, `>=`, `<=`, substring `contains`, and boolean
`and`/`or`/`not`. There is no `in [...]`, `starts_with`, or bare `<`/`>`.
Quote string literals with single quotes inside the expression.

```bash
sis query findings sample.html --where "severity == 'High'" --format json
sis query findings sample.html --where "confidence == 'Strong' or confidence == 'Certain'" --format json
sis query findings sample.html --where "kind contains 'html:'" --format json
sis query objects sample.pdf --deep --where "provenance == 'objstm:12:0'"
```

**A comparison is true, false, or UNKNOWN — not just true/false.** A subject
whose filtered field was never recorded (a finding with no `severity`, an
object with no `/Filter`) is unknown for EVERY operator, including `!=` and
`contains`, and `not` of unknown stays unknown. An absent number is never
read as `0`: `length < 5` does not match a subject with no recorded length.
`and`/`or` still decide what they can (`false and unknown` is `false`;
`true or unknown` is `true`).

`sis query` EXCLUDES unknown subjects — it neither matches nor counts them as
non-matches. The distinct-subject exclusion count appears as
`"excluded_unknown": <n>` beside `result` in JSON/YAML (present only when
above zero; a per-file field in `--path` batch output too). `--format text`
reports the same number only via a `note:` line on stderr. Read this before
concluding "no X exists" — the real population may instead be "unmeasured
for X."

Metadata keys need the `meta.` prefix (`meta.revision.anomaly_score`); a bare
key is a parse error, not a silent miss, and names the offending text with a
nearest-field suggestion. Numeric fields take numbers, text fields take
quoted strings, boolean-shaped fields (`risky`, `has_doctype`) take `'true'`/
`'false'` as STRINGS, and ordered operators (`<`,`>`,`<=`,`>=`) are numeric
only — a type mismatch is a parse error, not a quiet non-match.

With `--from-report`, `--where` only applies to findings projections and
`chains`; anywhere else it returns `UNSUPPORTED_IN_REPORT_MODE` rather than
being silently ignored.

**A query that WRITES files is stricter**: `/bytes --extract-to`, and the PDF
extraction queries (`js`, `embedded`, `xfa-scripts`, `swf`, `images`) with
`--extract-to` and `--where`, refuse outright (exit 2, nothing written) if
ANY selected subject is unknown — unlike a reporting query, which just
excludes and counts. `/text` prints to stdout and stays a reporting query.

Other consumers decide for themselves and each errs in its OWN restrictive
direction — do not assume `sis query`'s convention generalises: `sis sanitize
plan --asset` treats unknown as matched (planned for removal); `sis extract
--asset` refuses when any selected subject is unknown.

## Asset-path selectors

```bash
sis query '**' bundle.zip --format json
sis query '**/pe:*' bundle.zip --deep --format json        # any PE at any depth
sis query '**/[format=pe]' bundle.zip --format json
sis query '**/[format=ooxml]/text' bundle.zip --format json
sis query '**/[format=pe]/sha256' bundle.zip --format json
sis query '**/[format=pe]/bytes' bundle.zip --extract-to carved --format json
sis query '**/pdf:*/findings' f.zip --format json          # findings on the matched node only
sis query '**/pdf:*' f.zip --explain                        # resolution trace: counts/budget
```

Steps are `format:local` joined by `/`; `*` wildcards either part; `**` is
descendant-or-self; `tag:**` is shorthand for `**/tag:*`. Terminals: `/findings`
(exact node only — widen with `**` for descendants, it is NOT a subtree
projection), `/sha256` (a **Blake3** digest despite the legacy name — read the
algorithm field, don't assume SHA-256), `/summary`, `/views`, `/text`,
`/bytes` (the last two need live materialised bytes; `/bytes` additionally
needs `--extract-to`).

Predicates filter on typed asset fields: `format`, `origin`, `depth`,
`complete`, `analysis_state`, `finding`, polyglot-related fields, etc. — e.g.
`**/[format=pe]`, `**/zip:*[depth>2]`. A predicate on a field a node never
recorded is unknown for `=`/`!=` alike (same three-valued rule as `--where`),
not a match — the node is excluded and `excluded_unknown` carries the count;
`--explain` reports it too. A `format`/`observed_format`/`format_family`
literal that isn't a known value (a typo, an unidentified format) is a parse
error (`ASSET_SELECTOR_ERROR`, exit 2), not an empty result — select the
"not yet identified" population with `[format_state=text]` instead of
`[format!=X]` when that's really what's meant. See `sis docs asset-graph` for
the full grammar and node-attribution rules.

## PDF streams and the REPL

```bash
sis query 'stream 8 0' sample.pdf --decode
sis query 'stream 8 0' sample.pdf --raw --extract-to streams
sis query 'stream 8 0' sample.pdf --hexdump
sis query repl sample.pdf
```

Quote the whole `stream OBJ GEN` / `object OBJ GEN` query as one argument.
Choose exactly one of `--raw`, `--decode` (default), `--hexdump`. The PDF-only
REPL parses once and caches detector results across the session — it is not a
general multi-format shell.

## Introspecting the installed build

```bash
sis query --contract-version   # "language=N result=M" this build speaks
sis query --describe           # relations, fields, operators, enum domains, value states
```

Run these before relying on a specific field/relation name existing, and
before comparing two query results produced by builds that might differ.
