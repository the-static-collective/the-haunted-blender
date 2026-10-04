# COUNTERFACTUAL-DIRECTOR-001 — two audience cuts, two real previews

**Status:** experimental cartridge stacked on [SCENE-ARTIFACT-001](SCENE_ARTIFACT_001.md). Neither the Alchemy, SceneWorld, film/v1, nor N0 render contract changes.

Two separately authored SceneWorld snapshots share the same fictional entities, events, beats, questions and frozen Alchemy sources. The filmmaker places audience knowledge at different beats in each world. Each world already has a separately accepted Scene Artifact selecting the *same multiset of source images*, in a visibly different beat order. The pairing validates all four frozen witnesses and records the exact knowledge divergence. Pair approval stores a content-addressed snapshot; rendering calls the existing Scene Artifact/N0 path twice and issues a pair receipt only after both independent MP4s and their receipts exist.

## Local command door

First create and accept both SceneWorld/Scene Artifact cuts following the [Scene Weave](SCENE_WEAVE_001.md) and [Scene Artifact](SCENE_ARTIFACT_001.md) instructions. Author the alternate world's audience knowledge explicitly; the cartridge will not infer it from pixels. Then:

```sh
python -m haunted_blender.counterfactual_cli accept ~/HauntedBlender \
  /absolute/path/to/accepted-cut-a.json /absolute/path/to/accepted-cut-b.json --approve
python -m haunted_blender.counterfactual_cli render ~/HauntedBlender \
  /absolute/path/to/returned-pair-snapshot.json \
  --out-a ~/HauntedBlender/renders/cut-a.mp4 \
  --out-b ~/HauntedBlender/renders/cut-b.mp4
```

Each output has its own N0 receipt and Scene Artifact lineage witness. The pair receipt binds both MP4 hashes, both receipts and the authored knowledge differences. Rendering requires two distinct filenames and refuses any existing output/receipt. If the second render fails after the first succeeds, the first cut and its truthful scoped receipts remain; no pair success receipt is issued. Retry with a new second output or inspect the partial first cut. This is **not** atomic pair publishing.

## What the film says and what the data says

The data can prove the images, order, frozen sources and *authored* observer cuts. It cannot prove that a real viewer understood an image, that an image depicts the fictional event, or that the people photographed are the characters. Both outputs are silent static-image local previews. Authoring a world or approving a local preview does not authorize distribution or likeness use. A future camera/reveal adapter could connect specific visible detail to proposed knowledge changes, subject to filmmaker confirmation and a real viewer test.

## Proof

```sh
python -m unittest discover -s tests -v
python -m haunted_blender.counterfactual_cli --help
```

The synthetic fixture constructs two worlds from one three-photo Alchemy snapshot, moves one authored audience-knowledge beat, chooses different orders of the same three frames, renders two real MP4s and checks their independent and pair receipts. It also checks conflicting events/media, missing approval, stale source refusal and duplicate output refusal.
