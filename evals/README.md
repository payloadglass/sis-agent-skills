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
