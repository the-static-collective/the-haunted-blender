# N2 — Correspondence Engine (experimental additive layer)

**Status:** a separate, opt-in geometric cartridge on top of N1. N0 film schema, N0 storyboard renderer, N1 alchemy recipes/snapshots and N1 crossfade renderer are **not changed**. This branch is a draft and does not satisfy the complete-film release gate.

## Core operation

An artist declares two or more **named, normalized landmark correspondences** on two photographs, such as the left and right ends of a cup rim and the corresponding points on a moon's apparent outline. A frozen N1 Alchemical Compiler recipe supplies both source identities and the artist-proposed relationship. N2 accepts only **adjacent** participants in that recipe's explicit order. For a three-object recipe (cup → water → moon), compile one source → bridge take and a separate bridge → target take. The third object is not discarded or asserted to be implicit in a two-image morph.

N2 builds a 49-frame local 320×180 / 24fps 2D similarity morph. Each image is oriented using its EXIF orientation (where supported), scaled with preserved aspect ratio and letterboxed. Coordinates in the N2 input are fractions of the resulting *oriented image contents*, not the padded frame. At each time sample, two source anchors and their corresponding destination anchors are linearly interpolated to common canvas positions. Both photos are rotated, scaled and translated by an inverse affine sample to those locations and the resulting RGB frames are blended. The first output frame reproduces the letterboxed first image; the last reproduces the letterboxed second image. Intermediates are actual newly warped frames, **not the N1 static crossfade**.

The two primary anchors determine one 2D similarity transform. Any additional artist-selected landmarks are *constraints*, not extra degrees of freedom: the predicted reprojection of every landmark must remain within the declared pixel tolerance across every frame or the plan is refused. The reported maximum is a mathematical reprojection error of the declared coordinates; it **does not** verify that pixels show the claimed object, that two objects are the same physical entity, that a material is preserved, that generated pixels are witnessed, or that the images describe a real 3D transition.

## Source and revision boundaries

The N2 recipe references an **already frozen and verified N1 snapshot SHA**. N2 freezes its own content-addressed snapshot; it does not mutate the N1 snapshot or import arbitrary paths from the caller as source media. The N1 parent verifies both cataloged originals and frozen renderable derivatives. Reassociating a CR2 export after the N1 freeze cannot change the bound frame. To change landmarks, use a new N2 recipe with `--revises`; the earlier snapshot remains unchanged and its ID remains distinct. If a source file is edited after freeze, planning/rendering refuses instead of issuing a success receipt.

No private media, location metadata, project databases or render outputs are committed. No remote calls, photo uploads, subject recognition or automatic semantic inference occur. Pillow is an **optional dependency of the N2 cartridge only**; N0 and N1 remain standard-library + optional FFmpeg.

## Local execution

First complete N0 `init`/`scan` and N1 `create`/`freeze` using the real returned asset IDs and frozen alchemy path. Create a private local landmarks file (example coordinates, not automatically detected object positions):

```json
[
  {"id": "rim-left", "from": [0.25, 0.30], "to": [0.30, 0.25]},
  {"id": "rim-right", "from": [0.75, 0.30], "to": [0.80, 0.25]}
]
```

Install optional rendering dependencies: `python -m pip install Pillow`; install FFmpeg on your machine.

```sh
python -m haunted_blender.correspondence_cli create ~/HauntedBlender \
    /path/to/frozen-n1-alchemy-snapshot.json /path/to/private-landmarks.json \
    --from-role source --to-role bridge --max-error-px 2
python -m haunted_blender.correspondence_cli freeze ~/HauntedBlender correspondence-RETURNED_ID
python -m haunted_blender.correspondence_cli plan ~/HauntedBlender /path/to/frozen-n2-snapshot.json
python -m haunted_blender.correspondence_cli render ~/HauntedBlender /path/to/frozen-n2-snapshot.json \
    --out ~/HauntedBlender/renders/cup-to-water.mp4
```

For a pairwise N1 recipe, use source and target. For a triadic recipe, source→bridge or bridge→target is allowed when that sequence is adjacent in the accepted N1 order. To revise, create a different local landmarks file and pass `--revises correspondence-ORIGINAL_ID` to the same create command. Old accepted N2 recipes are not overwritten.

## Checks and next seam

The dedicated optional-dependency CI installs Pillow and FFmpeg and tests both prior layers, strict ordered pair selection, invalid and nonfinite input refusal, third-landmark incompatibility, immutable revision history, source-hash tampering, deterministic geometric frame generation and output digest/receipt. A successful CI result proves the bounded local renderer, not a semantic or photorealistic metamorphosis. The full filmmaker application is still unreleased.

Future geometry cartridges may support more complex nonrigid correspondences, masks, piecewise-affine meshes, topological birth/death events, occlusion and inpainting. Those need independent contracts rather than silently relaxing the current two-anchor similarity invariant.
