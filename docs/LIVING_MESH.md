# N3 — Living Mesh (experimental, additive)

**Branch:** `experimental/living-mesh-v0.1` stacked on N2. N0 film, N1 alchemy and N2 correspondence modules, CLI paths, frozen schemas and renderers remain unchanged. This is a bounded local 2D geometry cartridge, not a complete editor, topology-changing mesh, or photorealistic morph.

## What it does

An artist starts with a **frozen N2 correspondence snapshot** (which already binds the N1 artist-proposed relation, private pantry source records and renderable RAW derivatives). N3 adds a new immutable recipe with two explicitly authored, ordered 5×5 meshes. The canonical 16 boundary vertices stay fixed; the 9 interior vertices can be moved separately. Each grid cell is split into two fixed-connectivity oriented triangles, making 32 independent piecewise-affine patches. At every frame the two meshes interpolate, source and target image patches are inversely warped to the intermediate mesh and blended. A local FFmpeg adapter encodes 49 actual 320×180/24fps frames; it does not simply crossfade two stationary photographs. Accepted N2 snapshots and earlier N3 revisions are never edited.

The first and last video frames use the corresponding bound N2 stills. Intermediate frames use actual per-triangle deformation. The frozen parent revalidates source and edited-derivative SHA-256 digests before rendering and again before publication. This layer neither makes cloud requests nor inspects personal archives outside the explicit N0/N1/N2 approved paths.

## Dogram-inspired mathematical witness, not Dogram authority

N3 deliberately **does not import or mutate Dogram**. It carries three narrowly mathematical receipts inspired by Dogram's documented delta, orientation and no-promotion discipline:

- For every oriented triangle, report source signed double area, target signed double area, their difference, and the **analytic minimum over every continuous t in [0,1]**. Because vertex trajectories are linear, signed area is a quadratic in t; its minimum lies at an endpoint or the interior quadratic stationary point. Reject when any face reaches the declared collapse margin or reverses orientation, even when both endpoints look valid.
- Verify N2's artist-selected landmark correspondence independently: evaluate each point in its source and target triangle, require the selected mesh face to be consistent, and report forward/backward geometric mapping residuals. Reject a proposed N3 mesh when the declared tolerance is exceeded. The check uses N2's actual EXIF-oriented, letterboxed coordinate conversion, not an assumed full-frame mapping.
- Retain one per-face delta and one per-landmark residual instead of promoting a successful render to a global claim of object identity, material conservation, optical continuity or 3D reconstruction.

Current Dogram research on order-sensitive composition and higher-order relations suggests future independent oracles and a reversible vocabulary for permitted topology changes, but no open Dogram research PR is assumed merged or a required library. A signed-area test verifies this declared planar mesh; it does **not** prove a real-world object's topology, conservation of matter, or physical motion.

## First local usage

Initialize/index sources through N0, then produce actual frozen N1 and N2 snapshots through their existing commands. Install Pillow as an optional N3 dependency and have local FFmpeg available. From the checked-out N3 branch:

```sh
python -m pip install Pillow
python -m haunted_blender.living_mesh_cli example-grid --out /private/location/mesh.json
```

The generated JSON contains `source` and `target` lists of 25 normalized [x,y] points each in row-major order. Edit **only interior target vertices** initially. For example, the center vertex has index 12 and may be changed from `[0.5,0.5]` to `[0.58,0.53]` when this preserves the existing N2 landmark contract and every triangle's signed orientation. An edited mesh does not automatically imply its claimed shape correspondence is correct.

```sh
python -m haunted_blender.living_mesh_cli create ~/HauntedBlender \
  /absolute/path/to/frozen-n2-snapshot.json /private/location/mesh.json \
  --max-landmark-error-px 3
python -m haunted_blender.living_mesh_cli freeze ~/HauntedBlender mesh-RETURNED_ID
python -m haunted_blender.living_mesh_cli plan ~/HauntedBlender /absolute/path/to/frozen-n3-snapshot.json
python -m haunted_blender.living_mesh_cli render ~/HauntedBlender /absolute/path/to/frozen-n3-snapshot.json \
  --out ~/HauntedBlender/renders/living-mesh.mp4
```

Use actual returned IDs and paths. To change points, create a new mesh recipe with `--revises mesh-OLD_ID` (same frozen N2 parent). The prior snapshot and its renderer remain available. Existing output files or receipts are never intentionally overwritten.

## Boundaries and further frontier

This renderer can warp a photograph locally, but cannot synthesize occluded pixels, isolate individual subjects with mattes, conserve material, add or remove holes, or realize the literary meaning of a transformation. Tearing, triangle birth/death, mask-aware morphing, occlusion handling and mesh patches with true alpha need separate explicit operations; they should not be concealed by turning off the orientation test.

Next branch candidate: artist-selected **closed contour + interior/exterior masks** with separate deformation rigs, and an explicit `topology_change` instruction whenever a boundary is removed or fused. The initial N3 proof is a measurable, reversible 2D building block for that later work.

## Proof

The dedicated CI installs optional Pillow + local FFmpeg, compiles all layers, exercises N0/N1/N2/N3 regression tests including a real decoded midpoint frame, tests a triangle with both positive endpoints but zero interior area, refuses conflicting inherited landmarks, checks old snapshot immutability and verifies new output digest/receipt. A green check confirms these bounded computations, **not** full-film readiness.
