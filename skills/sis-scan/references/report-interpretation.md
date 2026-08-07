# Report interpretation

## Evidence hierarchy

1. Raw SIS JSON fields are observations.
2. SIS verdict and finding descriptions are engine conclusions.
3. Agent explanations are analyst inferences and must be labelled as such.
4. Actions such as quarantine are operator-policy decisions.

## Coverage first

Review `analysis_coverage` before interpreting the absence of findings. Preserve
its state, omissions, and capability identifiers. A report may be partial even
when the verdict is Clean or Anomalous.

Also inspect provider participation, parser failures, timeout markers, recursive
member status, and asset-graph traversal coverage when present. These surfaces
answer different completeness questions and must not be collapsed into one
boolean.

## Finding-kind discipline

Use exact `findings[].kind` values from the report. For format capability checks,
prefer the installed CLI's `sis explain-format FORMAT --json` surface. Do not
recall finding names from memory or infer them from prose.

## Batch reports

A batch report is an aggregate over entries. Report:

- total files considered;
- succeeded and failed counts;
- worst verdict as declared by SIS;
- per-entry failures;
- whether an aggregate omission or error hides individual report detail.

Do not assign ground truth from a batch verdict alone.
