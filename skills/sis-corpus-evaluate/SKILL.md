---
name: sis-corpus-evaluate
description: "Evaluate a corpus with SIS, compare a previous batch report, identify verdict or finding regressions, surface scan errors and coverage changes, and rank evidence-backed follow-up candidates. Use for release evaluation, detector calibration, corpus baselines, regression spotting, and case-study candidate generation. Do not use for merely syncing an index or hunting one known value."
compatibility: "Requires SIS CLI 0.6.6 or newer with directory scan JSON emission."
metadata:
  version: "0.1.0"
  runtime: "cli"
  role: "corpus-evaluation-engineer"
---

# SIS Corpus Evaluate

Run a reproducible corpus evaluation and preserve enough identity to compare it
with a baseline. A corpus label is an oracle claim to assess, not an unquestioned
truth source.

## Inputs

- corpus directory;
- output root and optional run identifier;
- optional prior SIS batch JSON report;
- optional deep mode requested explicitly;
- external ground-truth source and authority, when available.

## Procedure

1. Record SIS version, corpus path, run ID, mode, and timestamps.
2. Run one directory scan with JSON side output.
3. Preserve stdout, stderr, and raw batch JSON.
4. Record files considered, successful/failed entries, verdict distribution,
   coverage changes, and runtime data exposed by the report.
5. If a baseline is supplied, compare by stable path or digest and identify:
   - verdict label changes;
   - score deltas when both reports expose scores;
   - finding-kind additions/removals;
   - coverage and omission changes;
   - new scan failures or recoveries.
6. Rank regressions by operational impact and evidence authority.
7. Rank case-study candidates only after confirming novelty, provenance, correct
   driving signal, and benign-cousin behavior.
8. Emit the contracted files even when some corpus entries fail.

Run:

```bash
python3 scripts/evaluate_corpus.py CORPUS_DIR \
  --output-root reports/sis-corpus-evaluate \
  --baseline previous-batch-report.json
```

See [references/evaluation-method.md](references/evaluation-method.md) for
regression and candidate criteria.

## Required output

Under `OUTPUT_ROOT/RUN_ID/`:

- `batch-report.json`;
- `sis.stdout.log` and `sis.stderr.log`;
- `summary.json` and `summary.md`;
- `hotspots.json`;
- `errors.json`;
- `regressions.json`;
- `case-study-candidates.md`.

Use [assets/evaluation-summary.md](assets/evaluation-summary.md) for manual work.

## Guardrails

- Continue after per-entry failures when SIS produces a batch report.
- Do not call every feed sample malicious without checking oracle authority.
- A right verdict via the wrong signal is a defect, not a baseline to preserve.
- Test proposed FN fixes against benign cousins before recommending calibration.
- Never invent finding kinds or silently normalize changed kind names.
- Keep run identity and options with every comparison.
