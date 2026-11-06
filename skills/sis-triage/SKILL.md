---
name: sis-triage
description: "Triage an existing SIS JSON report into an operational, evidence-backed summary. Use when an agent must explain a SIS verdict, rank analyst attention, identify material findings and nested assets, expose coverage gaps, or recommend the next bounded action. Do not use to run a new scan unless the report is absent; use sis-scan for acquisition and sis-analyze for deep single-sample investigation."
compatibility: "Consumes SIS JSON reports produced by SIS CLI 0.70.0 or newer."
metadata:
  version: "0.2.0"
  runtime: "cli"
  role: "soc-triage-analyst"
---

# SIS Triage

Turn an existing SIS report into an operational triage record without adding
unsupported certainty. The raw report remains the evidence source.

## Inputs

- a SIS JSON report;
- optional ticket context, business criticality, and known delivery source;
- optional output directory.

When no report exists, use `sis-scan` first and then return here.

## Procedure

1. Verify that the JSON is a SIS report or batch report.
2. Preserve its digest and path; never rewrite the evidence file in place.
3. Read coverage, omissions, failures, and member-analysis status before findings.
4. Record verdict, score, confidence, profile, and engine version when present.
5. Rank material findings using the report's own severity and confidence values.
6. Map findings to root or nested assets using object references, finding IDs,
   asset paths, and the asset graph when available.
7. Distinguish four layers:
   - **observed evidence**: report fields and evidence spans;
   - **SIS conclusion**: findings and verdict;
   - **analyst hypothesis**: interpretation not asserted by SIS;
   - **operator action**: quarantine, block, escalate, or allow.
8. Recommend the smallest justified next action and state what could change it.

Use [references/triage-method.md](references/triage-method.md) for priority and
uncertainty rules.

## Deterministic report rendering

```bash
python3 scripts/render_triage.py REPORT.json \
  --output-dir reports/sis-triage/CASE_ID
```

The renderer extracts observed fields and leaves hypotheses explicitly blank. It
is not a substitute for analyst reasoning.

## Required output

- `triage.json`: normalized observed facts and prioritized finding summaries;
- `triage.md`: operator-readable triage record;
- the original report path and SHA-256;
- prioritized actions labelled P0, P1, or P2;
- an explicit coverage constraint section.

Use [assets/triage-report.md](assets/triage-report.md) for manual work.

## Guardrails

- Never call an artefact safe solely because the verdict is Clean.
- Never hide omissions to make the conclusion simpler.
- Never infer campaign attribution, intent, or exploitability from a finding
  name alone.
- Never invent finding kinds, object references, or asset paths.
- Do not expose raw secrets, full payloads, or unnecessary sensitive metadata.
- Require confirmation before any destructive or external action.
