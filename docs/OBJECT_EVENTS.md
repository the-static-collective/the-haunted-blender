# N6 — Event Graph: the eventful object

**Experimental branch:** `experimental/object-events-v0.1`, stacked on the frozen N5 Living Object branch. This cartridge adds files only; it does not edit N0–N5 project schemas, snapshots, renderers, asset catalog, command doors or accepted creative decisions.

## Scope: explicit lineage plus executable visibility

An N6 recipe binds one verified **frozen N5 Living Object snapshot**, which already binds the N4 foregrounds, N3 mesh, N2 correspondence, N1 declared relationship and N0 source/derivative digests. N6 introduces 2–8 *event-level part IDs* referring to the names of existing frozen N5 layers. An N6 part may reuse an N5 layer's cutout, geometry and material under a **new declared artistic identity**. Reuse does not synthesize new image content, separate geometry, or prove a true physical split.

Each part has `id`, `source_layer_name`, `role` and `initial` (explicit Boolean). Only declared initially active parts have visibility 1 at frame 0. Other parts must have exactly one producer event. A part may be consumed at most once, and consumed identities cannot be reborn or silently recycled. Hence `split(body -> left,right)` followed by `join(left,right -> body)` is **invalid** in v0.1: use a newly named `body_returned` destination. This is deliberately more restrictive than expressive narrative identity and leaves the later identity-continuation question open.

The four implemented event types require **strictly positive-duration windows** within integer frames 0–48:

- `birth`: no source, exactly one newly available target.
- `death`: exactly one available source, no target.
- `split`: exactly one available source, exactly two newly available targets.
- `join`: exactly two available sources, exactly one newly available target.

For a produced part used as a subsequent event input, its producing event must **finish strictly before** the consuming event starts. Reused or unknown IDs, duplicate producers, duplicate consumers, incompatible intervals, and cycles are refused. Events are artist proposals, not independently witnessed occurrences or physical/causal claims.

The renderer uses N5's already-authorized source polygons, texture modes, independently selected N5 part clocks, alpha masks, declared z-order and N4's explicitly selected background. N6 adds a separate event-visibility multiplier for each named part. Within a window `[a,b]`, progress is `clamp((frame-a)/(b-a),0,1)`; input opacity ramps `1→0` and output opacity `0→1`. Outside windows, an identity retains the declared active/inactive state. If two event-level IDs reuse the same N5 source layer, their pixels may overlap or even be identical: the receipt must **not** claim their contours split into independent pieces. Rendering order within equal N5 z-order is deterministic by part ID, and that secondary order is a 2D presentation convention, not depth reconstruction.

N6 produces a 49-frame 320×180 24-fps silent local MP4 over the inherited N5 diagnostic matte or declared frozen clean plate. The optional separate transparent RGBA midpoint PNG contains only the assembled foreground. A JSON receipt reports the event graph, parent snapshot identity, per-frame part visibility, source clock, actual alpha footprint, compositing overlap, both output digests and nonclaims.

## Local exercise

Prepare two distinct frozen N4 contours over the **same frozen N3 parent**, combine them into a frozen N5 object, then create a private `/path/to/events.json` file with the actual N5 layer names and explicit lineage:

```json
{
  "parts": [
    {"id":"body","source_layer_name":"body","role":"primary-mass","initial":true},
    {"id":"rim","source_layer_name":"rim","role":"rim","initial":true},
    {"id":"left","source_layer_name":"body","role":"split-child","initial":false},
    {"id":"right","source_layer_name":"body","role":"split-child","initial":false},
    {"id":"body_returned","source_layer_name":"body","role":"joined-part","initial":false},
    {"id":"shadow","source_layer_name":"rim","role":"shadow","initial":false}
  ],
  "events": [
    {"id":"birth-shadow","type":"birth","from":[],"to":["shadow"],"start_frame":5,"end_frame":12},
    {"id":"split-body","type":"split","from":["body"],"to":["left","right"],"start_frame":8,"end_frame":16},
    {"id":"join-body","type":"join","from":["left","right"],"to":["body_returned"],"start_frame":20,"end_frame":30},
    {"id":"death-rim","type":"death","from":["rim"],"to":[],"start_frame":32,"end_frame":42}
  ]
}
```

`shadow` in this example is a descriptive role for a repurposed N5 cutout, **not** a physically computed shadow or a new lighting effect.

Install local optional Pillow and FFmpeg, check out the N6 branch, and supply only paths/IDs returned from your actual frozen parent recipes:

```sh
python -m haunted_blender.object_events_cli create ~/HauntedBlender /absolute/path/to/frozen-N5.json /private/events.json
python -m haunted_blender.object_events_cli freeze ~/HauntedBlender events-RETURNED_ID
python -m haunted_blender.object_events_cli plan ~/HauntedBlender /absolute/path/to/frozen-N6.json
python -m haunted_blender.object_events_cli render ~/HauntedBlender /absolute/path/to/frozen-N6.json --out ~/HauntedBlender/renders/events.mp4 --alpha-out ~/HauntedBlender/renders/events-midpoint.png
```

The local outputs are not committed to GitHub or sent to remote image generation. Create a **new recipe** with `--revises events-OLD_ID` to alter the event graph while preserving the same frozen N5 parent. Existing videos and receipts are not silently overwritten; process interruption before a receipt may leave outputs requiring manual reconciliation.

## Crater breadcrumbs: reserved, unsupported and non-authoritative

The following event names are deliberately **reserved but rejected** by N6 rather than accepted as no-op annotations: `reveal`, `conceal`, `open`, `close`, `detach`, `attach`, `split_many`, `join_many`, `part_birth`, `part_death`.

**N7 — Aperture / Interior:** named boundary and hole geometry, explicit opening/closing event, source authorization for formerly unseen pixels, alpha/hole and occlusion checks. Mere visibility of a preexisting N5 layer is not an opened 2D hole.

**N8 — Shadow / Reflection Companions:** a separate optional dependency graph for a light source, surface, caster and timing; explicitly rendered phenomena with uncertainty, rather than assigning `role=shadow` and asserting a light-transport calculation.

**N9 — Topology:** typed operations for split contour, merge contour, tear, hole birth/death and multiple components, with Dogram-inspired before/after topology delta and local geometry certificates. These must be new explicit operations; no reinterpretation of N6 opacity ramps as preserved topology.

**N10 — Object identity continuation:** optional artist-confirmed alias/return relation between an consumed part and a new part, without reusing consumed event IDs or claiming historical or physical identity from pixel overlap.

All prospective Dogram math witnesses remain bounded to measurable graph/geometry predicates: **do the math, show the delta, keep the receipt, do not decide what it means**. No Dogram research branch is imported as a required renderer or allowed to determine artistic intent.

## Verification

```sh
python -m compileall -q haunted_blender
python -m unittest discover -s tests -v
python -m haunted_blender.object_events_cli --help
```

Dedicated CI installs Pillow and FFmpeg and runs N0–N6 regression and local MP4/transparent PNG proof using generated synthetic images only. Passing tests demonstrates the declared lineage and measurable 2D alpha transitions, **not** physical split/join, topological continuity, hidden-surface synthesis, production-ready quality or release readiness.
