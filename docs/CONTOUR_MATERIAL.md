# N4 — Contour & Material Engine (experimental additive cartridge)

This branch `experimental/contour-material-v0.1` is stacked on N3. It adds only N4 files. It does not mutate N0's film/v1 or catalog, N1's alchemical recipes, N2's landmark correspondence, N3's grid, their frozen snapshots, or their renderers. N4 is an object-level **2D masked preview**, not a released visual editor, 3D reconstruction, semantic morph, inpainting system, or proof of material conservation.

## Two independent things can change

1. **Shape:** an artist provides a clockwise-in-image ordered, convex, 3–12-vertex polygon on each inherited N3 source and target photograph. Vertices correspond by index. The polygon is the artist-authored **opaque foreground mask**; N4 does not pretend to detect or recognize an object. It interpolates polygon vertices over 49 frames. A centroid fan and N3's independent per-triangle inverse-affine mathematics deform only the masked object into its intermediate contour. Convexity and positive oriented area are checked **analytically over all continuous t in [0,1]**, not just sampled frames. Degenerate, reversed, or folding contours are refused.

2. **Material:** `source-only` warps the cutout texture from the source photograph throughout the entire sequence, even once the object reaches its destination outline. `crossfade` independently warps both artist-masked source and target textures and blends their appearances as the shape changes. Neither mode claims that pixels are physically conserved; neither mode modifies any source image. These are deliberately different operations: shape change does not imply material substitution.

N4 consumes and verifies a **frozen N3 snapshot**. It reuses N2's EXIF-aware, aspect-preserving conversion from normalized coordinates on oriented image content into letterboxed canvas pixels and N3's triangle inverse-affine and analytic orientation kernels. Existing N3 mesh positions are not secretly applied twice. It uses the source and target frame records inherited from N3, but renders a distinct isolated foreground take rather than reusing N3's full-frame pixels as a background.

## The background-hole boundary

A photographed object is baked into its original photographic background. If we simply move its cutout on top of that photograph, the original object remains behind as a duplicate. N4 refuses to hide this fact through undocumented inpainting. An explicit background choice is required:

- `diagnostic-matte` (default) composites the independently deforming cutout over a clearly identified uniform colored diagnostic canvas. This **does not represent the original scene**.
- `clean-plate` requires a separately indexed, explicitly selected local image asset that the artist asserts is a suitable background without the moving object. N4 freezes the plate's original/derivative digests as additional provenance and checks them before rendering and again before writing the receipt. It does **not** verify that the plate genuinely depicts the same place or viewpoint. A separate clean plate should be photographed or prepared deliberately; never mistake the original source photo for a clean plate.

There is no subject detection, alpha-aware output codec, automatic background removal, depth, shadow reconstruction, occlusion recovery, transparent RGBA master video, topology change, or remote AI provider in this cartridge. The preview is a silent 320 × 180, 24 fps, 49-frame H.264 MP4 on an explicitly selected opaque background. Actual selected foreground matte is RGBA during composition, but the exported preview is opaque.

## Local usage

First create an N0 indexed local photo library and actual frozen N1, N2, N3 snapshots using their respective documented command doors. Checkout N4, install optional Pillow and local FFmpeg. Coordinates are normalized to each independently **oriented image's content**, not to an arbitrary full-frame projection. In a private `/path/to/contours.json` create:

```json
{
  "source": [[0.26,0.33],[0.44,0.33],[0.44,0.67],[0.26,0.67]],
  "target": [[0.54,0.30],[0.77,0.32],[0.75,0.74],[0.52,0.70]]
}
```

Both polygons require the same count, matching correspondence by position, positive signed image-space orientation, and convexity for the complete trajectory; start with small displacements. Do not include personal image content, names, EXIF, or private filesystem paths in this public repository.

```sh
python -m haunted_blender.contour_cli create ~/HauntedBlender /absolute/path/to/frozen-n3.json /private/contours.json --material source-only --background diagnostic-matte
python -m haunted_blender.contour_cli freeze ~/HauntedBlender contour-RETURNED_ID
python -m haunted_blender.contour_cli plan ~/HauntedBlender /absolute/path/to/frozen-n4.json
python -m haunted_blender.contour_cli render ~/HauntedBlender /absolute/path/to/frozen-n4.json --out ~/HauntedBlender/renders/object.mp4
```

For an artist-provided clean plate, add `--background clean-plate --clean-plate-asset-id asset-ACTUAL_INDEXED_ID` to `create`. For a material change, select `--material crossfade`. For a reversible revision, `create ... --revises contour-PREVIOUS_ID` makes a new separate recipe and snapshot, without overwriting any earlier one.

## Receipts and boundaries

Each N4 plan reports a signed source/target polygon area and delta, the analytic minimum signed area for every fan face and every convexity corner, the original/derivative source hashes inherited from N3, clean-plate identity when supplied, render mode, and nonclaims. The completed receipt records the actual MP4 digest and per-frame number of nonzero-alpha foreground pixels before flattening against the background. This does not certify semantic identity or satisfactory aesthetics. N4 never imports Dogram as an execution authority; it reuses N3's bounded math witness already inspired by Dogram's `DO THE MATH, SHOW THE DELTA, KEEP THE RECEIPT, DO NOT DECIDE WHAT IT MEANS` contract.

Run:

```sh
python -m compileall -q haunted_blender
python -m unittest discover -s tests -v
python -m haunted_blender.contour_cli --help
```

The dedicated N4 CI uses synthetic local graphics and installs Pillow plus FFmpeg to render and decode real frames. N0 through N3 regression tests must also pass. A successful check is **not** evidence of a ready-for-filmmakers release.

**Next optional experiments:** higher-fidelity subpixel alpha edges and standalone transparent frame export, a genuine mask editor and local segmentation proposals that remain unaccepted until confirmed, contours containing holes or multiple parts with explicit topology-change events, occlusion/inpainting as opt-in cartridges, and a versioned accepted-take adapter to N0 film shots.
