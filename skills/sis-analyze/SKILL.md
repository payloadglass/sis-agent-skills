---
name: sis-analyze
description: "Perform deep, single-sample SIS analysis by preserving a default scan, running a justified deep scan, comparing verdicts, findings, and coverage, and producing analyst-ready artefacts. Use for one suspicious file, parser-boundary investigation, nested asset analysis, or when the user asks what deep mode adds. Do not use for simple acquisition, broad corpus evaluation, or an existing-report-only triage."
compatibility: "Requires SIS CLI 0.6.6 or newer, Python 3.10+, and local filesystem access."
metadata:
  version: "0.1.0"
  runtime: "cli"
  role: "document-malware-analyst"
---

# SIS Analyze

Investigate one sample through reproducible default and deep scans. Preserve both
reports so differences can be attributed to analysis posture rather than memory.

## Inputs

- one local sample path;
- optional claimed password arguments supplied directly to SIS by the operator;
- optional case identifier and analyst context.

## Procedure

1. Record filename, size, SHA-256, and SIS version.
2. Run a default scan and preserve JSON.
3. Run a deep scan and preserve JSON.
4. Compare:
   - verdict label, score, and confidence;
   - finding kinds added or removed;
   - coverage state and omissions;
   - nested-member and asset-graph visibility;
   - detector failure or timeout changes.
5. Inspect the evidence and object/asset references for material new findings.
6. Identify competing hypotheses and state what evidence would distinguish them.
7. Recommend whether the sample is suitable for a regression fixture or case study.

Use the helper:

```bash
python3 scripts/analyze_sample.py SAMPLE \
  --output-dir reports/sis-analyze/SAMPLE_ID
```

See [references/analysis-method.md](references/analysis-method.md) for comparison
and escalation discipline.

## Required output

- `baseline-report.json` and `deep-report.json`;
- stdout/stderr logs for both runs;
- `analysis.json` with sample identity and structured deltas;
- `analysis.md` with evidence, constraints, hypotheses, and actions.

Use [assets/analysis-report.md](assets/analysis-report.md) for manual analysis.

## Guardrails

- Never execute or render the sample.
- Deep mode is not ground truth; it is a different analysis posture.
- A verdict change is a fact to explain, not proof that the higher label is right.
- Validate finding names from the reports or `sis explain-format`; never invent them.
- Treat repeated projections of one signal as dependent evidence.
- Preserve partial results when one scan fails or times out.
- Do not add a regression baseline until the right signal and expected outcome are
  independently justified.
