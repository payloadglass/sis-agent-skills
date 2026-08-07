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

Optional filters exposed by current SIS versions may include `--value`, `--role`,
`--max-depth`, `--order`, and `--limit`. Confirm them with `--help` before use.

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
