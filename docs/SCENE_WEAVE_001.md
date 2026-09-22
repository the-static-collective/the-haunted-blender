# SCENE-WEAVE-001 — the Cinematic Relationship Engine

**Status:** experimental additive scaffold on top of the separate Alchemical Compiler branch. No changes to N0 film/v1, the N0 still renderer, alchemy schemas or media files. This module creates *fictional* scene-world models and deterministic **non-rendering** camera proposals; a complete AI filmmaking director is not claimed.

## The actual composition seam

\`\`\`text
Pantry (source ID / RAW / edited-frame digest)
    -> accepted Alchemy snapshot (read-only, 2 or 3 image roles)
    -> explicitly filmmaker-authored fictional world
    -> frozen scene-world/v0 snapshot
    -> per-beat camera proposals / character + audience knowledge
    -> optional later fictional fact proposal
    -> explicit filmmaker approval => separately addressed descendant world
\`\`\`

A material image can inspire a scene. It does **not** establish the real identity, inner life, behavior or consent of a photographed person. The filmmaker must explicitly define the fictional characters, objects, locations, facts, relations, questions and available actions. The same source image can be used in many different fictional worlds.

## What is executable

- Seed a world from a **real, already frozen alchemy snapshot**, validating the parent alchemy frame digests through its own read-only planner. No photographs are uploaded or copied.
- Require explicit author basis for every fictional entity, fact, relation and knowledge record. Reject dangling dependencies, forged earlier knowledge and implicit biometric identification.
- Preserve separate knowledge cuts for each character and for the audience. A proposed action becomes available to a character only once declared prerequisites both occurred and became known to that character.
- Produce three fixed but distinct deterministic **presentation** proposals (establishing / insert / negative space). The detail treatment marks otherwise withheld facts as *possible reveals requiring filmmaker authorization*; proposals never grant audience knowledge or establish an event.
- Propose an alternate later state as an append-only fact supersession. Explicit approval creates a new world ID, parent hash and receipt field, leaving the original world and earlier fact intact. Stale or altered proposals refuse.
- Freeze/reload addressed world snapshots and retain alchemy recipe ID, source IDs, and frozen frame digests.

**Not implemented:** photographic object detection, dynamic composition search, actual cinematic quality evaluation, camera motion, sound, dialogue, scene-to-film render adapter, Dogram/MEMENTO/3rdi runtime calls, independent shot rerender, multi-user permissions or 10k-archive benchmarking. The creative ancestry is architectural inspiration, not a claim those projects were integrated as running services. The existing alchemy crossfade renderer remains independent.

## Local trial (synthetic-fixture or user-owned images only)

Create a 2–3 image alchemy snapshot using [Alchemy instructions](ALCHEMY.md), then:

\`\`\`sh
python -m haunted_blender.scene_weave_cli seed ~/HauntedBlender \
  /absolute/path/to/frozen-alchemy-snapshot.json \
  examples/scene-weave-three-photo.story.json
python -m haunted_blender.scene_weave_cli freeze ~/HauntedBlender world-RETURNED_ID
python -m haunted_blender.scene_weave_cli compose ~/HauntedBlender \
  /absolute/path/to/returned-world-snapshot.json --beat 0
python -m haunted_blender.scene_weave_cli compose ~/HauntedBlender \
  /absolute/path/to/returned-world-snapshot.json --beat 1
\`\`\`

At beat 0 the daughter has not been declared to know the letter's condition, so "open-letter" is *not* offered as an available action for her. At beat 1 the explicitly authored knowledge record makes the action a possible continuation, not an event. The mother's knowledge of the sender is never silently attributed to the audience.

To explore an independent future:

\`\`\`sh
python -m haunted_blender.scene_weave_cli branch ~/HauntedBlender \
  /absolute/path/to/returned-world-snapshot.json --source-fact sealed \
  --new-fact-json examples/scene-weave-open-letter.fact.json \
  --out ~/HauntedBlender/branch-proposal.json
python -m haunted_blender.scene_weave_cli approve ~/HauntedBlender \
  /absolute/path/to/returned-world-snapshot.json \
  ~/HauntedBlender/branch-proposal.json --approve
\`\`\`

The explicit CLI flag is an authoring-control prototype, **not** user authentication. Never put a real photographic archive, identifying information, EXIF locations, or private production data in this public repo.

## Composition aspirations

MEMENTO-inspired world vs. source separation; 3rdi-inspired observer cuts; Free Graph and National Treasure-inspired relations and open questions; Toaster-inspired candidate diversity; Dogram-inspired comparison *without* aesthetic verdict; ALEX/LOADOUT-inspired source and execution lineage. All remain optional, versioned future adapters. Blender owns the story-world decisions.

**Next gate:** prove an approved SceneWorld shot handoff into N0's existing accepted film/render path with explicit scoped cache invalidation, sound, rights checks, and preview/render parity. This slice alone does not produce a completed drama.
