# Analysis method

## Compare posture, not just verdict

Default and deep scans may differ because detectors are cost-gated, parsers expose
additional representations, or budgets change. Attribute each material delta to
the earliest supported cause:

1. recognition or root-format change;
2. analysis coverage or provider participation;
3. new detector evidence;
4. correlation or chain synthesis;
5. adjudication or policy.

Do not assume the first textual difference is causal.

## Strong evidence

Prioritize evidence that is:

- directly tied to a decoded object or nested asset;
- independently corroborated across surfaces;
- reproducible across repeated runs;
- accompanied by complete analysis for the relevant capability.

## Case-study suitability

A sample is a good case-study candidate only when the expected behavior is
justified, the driving signal is the right one, provenance permits retention,
and the sample adds a technique or structure not already represented.

## Failure handling

If deep mode fails, preserve the baseline and describe the missing capability.
If default mode fails but deep succeeds, do not hide the default failure. If both
fail, produce an identity and failure record rather than an invented analysis.
