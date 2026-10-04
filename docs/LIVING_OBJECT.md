# N5 — Living Object (independent multi-part foreground composition)

**Experimental, additive**: `experimental/living-object-v0.1` is based on the exact open N4 branch `experimental/contour-material-v0.1`. No N0–N4 implementation, accepted snapshot, or historical renderer is modified. N5 is a 2D executable proof, not the full filmmaking editor or a model of physical object identity.

## New object contract

A living object is a **filmmaker-assigned collection of 2–4 distinct frozen N4 cutout takes**. Each part has a unique name, integer `z` (ascending back-to-front), explicit `delay_frames` (0–24 on the 49-frame timeline), and finite opacity in (0,1]. Its selected source/target polygon and material mode remain *inside its N4 parent*. N5 must not overwrite or reinterpret them. All parts must share the exact same frozen N3 parent, source and target image content hashes, background mode and optional clean-plate original/derivative hashes. Mismatched scene or plate **refuses composition** rather than silently layering unrelated worlds.

The clock for a part starts at its delay and completes on the global final frame:

```text
local_t(frame) = clamp((frame - delay_frames) / (48 - delay_frames), 0, 1)
```

This is deliberately a small independent-clock proof, not arbitrary keyframes, recurrence or physics. Parts may overlap: compositing is deterministic by explicitly unique z-order, and per-frame alpha-footprint plus overlap counts are retained. The receipt distinguishes overlap **of rendered masks** from true spatial occlusion, causal interaction, or physical identity. Reversing z can change which object's texture is visible in the overlap, even with identical source assets.

## Outputs

- **Opaque local MP4:** 320×180, 24fps, 49 frames. Each frame composites *only the independently masked N4 foregrounds* over the shared N4 diagnostic matte or the exact separately cataloged/frozen N4 clean plate. N4's source photograph containing the subject is never silently reused as its clean background.
- **Optional transparent RGBA midpoint PNG:** distinct `--alpha-out` path. This output contains the layered object **without** the opaque background. It is a separately hashed preview of alpha-bearing image material, not a transparent video master.
- **JSON receipt:** content address for the N5 snapshot, each N4 frozen source, explicit z/clock/material settings, output digests, and per-frame local clock, per-layer nonzero-alpha pixel count and layer-overlap count. No subject identity inference or AI-provider call is performed.

Existing outputs and receipt paths are never intentionally overwritten; a process interruption before the receipt may leave unreceipted local outputs, which must be inspected and reconciled manually. The private source archive is not checked into the repository.

## Local exercise

Use N0 to index source photographs; create and freeze N1, N2, N3 and **two distinct N4 recipes based on the same frozen N3 scene**. Select two separate polygons (e.g., the cup body and rim) and their respective material modes in N4. Add the actual frozen N4 snapshot paths returned by their commands to a **private** JSON file such as:

```json
[
  {
    "name": "body",
    "snapshot": "/absolute/path/to/frozen-body-N4.json",
    "z": 0,
    "delay_frames": 0,
    "opacity": 1.0
  },
  {
    "name": "rim",
    "snapshot": "/absolute/path/to/frozen-rim-N4.json",
    "z": 1,
    "delay_frames": 20,
    "opacity": 0.8
  }
]
```

With optional Pillow and FFmpeg installed locally:

```sh
python -m haunted_blender.living_object_cli create ~/HauntedBlender /private/layers.json
python -m haunted_blender.living_object_cli freeze ~/HauntedBlender object-RETURNED_ID
python -m haunted_blender.living_object_cli plan ~/HauntedBlender /absolute/path/to/frozen-N5.json
python -m haunted_blender.living_object_cli render ~/HauntedBlender /absolute/path/to/frozen-N5.json \
  --out ~/HauntedBlender/renders/living-object.mp4 \
  --alpha-out ~/HauntedBlender/renders/living-object-midpoint.png
```

To change z, clock, opacity or layer lineup, write a new input and use `create ... --revises object-PRIOR_ID`. Older accepted snapshots remain unchanged; a revision must retain the same N3 scene.

## Inherited boundaries and next open seam

N5 reuses N4's closed convex contour, local polygon texture warp and EXIF-aware coordinates. The N4 parent verifies its N3 geometry, which in turn verifies N2 landmarks, N1 frozen media bindings and N0 source hashes. N5 does **not** implement multiple contour holes, split/merge topology, local shadow reconstruction, depth sorting or alpha-coded video. Layering two masks does not prove that one object split into two or that two objects physically fused.

**Next candidate (separate experiment):** an explicit `part_birth|part_death|split|join` event graph with declared before/after part IDs, topological transition frames and an independent Dogram-style structural delta receipt. Do not disguise an event as automatic alpha overlap or assign historical/causal meaning to a successful mathematical check.

## Proof commands

```sh
python -m compileall -q haunted_blender
python -m unittest discover -s tests -v
python -m haunted_blender.living_object_cli --help
```

The dedicated CI installs Pillow and FFmpeg, runs every N0–N5 regression suite, actually encodes an MP4 and decodes its final frame, verifies the transparent PNG alpha and hashes, and exercises order, clock, overlap, source mutation, incompatible background and frozen snapshot tampering. A successful test does not establish film-release readiness or perceptual quality.
