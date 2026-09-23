# Haunted Blender — branch plans index

**Scope:** plans, decisions and test gates only. This branch is based on `main`, not on any experimental organ. Its contents are proposals, not accepted cinematic capability or a merge authority.

| Document | Job |
| --- | --- |
| [Branch ledger](BRANCH_LEDGER.md) | Snapshot of known branches/PR ancestry, with links and explicit gaps; refresh against GitHub before acting. |
| [Plan contract](PLAN_CONTRACT.md) | Reusable format for one bounded experiment on any branch. |
| [Spectral Interaction 001](SPECTRAL_INTERACTION_001.md) | Next executable slice: independent inhabitants → finite shared color/sound field → renderable witnesses. |

## Branch method

1. Maintain **one plans branch** containing independently named `PLANS/<experiment>.md` files and a central index. Do not spawn a separate plans branch for each experiment.
2. Code branches remain independently addressable. A plan points to its *current* source branch/PR and states exact prerequisites; it never copies or merges another branch's implementation.
3. A plan may record new hypotheses, but cannot declare a capability implemented. Move its status only after checking the exact live PR SHA and running the prescribed checks.
4. Branch and test states in the ledger are **time-bounded snapshots**, not synchronized live metadata; check GitHub before any integration.
5. ORCHARD/Chronobody is a separate experiment in pinned composition and source contracts. A plans file does **not** act as a Chronobody registry, accepted capability, runtime import, or permission for auto-merge.
6. Review the plans-only PR independently. If it lands in `main`, future code branches can read the common files without inheriting each other’s code. Existing stacked PR bases are not changed by this plan.

## Tomorrow's testable question

Can two simultaneous inhabitants with independent attention/memory receipts generate a stable, aesthetically useful shared color-and-sound treatment **without exchanging facts, rewriting the scene, or exceeding perceptual/compositing budgets**?

The first slice uses two inhabitants and one short synthetic scene. Later experiments may explore more senses, speech, contradiction and a playable game loop, but those are not claims of this plan.
