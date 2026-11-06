# Skill evaluation cases

`trigger-cases.json` contains positive and negative discovery cases for the
normalized skills. It is intentionally host-neutral: each entry names the expected skill,
a user request, and whether that skill should activate.

A host-specific evaluation harness should verify at least:

1. positive discovery selects the expected skill;
2. negative cases do not select a superficially related skill;
3. the agent chooses JSON output rather than scraping human output;
4. samples are never executed or rendered;
5. coverage omissions remain visible in summaries;
6. mutating actions require explicit confirmation.

The pack validator checks that every skill has both positive and negative cases.

Host-by-host discovery runs follow `discovery-protocol.md` (not yet run).
The setup skill's cases include a user who has no `sis` installed (positive) and an
unrelated package-install request (negative), because install requests are the
most likely confusion.
