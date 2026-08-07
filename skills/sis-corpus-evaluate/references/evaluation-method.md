# Evaluation method

## Regression candidates

Prioritize:

1. known-malicious or suspicious expectation dropping toward Clean, when the
   oracle is authoritative and coverage is comparable;
2. disappearance of stable, correctly driving evidence;
3. new analysis omissions or provider failures;
4. material runtime degradation on the same inputs and options;
5. benign samples moving upward, especially across operational thresholds.

A verdict delta without comparable run identity is configuration drift, not a
confirmed engine regression.

## Hotspots

Hotspots can include top-percentile runtime, repeated parser/decode failures,
large omission populations, unstable verdicts, or high-impact findings with poor
chain or asset context. State the selection rule and population denominator.

## Case-study candidates

Prefer samples that are reproducible, retainable, structurally novel, and driven
by the correct signal. Deduplicate by SHA-256 and compare emitted finding kinds
against existing cases when that corpus is available.

## Finding vocabulary

Use exact kinds emitted by scan JSON. For capability review, build a valid-kind
set from `sis explain-format FORMAT --json` across relevant canonical formats.
Do not use source-code grep as the sole authority because runner- and
analysis-owned kinds may live outside detector source files.

## Ground truth

Record source, authority, date, and uncertainty. Malware-feed membership is
campaign evidence but may not prove every individual file contains a live
payload or should reach a particular SIS verdict.
