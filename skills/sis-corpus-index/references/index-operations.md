# Index operations

## Canonical sequence

```bash
sis corpus sync NAME --index INDEX --location DIRECTORY --jobs N
sis corpus status NAME --index INDEX
```

Confirm the installed command syntax with `--help`; do not guess alternate
spellings.

Verified against sis 0.70.0. `sync` also accepts `--manifest corpora.toml` in place
of `--index`/`--location`, `--reports JSONL` to import saved reports, and `--prune`.

## Identity model

Keep these concepts distinct:

- corpus: operator-defined collection identity;
- item: a source artefact admitted to the corpus;
- snapshot: analysis of one item under a particular SIS analysis contract;
- occurrence: one asset at one path/depth in a snapshot;
- content: digest-addressed bytes that may occur in many items.

A content digest count is not a file count. An occurrence count is not a unique
sample count.

## Freshness and currentness

An index can be structurally healthy while snapshots are stale relative to a new
SIS build or analysis contract. Record the installed SIS version and use status
or future migration commands exposed by the installed CLI. Never edit the SQLite
database directly.

## Failures

Per-item failures should not erase successful items. Report the failed population
and retry advice. A zero-result index with failures is not an empty corpus.
