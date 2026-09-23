# Reusable plan contract — PLANS/001

Each experiment gets one durable Markdown plan; additional branches and receipts are **references**, not hidden dependencies or copied source. A plan never asserts implementation simply because it has been approved.

## Required fields

| Field | Meaning |
| --- | --- |
| ID and status | `idea`, `approved_plan`, `in_progress`, `tested`, `held`, or `scoped_complete`; scope applies to the *plan*, not the whole product. |
| Goal and non-goals | A falsifiable small outcome and an explicit boundary against expansion. |
| Source pins | Repo, base branch, relevant PRs and **verified SHA at time of execution**. Do not guess future SHAs in the plan. |
| Inputs and outputs | Typed representations, size/time bounds, privacy, rights and provenance restrictions. |
| Invariants | What must remain unchanged; which claims a receipt cannot make. |
| Algorithm and alternatives | Deterministic ordering, budgets, conflict resolution and clearly separated aesthetic choices. |
| Executable proof | Small fixtures, real adapter or renderer output where applicable, and hostile tests. |
| Receipt | Exact source/projection/observer/output digests, scope, parameters, rejections and nonclaims. |
| Gate and next frontier | Pass/fail criteria, what would be ready to review, and what remains speculative. |

## Shared integration laws

- `observed != inferred != remembered != reported != fiction != rendered`. These may affect **presentation** under a typed policy but never silently promote one another into occurrence.
- Keep inhabitant-local attention and memory separate. Shared spectral display is not shared knowledge or consent.
- A source asset, accepted take, authored world and observer receipt stay immutable. Rendered variants get new identities and receipts.
- A proposal, plan, candidate, green test or dry-run is not permission to publish, place footage in a scene, merge a branch or declare product completion.
- Any future plan update should identify what changed relative to the previous plan, with links to actual code PRs and tests. Keep unresolved conflicts visible rather than forcing a universal winner.
