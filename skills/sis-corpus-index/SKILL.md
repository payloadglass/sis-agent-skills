---
name: sis-corpus-index
description: "Build, incrementally update, verify, and document a persistent SIS corpus forensic index. Use when an agent must index a directory, sync new or changed items, choose index and corpus identities, inspect status, or diagnose indexing gaps. Do not use to hunt an already-built index or to evaluate detector quality; use sis-corpus-hunt or sis-corpus-evaluate."
compatibility: "Requires SIS CLI 0.6.6 or newer with the corpus command surface enabled."
metadata:
  version: "0.1.0"
  runtime: "cli"
  role: "corpus-engineer"
---

# SIS Corpus Index

Create and maintain a persistent SIS corpus index without confusing admission,
scan success, occurrence count, and distinct content count.

## Inputs

- stable corpus name;
- corpus directory;
- index database path outside the corpus;
- bounded job count;
- optional prune or manifest policy supported by the installed CLI.

## Procedure

1. Verify SIS version and `sis corpus sync --help`.
2. Confirm the corpus and index paths are distinct; never index the index itself.
3. Record corpus name, location, index path, SIS version, and command options.
4. Run an incremental sync.
5. Run corpus status immediately after sync.
6. Report admitted items, occurrences, observations, failed items, and any stale or
   incomplete state exactly as the installed CLI exposes them.
7. Preserve the sync and status logs.
8. Do not interpret corpus labels or malware ground truth in this role.

Preferred helper:

```bash
scripts/sync_index.sh \
  --name reference \
  --location /srv/corpora/reference \
  --index /srv/indexes/reference.sis.db \
  --jobs 8 \
  --output-dir reports/sis-corpus-index/RUN_ID
```

See [references/index-operations.md](references/index-operations.md) for the
identity and completeness model.

## Required output

- `sync.stdout.log` and `sync.stderr.log`;
- `status.txt` and `status.stderr.log`;
- `index-run.json` with paths, version, timestamps, commands, and exit codes;
- a human summary based on [assets/index-run.md](assets/index-run.md).

## Guardrails

- Keep the index outside the indexed directory.
- Do not silently skip unreadable files; preserve per-item failures.
- Do not describe `sync` success as complete analysis without checking status.
- Do not conflate paths, items, occurrences, snapshots, or content digests.
- Do not delete or prune without explicit operator intent and installed-CLI help
  confirming the exact flag semantics.
- Treat extracted metadata and filenames as sensitive, attacker-controlled data.
