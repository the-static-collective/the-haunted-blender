# SCENE-ARTIFACT-001 — accepted camera proposal to existing render contract

**Status: bounded experimental rocket step.** This branch stacks on SCENE-WEAVE-001, which stacks on the Alchemical Compiler. All pre-existing Pantry, alchemy, SceneWorld, N0 film and N0 rendering code remains unchanged.

## What actually works

\`\`\`text
cataloged photos + CR2-to-edited-image links
    -> frozen Alchemical Compiler material
    -> frozen explicitly fictional SceneWorld
    -> author-selected beat, photograph role, "wide" camera proposal
    -> explicit approval of a LOCAL PREVIEW ONLY
    -> immutable accepted-scene-artifact/v0
    -> deterministic film/v1 snapshot, one static shot per selected beat
    -> N0 FFmpeg silent 720p storyboard and ordinary N0 receipt
    -> separate artifact-to-render lineage receipt
\`\`\`

The artifact retains SceneWorld identity/hash, Alchemy snapshot hash, selected image-role IDs and original/edited relationships, exact candidate digests, beat indices, audience knowledge already established by the filmmaker, local rights markers, and render adapter/scope. The existing N0 film schema and execution authority are used **without modification**. The output video is not presumed to prove any fictional event, acting performance or character identity.

Only \`wide\` is executable at this seam: the current N0 adapter supports static full-image framing, so it would be misleading to claim that its \`detail\`/insert or \`absence\`/negative-space proposals have been realized. Those remain valid non-rendering proposals for future camera/motion adapters. No withheld narrative facts are auto-revealed and no proposed action is admitted as an occurrence.

Source/edited-image digests are rechecked against the Alchemy source snapshot and N0's actual render plan. Editing an earlier source, reattaching a different RAW derivative or altering a frozen world fails closed rather than silently substituting footage. Each accepted source/artifact/film/render witness is independent and content-addressed where defined by the source layer; the adapter never changes source photographs or existing project models. A renderer failure remains a failure; no artifact success receipt is issued before N0 returns a completed output.

This is **local private preview**, not permission to distribute photos, voice, likeness, music or a film. \`--approve\` attests a creative preview choice, not an actor release, rights clearance or account authentication. Future exports require a separate rights gate.

## Local exercise

Requires Python 3.10+, local FFmpeg and a locally initialized Pantry. Use your own assets. First create a two/three-source Alchemy snapshot using [Alchemy instructions](ALCHEMY.md); then seed and freeze a SceneWorld using [Scene Weave instructions](SCENE_WEAVE_001.md). A three-source illustrative selection is in \`examples/scene-artifact-selections.json\`.

\`\`\`sh
python -m haunted_blender.scene_artifact_cli accept ~/HauntedBlender \
  /absolute/path/to/frozen-scene-world.json \
  /absolute/path/to/frozen-alchemy-snapshot.json \
  examples/scene-artifact-selections.json --approve

python -m haunted_blender.scene_artifact_cli render ~/HauntedBlender \
  /absolute/path/to/returned-scene-artifact-snapshot.json \
  --out ~/HauntedBlender/renders/scene-weave-pilot.mp4
\`\`\`

Outputs: one silent MP4, the N0 \`.receipt.json\` file, the additional \`.scene-artifact.json\` lineage witness, plus the retained N0 film snapshot. The same accepted source inputs lead to the same artifact and film snapshot identities. Rendering an existing output refuses rather than overwriting.

## Acceptance proof and limits

The synthetic contract suite tests filmmaker approval, shot-selection boundaries, audience disclosure non-promotion, stable replay, stale/tampered source refusal, retention of the N0 film/render semantics and the output/witness chain with a real FFmpeg rendering test where FFmpeg is installed.

This is not yet a finished dramatic scene, photo-object detection, full scene-motion composition, sound/acting, independent shot cache, 10,000-photo indexing benchmark, or a release candidate. The core next target is a **camera realization adapter** (inserts, negative space, depth/camera motion) with explicit geometry and separate view/revelation approvals; then sound/performance composition and per-scene caching before the full three-scene drama gate.

## The artifact question

An artifact is a **durable creative carrier**: a referenced source, a filmmaker-accepted edit decision, or a produced output, each with a separate identity and scope. A creative artifact can become material for another story only by an explicit new import/admission; a film render does not silently become the historical truth of what it fictionalizes. This is one interpretation of the proposed artifact frontier, not an irreversible ontology or a substitute for further conversation.
