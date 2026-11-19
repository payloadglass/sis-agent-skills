# Triage method

## Priority

Use business context and evidence together. A default technical ordering is:

1. P0: credible active-execution, payload, persistence, or exfiltration evidence;
2. P1: suspicious multi-signal chains, incomplete analysis on a high-risk asset,
   or a material nested-member verdict;
3. P2: contextual anomalies, low-confidence observations, or follow-up hygiene.

Do not convert severity directly into incident priority without delivery and
asset context.

## Coverage constraints

Anomalous (sis 0.71) means "not fully examined", for example undecodable or
undecryptable streams or a large unread proportion. It is a coverage statement,
not evidence of a threat: report it as unexamined content, do not call the file
malicious, and do not call it clean. State which omission reasons
(`analysis_coverage.omissions[].reason_id`) apply.

A coverage omission can itself justify escalation when the missing capability is
material to the threat hypothesis. State the capability, skip/failure reason,
and whether a deep or differently configured scan could address it.

## Evidence independence

Multiple findings may be projections of the same underlying object or signal.
Do not count duplicated descriptions as independent corroboration. Prefer
explicit chain, source, evidence-span, and asset relationships from the report.

## Negative conclusions

Use wording such as:

- "No matching finding was emitted in the analysed content."
- "The report does not establish execution."
- "Analysis was partial because …"

Scoped assurance (ADR-0011): Clean means nothing was found in what sis
examined. Never claim safety; always say what was not examined.

Avoid "clean", "safe", or "benign" as analyst assertions unless supported by
both complete analysis and trusted external context.
