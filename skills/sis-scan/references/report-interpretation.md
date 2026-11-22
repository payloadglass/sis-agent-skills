# Report interpretation

## Evidence hierarchy

1. Raw SIS JSON fields are observations.
2. SIS verdict and finding descriptions are engine conclusions.
3. Agent explanations are analyst inferences and must be labelled as such.
4. Actions such as quarantine are operator-policy decisions.

## Coverage first

Review `analysis_coverage` before interpreting the absence of findings. Preserve
its state, omissions, and capability identifiers. A report may be partial even
when the verdict is Clean.

## What the labels mean (sis 0.71)

| label | meaning |
|---|---|
| Clean | nothing reached a warning threshold, over the scope stated beside it |
| Anomalous | not fully examined: a coverage statement, not a weaker threat claim |
| Suspicious | warn and require review; a person or policy decides |
| Malicious | evidence of malice |

- A file that sis could not examine (undecodable or undecryptable streams, a
  large unread proportion) reads **Anomalous**, not Clean. In 0.71.0 a PDF with at
  least 25% unread bytes floors to Anomalous
  (`unread_proportion_constrained_analysis`). This is NOT evidence of a threat
  and must not be reported as one; it is also not a pass.
- Encrypted PDFs: streams sis cannot decrypt are recorded as not examined, and no
  finding is built on ciphertext. Report them as unexamined content.
- Do not read Anomalous as "probably fine", and do not block on Suspicious alone;
  a person or policy decides.
- The text report starts with `Verdict: <label> (<confidence>, coverage <state>)`.
  `not computed` is never Clean.
- `--fail-on` ranks labels Clean < Anomalous < Suspicious < Malicious and ranks a
  coverage-withheld Clean as Anomalous. `--fail-on anomalous` is the lowest
  threshold that catches it.
- Omission reasons are typed (for example `stream:decode_failed`,
  `extraction:budget_exceeded`, `extraction:content_unreachable`,
  `interpretation:not_enumerated`, `member:findings_withheld`,
  `detector_cost_excluded`). Quote the reason as emitted; it says what was not
  read. A `detector_cost_excluded` omission means a deep-only detector did not run
  at the default posture.
- Batch entries expose this as `assurance_scope.gaps` and `coverage_withheld`.

## Scoped assurance (never claim safety)

Clean means "nothing found in what sis examined", never "safe". Never claim an
input is safe. Always state the scope (nodes examined, coverage state) and what
was not examined. Absence of findings is not absence of risk.

## Known limitation

On macOS, `sis sanitize release` refuses in 0.70.0 and 0.71.0 (the isolated CDR
worker cannot start). The 0.72.0 release notes say this is fixed; it has not been
re-run for this pack, so report a refusal as a refusal. Scanning, `doctor` and
`sanitize apply` work, and a refusal is never evidence that a file is safe.

Also inspect provider participation, parser failures, timeout markers, recursive
member status, and asset-graph traversal coverage when present. These surfaces
answer different completeness questions and must not be collapsed into one
boolean.

## Finding-kind discipline

Use exact `findings[].kind` values from the report. For format capability checks,
prefer the installed CLI's `sis explain format FORMAT --json` surface. Do not
recall finding names from memory or infer them from prose.

## Batch reports

A batch report is an aggregate over entries. Report:

- total files considered;
- succeeded and failed counts;
- worst verdict as declared by SIS;
- per-entry failures;
- whether an aggregate omission or error hides individual report detail.

Do not assign ground truth from a batch verdict alone.
