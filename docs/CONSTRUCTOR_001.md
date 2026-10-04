# CONSTRUCTOR-001 — ART × I × FACT

Status: experimental additive cartridge stacked on the existing Counterfactual Director draft. Does not change N0/N1, SceneWorld, Scene Artifact, or Counterfactual Director schemas or code. Nothing here defines **I** for all art or declares artistic quality computable.

## Bounded proposition

An *artist-accepted source artifact* + an explicit, typed *constructor sequence* + *scoped source facts* -> one immutable **construction recipe**. Running that recipe through N0 yields another distinct **output artifact** with independent content digest and a separate receipt. A recipe is not proof of execution. A fictional statement is not evidence about a person depicted in a photograph.

\`\`\`text
ART    = accepted Scene Artifact identity + the filmmaker's stated intention
I      = ordered, registered constructors, their versions, parameters, selection
FACT   = separately typed fictional fact/observer hashes + actual source media digests
RECIPE = frozen, content-addressed proposed executable film, PRIVATE PREVIEW
OUTPUT = real N0 silent MP4 + existing N0 receipt + new construction receipt
\`\`\`

Exactly two constructors are executable in v0:
- \`editorial.reverse/v0\` reverses the **presentation order** of existing accepted static shots. Fictional beat chronology and authored character/audience knowledge are retained as ancestor witnesses; a montage's visible order does not rewrite what the characters actually learned in the story.
- \`editorial.hold-first/v0\` changes the duration of the currently first shot to an explicitly requested 250–600000 ms. It does not change the photographed frame, character knowledge or fictional events.

Both operators are pure, deterministic transformations of a film/v1 document. The registry lists supported input/output type, declared preservation scope, change scope and execution class. Unknown names and unsupported parameters fail closed; arbitrary user-supplied Python, shells, model plugins or remote uploads cannot enter as constructors.

**Order is meaningful:** \`reverse;hold-first\` holds the original last image, while \`hold-first;reverse\` holds the original first image, now last. The intermediate shot-sequence hashes and the final sequence are retained. A separate test holds I fixed and varies one filmmaker-authored fictional fact in the source SceneWorld: the recipe must change, and that fact must remain labeled *fictional* in both outcomes. No operator scores creativity, asserts observed audience comprehension or modifies the source world.

## How to exercise

A local library with a frozen 2–3-photo Alchemy snapshot, SceneWorld and accepted Scene Artifact already exists (see [Scene Artifact](SCENE_ARTIFACT_001.md)).

\`\`\`sh
python -m haunted_blender.construction_cli accept ~/HauntedBlender \
  /absolute/path/to/accepted-scene-artifact.json \
  examples/constructor-reverse-then-hold.json \
  --intent "Hold the image that closes the original sequence" --approve

python -m haunted_blender.construction_cli plan ~/HauntedBlender \
  /absolute/path/to/returned-constructor-recipe.json

python -m haunted_blender.construction_cli render ~/HauntedBlender \
  /absolute/path/to/returned-constructor-recipe.json \
  --out ~/HauntedBlender/renders/my-private-construction.mp4
\`\`\`

Try the alternate example \`constructor-hold-then-reverse.json\` with the same source artifact and intention. The source image sequence/duration mapping differs. These are **silent static-image films**; no real camera move or auditory information is synthesized.

The constructor recipe lives under \`snapshots/constructors/<sha>.json\`. The N0 film snapshot, output MP4, N0 \`.receipt.json\` and additional \`.construction.json\` witness remain distinct, inspectable outputs. Missing or changed originals, edited frame mismatch, altered accepted source, altered film snapshot, overwritten output and bad recipe hash refuse; no successful construction receipt is issued on failed rendering.

## Limits / future growth

- The current input type is only an approved static Scene Artifact; the only output medium is an N0 silent photographic storyboard. This is **not** a general-purpose graph of all creative media, a model-backed video synthesizer, or a finished filmmaking UX.
- Construction may alter **presentation order**, but not story canon, depicted real-world facts, character knowledge, privacy disclosures, rights or likeness consent. A local preview approval does not authorize publishing media.
- The output's bytes can be cataloged as a *new creative media source only through an explicit future admission interface*. Its production digest may be used as a production fact; its fictional content never becomes historical evidence automatically.
- Future constructor species may include accepted N2 landmark correspondence, N3 geometry, N4 contour/material, audience-aperture maps, soundtrack and deliberate color/camera operations. Each needs its own executable adapter and declared preserved/changed properties, not a text-only registry entry.
- Future conformance should pressure relative source-path portability, scope-limited cache invalidation, partial output reconciliation, actual audience disclosure measurements and preview/render parity beyond N0. The currently retained receipt attests only the bounded local render.

This is a researchable instrument for comparing **same ART+FACT / different I**, **same ART+I / changed fictional FACT**, and **I2(I1(...)) vs I1(I2(...))**, not a universal verdict about meaning.
