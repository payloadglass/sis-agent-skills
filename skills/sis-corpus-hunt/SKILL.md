---
name: sis-corpus-hunt
description: "Hunt an existing SIS corpus index for finding distributions, metadata, identities, coverage gaps, bindings, or repeated embedded assets. Use when an agent must find similar samples, count exact SIS finding kinds, pivot on producer or creator families, locate a content digest, or extract an indexed asset. Do not use to build the index or claim ground truth from corpus membership."
compatibility: "Requires SIS CLI 0.70.0 or newer with corpus query, occurrences, and optional extract surfaces."
metadata:
  version: "0.2.0"
  runtime: "cli"
  role: "threat-hunter"
---

# SIS Corpus Hunt

Query a pre-built SIS forensic index reproducibly. State the aggregation unit and
filters so counts cannot be mistaken for unique files or unique content.

## Typical questions

- Which finding kinds occur most often in this corpus?
- Which producer or creator families co-occur with a signal?
- Where does this content digest occur at any nesting depth?
- Which analysis capabilities are commonly omitted?
- Can an indexed nested asset be safely re-materialized for further scanning?

## Procedure

1. Confirm corpus name and index path.
2. Check `sis corpus query --help` on the installed version.
3. Choose one evidence family and explicit grouping fields.
4. State filters, maximum depth, order, limit, and aggregation semantics.
5. Run with `--json` and preserve the query result unchanged.
6. Separate counts of items, occurrences, and distinct content.
7. For a content digest, use `occurrences`; use `extract` only when the installed
   CLI reports a supported materialization class and the output path is safe.
8. Validate every cited finding kind directly from query or scan output.

The generic query wrapper is:

```bash
scripts/query_index.sh \
  --name corpus-name \
  --index /srv/indexes/corpus.sis.db \
  --family finding \
  --group kind,severity,confidence \
  --limit 100 \
  --output reports/sis-corpus-hunt/HUNT_ID/result.json
```

Use [references/query-recipes.md](references/query-recipes.md) for supported
query patterns and FN/FP discipline.

## Version-guarded notes

- `sis corpus extract NAME --index INDEX --location DIR --source KEY --asset-path PATH --out FILE`
  needs the corpus location as well as the indexed address.
- **Cross-sample clustering (`sis corpus correlate ...`).** In 0.70.0 the
  `findings` reader accepts `{path, finding}` lines (`sis scan --format
  jsonl-findings`) and can report zero clusters for input it did not recognise, so a
  zero is not "nothing shared". From **sis 0.71.0** `correlate` reads report-shaped
  input and exits non-zero when it skipped everything; `--allow-skips` accepts a
  partly unreadable file and the skips must then be reported. Always state how many
  inputs were accepted and skipped.

## Required output

- exact command and SIS version;
- raw JSON query result;
- aggregation unit and filters;
- concise findings with counts and uncertainty;
- reproducible next pivots using [assets/hunt-report.md](assets/hunt-report.md).

## Guardrails

- Corpus membership is not sufficient ground truth.
- Malware feeds may contain lures, corrupt files, duplicates, or mislabels.
- Always test a proposed malicious discriminator against a benign cousin.
- Do not infer unique samples from occurrence counts.
- Do not extract or share bytes without explicit purpose and authorization.
- Never execute an extracted asset.
