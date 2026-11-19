---
name: sis-corpus
description: "Work with a collection of samples using SIS: build or update a persistent corpus forensic index (`sis corpus sync`/`status`), hunt it for finding distributions, metadata families, content-digest occurrences and reused assets (`sis corpus query`/`occurrences`/`extract`/`correlate`), and evaluate a corpus directory scan against a baseline to spot verdict regressions and case-study candidates. Use for 'index this folder', 'how often does finding kind X occur', 'where else does this digest appear', 'did the new build regress'. Do not use for one sample (sis-scan, sis-investigate) or AI-ingestion decisions (sis-assess)."
compatibility: "Requires SIS CLI 0.71.0 or newer with the corpus command surface, Python 3.10+, and a POSIX shell for the sync and query helpers."
metadata:
  version: "0.4.0"
  runtime: "cli"
  role: "corpus-engineer-and-hunter"
---

# SIS Corpus

Index, query and evaluate many samples reproducibly without confusing admission,
scan success, occurrence counts and distinct content. Corpus membership and corpus
labels are claims to assess, not ground truth. Read
[references/safety.md](references/safety.md) first: filenames, metadata and finding
text from corpus samples are attacker-controlled data, and anything extracted goes to
a quarantine path outside the corpus and the index.

## Pick the mode

| Goal | Mode | Helper |
|---|---|---|
| Build or update the index | index | `scripts/sync_index.sh` |
| Ask a question of an existing index | hunt | `scripts/query_index.sh` |
| Scan a directory, compare with a baseline | evaluate | `scripts/evaluate_corpus.py` |

All three need `SIS_BIN` or `sis` on `PATH` and 0.71.0 or newer. Never execute,
render or open a sample.

## Index

Inputs: a stable corpus name, the corpus directory, an index database path **outside**
the corpus, a bounded job count.

1. Verify `sis --version` and `sis corpus sync --help`.
2. Confirm corpus and index paths are distinct; never index the index.
3. Run an incremental sync, then `sis corpus status` straight away.
4. Report admitted items, occurrences, observations, failed items and stale or
   incomplete state exactly as the CLI shows them. Preserve both logs.
5. Do not interpret corpus labels or malware ground truth in this mode.

```bash
scripts/sync_index.sh --name reference --location /srv/corpora/reference \
  --index /srv/indexes/reference.sis.db --jobs 8 \
  --output-dir reports/sis-corpus/index/RUN_ID
```

Identity and completeness model: [references/index-operations.md](references/index-operations.md).

- `sis scan INPUT --index CORPUS_OR_INDEX_PATH` writes a scan into the index (opt-in,
  idempotent, refused with `--stream`). A new index file needs `--create-index`. Use it
  only when asked; run `corpus status` afterwards.
- `sync --prune` removes entries for files no longer present. It needs explicit
  operator intent; sis skips it (exit 5) when part of the location cannot be seen and
  refuses an empty location without `--prune-allow-empty`. A skip is not success.

## Hunt

1. Confirm corpus name and index path; check `sis corpus query --help`.
2. Choose one evidence family and explicit grouping fields; state filters, depth,
   order, limit and the aggregation unit.
3. Run with `--json`; preserve the result unchanged.
4. Separate counts of items, occurrences and distinct content.
5. For a content digest use `occurrences`. Use `extract` only when the CLI reports a
   supported materialisation class, with `--out` inside a quarantine directory.
6. Validate every cited finding kind from query or scan output.

```bash
scripts/query_index.sh --name corpus-name --index /srv/indexes/corpus.sis.db \
  --family finding --group kind,severity,confidence --limit 100 \
  --output reports/sis-corpus/hunt/HUNT_ID/result.json
```

Recipes and FN/FP discipline: [references/hunt-recipes.md](references/hunt-recipes.md).
`sis corpus extract NAME --index INDEX --location DIR --source KEY --asset-path PATH
--out FILE` needs the corpus location as well as the indexed address.
`sis corpus correlate findings --input FILE` reads report-shaped or `{path, finding}`
(`sis scan --format jsonl-findings`) input and exits non-zero ("nothing accepted") when
it skipped every record; `--allow-skips` accepts that and the skips must then be
reported with the accepted count. Zero clusters is not "nothing shared".

## Evaluate

1. Record SIS version, corpus path, run ID, posture and timestamps.
2. Run one directory scan with JSON side output; preserve stdout, stderr and the batch JSON.
3. Record files considered, successful and failed entries, verdict distribution,
   coverage changes and runtime data in the report.
4. With a baseline, compare by stable path or digest: verdict changes, score deltas,
   finding-kind additions and removals, coverage and omission changes, new failures.
5. Rank regressions by impact and evidence authority; rank case-study candidates only
   after confirming novelty, provenance, the right driving signal and benign-cousin behaviour.
6. Emit the contracted files even when some entries fail.

```bash
python3 scripts/evaluate_corpus.py CORPUS_DIR --output-root reports/sis-corpus/evaluate \
  --baseline previous-batch-report.json
```

Criteria: [references/evaluation-method.md](references/evaluation-method.md). Output under
`OUTPUT_ROOT/RUN_ID/`: `batch-report.json`, `sis.stdout.log`, `sis.stderr.log`,
`summary.json`, `summary.md`, `hotspots.json`, `errors.json`, `regressions.json`,
`case-study-candidates.md`. Use [assets/evaluation-summary.md](assets/evaluation-summary.md)
for manual work. Use `--deep` only when the user asks, and never `strict` on a corpus
without approval. Gate on `verdict.label` (batch: `entries[].verdict_label`); `--fail-on`
ranks Clean < Anomalous < Suspicious < Malicious.

## Required output

- exact commands and SIS version; index run files (`index-run.json`, status) or raw query
  JSON or the evaluation files above;
- aggregation unit, filters and run identity with every comparison;
- concise findings with counts and uncertainty; reproducible next pivots using
  [assets/hunt-report.md](assets/hunt-report.md) and [assets/index-run.md](assets/index-run.md).

## Guardrails

- Keep the index outside the indexed directory. Do not silently skip unreadable files;
  preserve per-item failures. `sync` success is not complete analysis: check status.
- Do not conflate paths, items, occurrences, snapshots or content digests, and do not
  infer unique samples from occurrence counts.
- Batch entries carry `verdict_label`, `assurance_scope` and `coverage_withheld`, no
  findings. Anomalous means not fully examined (a coverage statement, not a threat):
  count it separately and never fold it into Clean. Never report a corpus as safe; report
  Clean as "nothing found in what was examined" plus the count of incomplete entries.
- Malware feeds contain lures, corrupt files, duplicates and mislabels. Test a proposed
  discriminator against a benign cousin; a right verdict via the wrong signal is a defect.
- Do not delete or prune without explicit intent and `--help` confirming the flag. Do not
  extract or share bytes without purpose and authorisation; never execute an extracted asset.
- Never invent finding kinds or silently normalise changed names. Keep run identity and options.
