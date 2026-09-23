# ORCHARD-002 — Pinned two-organ crossing, synthetic only

**Status: experiment; stacked draft on ORCHARD-001 (#27). Not proposed for main.**

## Research question

Can one exact source of authored fictional occurrence produce *different observer-local projections*, with one observer legitimately retaining previously seen pixels as a bounded afterimage, and another observer never gaining those pixels—while the frozen scene remains byte-identical?

This test advances beyond ORCHARD-001's paper contract: it calls the actual `haunted_blender.observer_local.project`, `memory_feedback._compile_timeline` and `memory_feedback._memory_frames` from two **verified, exact-commit source bodies**. It does not exercise accepted-take admission, a complete FFmpeg MP4 render, or a production scene adapter.

## Stack-resolution finding

Memory Feedback is a **descendant of** Observer-Local Vision in the same repo, not an independent library. In the tested source history the `haunted_blender/observer_local.py` blob is identical at both pinned commits. The crossing therefore:

1. Checks out the exact Observer Vision commit and the exact Memory Feedback commit into independent read-only CI directories.
2. Verifies both HEAD identities, known source Git blob hashes, clean trees, and the observer commit's ancestry of the memory commit.
3. Imports the inherited observer and memory code **once from the verified Memory Feedback checkout**. It does not concatenate or concurrently import two overlapping Python trees.
4. Refuses if the pinned source or inherited observer blob differs.

This proves one *specific stacked composition*, not a general solution for arbitrary branches or providers.

## Synthetic fixture / executable proof

The frozen world has two authored facts: `room` and `figure`. The hallway and threshold camera inspect the **same** world at the same beat and door openness. The threshold camera can see the figure at 60% openness; the hallway camera's access rule requires 80%, so it cannot. After the door closes to 10%, the threshold retains a valid figure-memory receipt. The hallway does not.

The adapter supplies explicitly **drawn, separate synthetic RGB camera frames**, corresponding to each camera's authored visibility. It passes each camera's 4-frame projection timeline and RGB buffer to the real memory-feedback implementation. It records each frame-input digest, each output digest, per-camera projection receipts, memory capture and fade statistics, source identities, frozen-world hash, and nonclaims.

**A valid receipt must show:** identical unchanged world digest for both eyes; different projection identities; threshold capture then decaying visual residue; no hallway figure memory or invented pixel residue; different output-frame digests.

The negative controls must refuse a cross-observer prior receipt, a prior receipt from an altered world, a forged projection digest, and a memory residue with no on-timeline pixel capture. A wrong source checkout must refuse before import.

## Run on a temporary machine or in CI

With the Orchard branch checked out as `orchard-method`, separately materialize the two exact commit IDs shown below as `pinned/observer` and `pinned/memory`, retaining full ancestry in the latter, then run:

```sh
cd orchard-method
PYTHONDONTWRITEBYTECODE=1 python -B -m orchard.observer_memory_probe \
  --observer-checkout ../pinned/observer \
  --memory-checkout ../pinned/memory
```

CI does that exact materialization. The probe refuses dirty or mismatched checkouts and performs no provider or network call itself.

**Observer:** `9beec9cce02f9c595386fc39fd7fb79a890434da`

**Memory:** `6aca64fdeeb458653e20558c4b23fa89ec622ba7`

## Boundaries / next falsification

- This is an API/source crossing in a **single stacked checkout**, not an isolation proof for two independent installed organs. CHRONOBODY's `execution: DISABLED` remains unchanged; the probe is explicitly invoked as a test harness.
- The raw RGB buffers are artist-authored fixture pixels. An authored camera projection is *not* proof that a real optical camera saw or could have seen these pixels.
- The memory experiment's `_memory_frames` is an internal API with no stability promise. A future runtime needs a reviewed, versioned adapter.
- A source branch's commit and blob integrity are not media rights, real-world occurrence, approval, or reproducible external model behavior.
- A CI success does not prove actual accepted moving take → FFmpeg → private output vault → signed release; that remains a separate test.
- The user-facing `main` branch and every preexisting cinematic branch remain unchanged. No automatic promotion. Failure means record the blocker, not silently merge the branches.

## Decision after the proof

If the exact-source/pixel test passes, it demonstrates that a spine-directed crossing can do **useful work** across stacked experiments *without merging their feature branches*. Keep the repo method experimental until at least one genuinely non-overlapping cross-stack adapter, real-media acceptance boundary, and replay/cleanup pressure test are demonstrated.
