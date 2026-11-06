# Query recipes

## Finding distribution

```bash
sis corpus query NAME --index INDEX \
  --family finding \
  --group kind,severity,confidence \
  --limit 300 \
  --json
```

## Producer or creator families

```bash
sis corpus query NAME --index INDEX \
  --family agent \
  --group role,value \
  --json
```

## Identity reuse

```bash
sis corpus query NAME --index INDEX \
  --family identity \
  --group role,value \
  --json
```

## Coverage gaps

```bash
sis corpus query NAME --index INDEX \
  --family coverage \
  --group kind \
  --json
```

Optional filters, verified on 0.70.0: `--value`, `--role` (observation families
only), `--max-depth`, `--order asc|desc`, `--limit`, `--meta-key` (the
`finding_meta` family). `--value` is an error for the `finding` family. Confirm
them with `--help` before use.

## Cross-sample clustering (version-guarded)

```bash
sis scan CORPUS_DIR --format jsonl-findings > findings.jsonl     # 0.70.0 input shape
sis corpus correlate findings --input findings.jsonl
```

0.70.0 does not say when it skipped input it could not read as a finding line, and
zero clusters can mean "nothing recognised". From sis 0.71.0 `correlate` reads
report-shaped input, refuses with a non-zero exit when it skipped everything, and
`--allow-skips` overrides that for a deliberately partial input. Report accepted
and skipped counts either way.

## Occurrence pivot

```bash
sis corpus occurrences NAME --index INDEX --content-digest BLAKE3
```

A digest occurrence can refer to a root or nested asset. Preserve asset path,
depth, item identity, and snapshot context.

## FN/FP discipline

1. Verify the external ground-truth authority.
2. Reproduce the exact signal cluster.
3. Identify whether the provider ran and coverage was sufficient.
4. Test the proposed discriminator against the closest benign structure.
5. File the earliest causal failure rather than the loudest downstream symptom.
