# MANGALIZE-004 — pixel execution

An admitted static layout acquires exact pixel consequences only through a
separate pixel-execution admission. The immutable 001/002/003 source, custody
and composition remain unchanged. This experiment starts at exact #66 parent
`736dc0eba07b591a7aa25abf3fb92e5ddbaa7a23`; all 94 historical specimen files
are pinned in `specimens/mangalize-004/ANCESTOR_PIN.json`.

Four canonical schema families separate execution plan, proposal, admission and
execution. Every record names MANGALIZE and MANGALIZE-004. Plan/proposal have
pixelExecution false. External admission can grant only pixelExecution true;
motion, sound, publication, external generation and character casting remain
false. The CLI never issues an admission. Factory references are accountable
external declarations, not cryptographic authentication of a human authority.

The new path is static PNG/RGBA8 only, with no fps, duration, keyframes, audio,
video or FFmpeg. Existing Cutout Stage behavior remains unchanged. Read-only
planning verifies the entire earlier event chain, hashes source byte snapshots,
inspects PNG dimensions/modes and calculates integer recipes. It does not resize,
composite or encode the founding page. Independently replaying the old harvest
witness uses the old authorized 001 quarry; it does not execute the 004 layout.

The exact v0 rules are:

- Absent authored background becomes a transparent RGBA `(0,0,0,0)` canvas.
  An explicitly authored background is refused by this v0, rather than replaced.
- x/y millipixels must divide exactly by 1000. Fractional origins refuse.
  Rotation must be zero; no crop or time range. Native-scale fit, top-left
  origin/anchor and explicit canvas clipping remain the authored instructions.
- Target dimensions are `max(1, floor((2*d*scaleMillionths+1000000)/2000000))`.
  This is positive half-up, not implicit Python banker rounding. v0 bounds are
  at most 16384 per dimension and 16777216 pixels per raster/canvas.
- Default resampling is explicit Pillow 12.1.1 `Image.Resampling.LANCZOS`.
  The real sources are RGBA with continuous tone in the panel/crop and variable
  alpha in the edge mask. Lanczos retains the existing tonal/mask-edge policy;
  nearest changes the visual transform. A separately named NEAREST policy is
  supported for synthetic comparison, with a different plan/proposal requiring
  separate admission. No sampler is inferred from a role.
- Convert to RGBA with Pillow, with no ICC/gamma transform. Supported sources
  are nonanimated PNG in RGB/RGBA/L/LA. Resize with `box=None`, `reducing_gap=None`.
  Lanczos at changed dimensions uses Pillow's premultiplied RGBa resize and then
  converts back to straight RGBA; unchanged dimensions copy RGBA. NEAREST samples
  straight RGBA channels. Source mode, target dimensions and the kernel are bound.
- Apply opacity to alpha only after resizing:
  `A_out=floor((2*A_in*opacityMillionths+1000000)/2000000)`.
  RGB stays unchanged after resize. At 0.35, alpha 255 becomes 89, alpha 30
  becomes 11, alpha 10 becomes 4. The half-up rule deliberately differs from
  the old implicit banker rule at some ties. Opacity 1 preserves every alpha byte.
- Intersect the half-open destination box with `[0,0,canvasWidth,canvasHeight]`.
  Record source/scaled dimensions, box before clipping, intersection, per-side
  discarded extents and final rectangle. Clipping discards raster overflow;
  it is not new source crop authorship.
- Copy clipped straight RGBA into its own transparent full-canvas layer with
  `paste` without a mask, so placement does not apply a second alpha blend.
  Preserve source/performed-use bytes. Save each layer under its exact useHash.
- Sort by `(z, useHash)` ascending, independently of transport array order.
  Source-over composition uses Pillow `Image.alpha_composite` with straight
  8-bit RGBA inputs/output and the pinned imaging binary's integer arithmetic
  and rounding. No linear-light conversion or role-specific interpretation.
- Encode a canonical PNG: RGBA8 IHDR, row filter 0, one IDAT, fixed zlib header
  0x7801, uncompressed stored blocks at most 65535 bytes, Adler32, IEND and CRC32.
  No timestamps, ICC, gamma or optional metadata. This small serializer removes
  compression heuristics/library variability without changing raster semantics.

Implementation witnesses bind renderer version, this module's exact SHA,
Pillow version, Image.py SHA, native imaging binary SHA, Python ABI, system and
architecture. A different witness produces a different plan; an old proposal
cannot authorize it. Independent replay in the declared installed environment,
including a separate process, proves exact matrices and PNG bytes. Cross-ABI,
platform, wheel or Pillow equivalence is unproven; mismatch refuses. The module
hash binds future implementation changes to a new plan and new admission.

`pixelMatrixHash` is SHA256 of canonical UTF-8 JSON containing schema
`static-collective/rgba-pixel-matrix/v0`, width, height and mode RGBA, then NUL,
then row-major RGBA8 bytes. It includes hidden RGB at alpha zero. This is exact
matrix identity, not perceptual equivalence. `encodedArtifactSha256` hashes
PNG bytes separately. Tests demonstrate identical raw pixels with a different
PNG encoding, and different zero-alpha RGB matrices that look identical over
opaque backgrounds. Visibility, exact pixels and file bytes remain distinct.

Execution requires the separately bound admission before any raster work.
Canonical execution writes three transparent full-canvas layer witnesses,
a final manga-page.png, exact receipts, the original plan/proposal/admission,
a readable trace and a renderer-neutral return basis. Each contribution retains
its useHash, 003 admission/role/placement hashes, promoted asset id, admittedUseId,
source SHA, full foreign locator, 001/002/003 event lineage and exact raster
recipe. The return basis adds complete 004 plan/proposal/admission/execution
lineage with no house admission or publication state change.

Independent verification replays the complete earlier custody and composition,
recompiles the plan from exact inputs/environment, reconstructs the separate
admission, rerenders in a temporary directory and compares every persisted byte.
Create-only persistence permits identical replay and refuses conflicts. Canonical
execution cannot write inside source, harvest, release or performed evidence.
No output is sent to LemonPRESS.

The executable doors are:

```sh
python -m haunted_blender.manga_pixel_execution_cli prepare \
  SOURCE_ROOT HARVEST_EVENT RELEASE_EVENT PERFORMED_EVENT PROPOSAL_OUT \
  --use ADMITTED_USE_DIR --authority-ref PROPOSER
# Only after separate exact approval/declaration:
python -m haunted_blender.manga_pixel_execution_cli execute \
  SOURCE_ROOT HARVEST_EVENT RELEASE_EVENT PERFORMED_EVENT PIXEL_EVENT_OUT \
  --use ADMITTED_USE_DIR --plan plan.json --proposal proposal.json \
  --admission admission.json
python -m haunted_blender.manga_pixel_execution_cli verify \
  SOURCE_ROOT HARVEST_EVENT RELEASE_EVENT PERFORMED_EVENT PIXEL_EVENT_OUT \
  --use ADMITTED_USE_DIR --plan plan.json --proposal proposal.json \
  --admission admission.json
```

The founding preparation is `python specimens/mangalize-004/prepare.py`.
It consumes the exact actual #66 performed state. Its original pending trace
remains unchanged. `ADMISSION_REQUIRED.md`, `VERIFICATION.md` and the prepared
trace record the earlier approval boundary; `EXECUTION_VERIFICATION.md` and
`FINAL_TRACE.md` record the later admitted consequence. A later explicit user
approval binds exactly layout
`fa198528b8454af1cb06ec3dde25c70d57db667f67591ac65234f3d12cebc46a`, plan
`b3203f8c3d9dfd0b080d149efca9de13fa266675833f08b803187925cbdc6a1a` and proposal
`2b8c9e795571f6e5ca7116d1046f761611ff2b1f789f4d86c37588561d8dfc2b`.
The separate recorded approval and admission authorize only pixel execution.
Earlier performedUse authority still keeps rendering closed; it was not edited.

The real execution is `specimens/mangalize-004/executed/`. It contains the
three 640×360 full-canvas layer witnesses and final RGBA PNG (922098 bytes each).
Final encoded SHA256 is
`2fc8d655c634c8b8ed5f986dc052dc3970b2fad4c9dfaac2cb676ab7e0e85c74`;
pixel-matrix hash is
`ee94091bcc3bfe2fc4deb6a8986cf47df3a448b57fcde0ea47ed57e7390b9ca5`.
Execution hash is
`c5adf79d7704c664145c079ea8d57ac0d2ba0ee1b1b40fa24bc38f613f4e5b0f`.
All three raster boxes are disjoint and entirely within the canvas: poster
`[32,48,160,240]`, cutaway `[224,72,320,216]`, texture `[448,48,576,240]`.
Every clipping extent is zero. Synthetic overlap and clipping tests establish
the rules beyond this particular unclipped, disjoint founding specimen.

Run `python specimens/mangalize-004/verify_founding.py /tmp/independent-pixels`
to consume the exact recorded approval, replay all earlier events and compare
every byte in a separately produced event tree. It never issues a new admission.
The dedicated CI job requires matching implementation/native-binary witnesses
before running the complete suite and exact founding replay. Foreign ABI jobs
test refusal while still verifying already-rendered PNG and matrix identities.

Synthetic success uses an independent temporary page with fictional source
identities and explicit fictional authorities. Tests cover exact plan/proposal,
read-only planning, integer and refused fractional geometry, 2×/2.4× dimensions,
half-up ties, alpha preservation/quantization, sampling/environment binding,
actual overlapping-layer z/source-over consequences, clipping, per-use custody,
return boundaries, raw/encoded identities, fresh-process replay, tampering and
unchanged historical witnesses. No synthetic authority admits the real page.

Unproven: cross-environment
pixel/byte equivalence, other samplers/encoders, fractional placement, rotation,
crop/time grammar, video/motion, sound, semantic recognition/casting, publication,
external generation, permission expiry/revocation and authenticated signatures.
The real texture witness retains 20 `(255,255,255,0)` pixels after opacity
quantization. Their hidden RGB changes its exact matrix identity. No extra
normalization occurs. The declared source-over operation leaves transparent
destination pixels unchanged at those positions in the final composite; the
intermediate witness retains the earlier exact bytes. VISIBILITY != PIXEL
IDENTITY; PIXEL IDENTITY != ENCODED-FILE IDENTITY; ZERO ALPHA != ABSENT RGB.

The rendered page contains 48744 nonzero-alpha pixels and 181656 zero-alpha
pixels. Its white texture reaches alpha 89. This exposes a bounded presentation
aperture: exact transparent pixels now exist, but their visible contrast depends
on a viewer or substrate background that was never authored. A presentation
background would be a later declared consequence, preserving this RGBA ancestor;
its choice and any publication authority remain unproven.
