# Security

## Hostile-input posture

All scanned artefacts, extracted members, filenames, metadata, and report text
must be treated as attacker-controlled. Do not execute or render samples. Do not
pass sample-derived text back into a shell. The included scripts invoke `sis`
through argument arrays or quoted shell arrays and write outputs beneath an
explicit destination directory.

## Data handling

The package is local-only and contains no network client. SIS reports can still
contain sensitive metadata, paths, indicators, or excerpts. Store outputs with
permissions appropriate to the source material and do not upload them without
operator approval.

## Mutating actions

These skills do not delete, quarantine, move, upload, or share artefacts. An
agent must obtain explicit confirmation before taking any such action outside
the skill.

## Dependency and update trust

Pin releases or commit SHAs when installing from GitHub. Verify `SHA256SUMS` for
release ZIPs. Review scripts before installation; Agent Skills may include
executable code and therefore form part of the software supply chain.

## Reporting vulnerabilities

Report vulnerabilities privately through the security-reporting mechanism of
the repository that distributes this pack. Do not include live malware or
sensitive reports in a public issue.
