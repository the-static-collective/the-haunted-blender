# FRANKEN BLENDER 005 — GHoT Compost Breeder Adapter

FRANKEN BLENDER 005 exposes one bounded donor capability:

```text
creative.blender.dreambreed.sixup
```

It accepts a `ghot.compost-breeder-request/v0` over stdin JSON and returns real donor-owned DREAMBREEDER 003 + Cutout Compiler 004 evidence.

## Physical crossing

```text
GHoT Compost Breeder request
        ↓
bounded Blender adapter
        ↓
create_ecology()
        ↓
6 proposal-only unborn films
        ↓
render_sixup()
        ↓
6 real proposal MP4s
+ 1 real 3×2 six-up MP4
        ↓
donor result JSON
```

## Request custody

The adapter requires:

- schema `ghot.compost-breeder-request/v0`;
- `authority = proposal-request-only`;
- effect `GROW_SIX_UNBORN_FILM_PREVIEWS`;
- a provenance-only parent history reference;
- parent capsule hash + positive generation;
- relation id;
- at least one source receipt id.

The exact parent capsule hash becomes the DREAMBREEDER common checkpoint. The Blender ecology generation is parent generation + 1.

## Real renderer path

This adapter does not simulate Blender semantics.

It calls the existing live functions:

- `haunted_blender.dreambreeder.create_ecology()`;
- `haunted_blender.dream_cutout_compiler.render_sixup()`.

The adapter builds a small deterministic local cutout kit from the normalized request identity, then Cutout Compiler 004 performs the actual FFmpeg/Pillow preview rendering.

## Result

The donor result schema is:

```text
haunted-blender/ghot-compost-breeder-result/v1
```

It carries:

- unresolved `haunted-blender/dream-ecology/v1`;
- `haunted-blender/dream-sixup-preview/v1`;
- six actual proposal preview paths + SHA-256 values;
- one actual contact movie path + SHA-256;
- inline content-addressed ecology/six-up JSON artifacts for Instrument Rack packet portability.

## Replay

The normalized request is content-addressed into the adapter output directory.

An identical direct donor request reuses the existing result only if the cached request identity matches and the contact preview still exists. It does not overwrite the old witness.

GHoT Instrument Rack provides an additional replay barrier above this donor-local behavior.

## Capability limits

The manifest declares one capability only.

It does not expose:

- KEEP;
- proposal selection;
- publication;
- arbitrary shell;
- network access.

## Laws

```text
ADAPTER != SELECTION
PREVIEW != KEEP
WATCHING != KEEP
PREVIEW != HISTORY
DONOR RESULT != GHOT SEMANTICS
IDENTICAL REQUEST != OVERWRITE
```

## Proof

The dedicated 005 workflow:

- installs FFmpeg + Pillow;
- compiles Blender + adapter code;
- runs the full inherited suite plus adapter tests;
- renders a durable real six-up through the stdin/stdout adapter;
- uploads the result JSON, six proposal MP4s, contact movie, plans, and generated kit assets.
