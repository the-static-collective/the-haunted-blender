# ORCHARD-001 · Repo method as an executable experiment

**Status:** experimental, additive, draft. This PR branches directly from `main`. No existing Blender branch, renderer, snapshot, asset, database, or film is modified.

## Question

Can we preserve independently evolving cinematic experiments while a tiny constituted spine discovers *candidate* compositions across their declared contracts?

**Today, only declared graph planning is proven.** The compiler does not clone, checkout, import or invoke registered organs. It does not assert that two stacked Python branches are independent modules, that their adapters exist, or that a scene has rendered.

## Working law

1. Branch names are human navigation. A full pinned commit SHA identifies a proposed body version. No `latest` selector, auto-discovery or automatic branch movement.
2. `CHRONOBODY.md` holds a single strictly parsed, fenced JSON registry. Markdown outside the fence cannot direct execution; unknown fields (including `command`) are refused.
3. Declare exact `requires` and `provides` types; compute dependency closure. Missing inputs yield `HELD`; two producers for one required contract yield `AMBIGUOUS`; a contract cycle yields `REFUSE`. A complete graph yields **`CANDIDATE`**, not `RUNNABLE`.
4. Record stacked branch ancestry overlap explicitly. A child branch often *already includes its parent implementation*; never concatenate overlapping checkouts or load the same library twice without a proved adapter boundary.
5. Every dry-run yields a JSON report of requested output, supplied types, ordered organ IDs + exact SHA pins, missing/ambiguous inputs, ancestry overlap, unverified gates and nonclaims. The CLI adds the SHA-256 of the full registry document.
6. No execution, render, scene admission, media rights, canon, or promotion flows from finding a compatible graph. A separate future reviewed runtime must verify local exact-SHA materialization, Git cleanliness, adapter effects, media rights, and output receipts.

## First crossing

`observer.projection` provides `observer_projection_timeline` and `memory.feedback` requires it. The requested `derived_memory_take` also needs a frozen fictional scene world, camera score, a separately **accepted** moving take, and explicitly authored memory regions.

```sh
python -m unittest discover -s tests -p 'test_orchard_chronobody.py' -v
python -m orchard.chronobody --want derived_memory_take --have frozen_scene_world camera_score accepted_moving_take authored_memory_regions
python -m orchard.chronobody --want derived_memory_take --have frozen_scene_world camera_score authored_memory_regions
```

The first dry-run should return `CANDIDATE` with observer + memory pins and an ancestry-review gate. The second should return `HELD` for `accepted_moving_take` (CLI exit code 1). The test suite also probes duplicate providers, malformed SHA, forbidden command fields, unknown execution modes, repeated organs, and missing registry fences.

## Falsification / next useful proof

- A declared edge is not an API compatibility test. Next, freeze a **synthetic** scene and adapter fixtures under a separate cartridge; prove shape compatibility and explicit source/receipt identity without invoking personal media or external providers.
- Review overlapping branch ancestry and decide whether to use *one stacked checkout* or separately packaged, non-overlapping adapters. A branch head is not inherently an installable plugin.
- Measure an actual cross-organ render only after adapter integration. Keep its produced video separate from the dry-run receipt.
- Compare at least one incompatible or ambiguous crossing against a compatible candidate; treat refusal as an experimentally useful result.
- Main should receive only a spine once the method has survived reviewed tests, not automatic organ promotion.

## Inputs anchored in current draft branches

- Observer Vision: https://github.com/the-static-collective/the-haunted-blender/pull/23
- Memory Feedback: https://github.com/the-static-collective/the-haunted-blender/pull/25
- Object Events: https://github.com/the-static-collective/the-haunted-blender/pull/14
- Visual Dream: https://github.com/the-static-collective/the-haunted-blender/pull/24
- Conceptual precedent, ALEX CHRONOBODY: https://github.com/the-static-collective/ALEX.2/pull/45

Those PRs remain distinct drafts. An Orchard entry is a pointer to their identified experiment, **not** a claim of integration or a request to merge them.
