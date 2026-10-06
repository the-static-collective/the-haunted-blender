# MANGALIZE-005 — presentation ground

An exact transparent manga page and an independently authored ground can produce
a new presentation projection. The page remains its exact ancestor. This work
starts directly on draft #67 at `49e9400d3753a6a308317eef8bd5b1fb93cc5322`.
117 historical specimen files and nine implementations (including read-only
008l) are frozen in `specimens/mangalize-005/ANCESTOR_PIN.json`.

The founding transparent parent is PNG / RGBA8 / 640×360:

- page pixel matrix: `ee94091bcc3bfe2fc4deb6a8986cf47df3a448b57fcde0ea47ed57e7390b9ca5`
- page encoded SHA256: `2fc8d655c634c8b8ed5f986dc052dc3970b2fad4c9dfaac2cb676ab7e0e85c74`
- 004 execution: `c5adf79d7704c664145c079ea8d57ac0d2ba0ee1b1b40fa24bc38f613f4e5b0f`

Five canonical event families use the existing sorted-JSON/SHA256 and create-only
machinery:

| Schema | What it binds | Authority |
| --- | --- | --- |
| `static-collective/manga-presentation-ground/v0` | Both exact page identities, dimensions, solid RGBA parameters, intent, semantics and implementation | None |
| `static-collective/manga-presentation-proposal/v0` | Exact 004 execution and complete custody, ground, output and semantics | None |
| `static-collective/manga-ground-comparison/v0` | Unadmitted candidate hashes and independently reproducible numeric observations | None; no selection or ranking |
| `static-collective/manga-presentation-admission/v0` | Exact proposal/ground/page identities and external authority declaration | Presentation only |
| `static-collective/manga-presentation-projection/v0` | Distinct output matrix/file identities, parent, ground, admission, recipe and observations | Presentation only |

The internal parent descriptor is derived from the exact sealed 004 execution.
The public prepare/execute/verify paths independently replay all four ancestor
events using their existing admissions, compare the whole 004 execution tree,
and verify the actual parent PNG SHA and matrix identity. Pure factories bind
this already verified descriptor; they do not confer custody or human authority.
External declarations remain accountable references, not authenticated signatures.
The CLI cannot issue an admission. A proposal, 004 pixel admission or candidate
comparison cannot admit presentation.

Only `kind=solid-rgba` is implemented. Parameters are four explicit integer
RGBA8 channels with alpha exactly 255 and `materialProfile=null`. There is no
default ground, RGB inference or automatic color choice. Unknown kinds, material
profiles and translucent grounds refuse. A later version could introduce a
separate material-ground branch; v0 does not claim to implement it.

008l's paper/cardboard/inked/junk-collage presets alter surface pixels and can
affect motion/directing. They remain separate from this context-only operation.
005 never invokes materialization, grain, lighting, blur or physics. An encoded
screen color names neither print stock nor calibrated paper reflectance.

## Exact pixel rules

Use inherited Pillow 12.1.1 `Image.alpha_composite(opaqueGroundRGBA, pageRGBA)`.
There is no resize, crop, page transform, mode conversion, enhancement, gamma,
profile or linear-light processing. Every projection alpha byte is 255. For each
color channel and opaque ground, the pinned implementation reduces to:

```text
N = sourceChannel * sourceAlpha + groundChannel * (255 - sourceAlpha)
Q = 128 * N + 16384
outputChannel = ((Q >> 8) + Q) >> 15
outputAlpha = 255
sourceAlpha = 0: copy the ground exactly
```

This declares Pillow's 7-bit coefficient precision and SHIFTFORDIV255 rounding,
rather than silently substituting a different integer blend. Tests independently
check all 256 source-alpha values for several nontrivial channel/ground pairs.
The engine is the inherited native operation, not a second implementation.

Witnesses bind this module's exact SHA and the whole 004 raster dependency:
004 module SHA, Pillow/Image.py/native binary SHA, Python ABI, system and machine.
Different implementation/dependency witnesses require new ground/proposal
identities and a new admission. Cross-witness equivalence is unproven.

Encoding reuses 004's deterministic RGBA8 PNG serializer: filter 0, uncompressed
stored blocks, no optional metadata. Matrix identity reuses its canonical
dimension/mode header plus NUL plus row-major RGBA bytes. The resulting
`presentationPixelMatrixHash` and `presentationEncodedArtifactSha256` remain
distinct from `pagePixelMatrixHash`, the parent encoded SHA and `groundHash`.
Hidden zero-alpha page RGB has no visible contribution to an opaque projection,
but remains in the bound parent matrix/file identities. No parent normalization
occurs. The original texture witness's 20 hidden white RGB pixels remain part
of 004 history even though the final transparent page contains no nonzero hidden
RGB. INVISIBLE CONTRIBUTION TO PROJECTION != ABSENCE FROM PARENT.

## Observation and admission boundary

The user requested candidate evidence before editorial selection. `compare`
computes ephemeral prospective matrices using the same pinned compositor and
persists only hashes, counts and histograms. It never encodes, saves or displays
a candidate image; it creates no projection/execution/admission artifact. A
forecast matrix hash is explicitly named `predictedPresentationPixelMatrixHash`.
It is not evidence that an admitted presentation was executed. Tests prevent
PNG encoding/image saving during this observation path.

Observations include exact unique RGB counts; the full encoded-channel luma
histogram; zero/partial/opaque parent-alpha counts; hidden RGB count; partial
RGB changes; pixels matching the ground; and absolute luma-difference histograms
for all pixels, nonzero-alpha pixels and partially transparent pixels.

The bounded proxy is `Y8=floor((2126R+7152G+722B+5000)/10000)`, computed with
integer half-up arithmetic. This is encoded-channel luma, not linear luminance,
WCAG contrast, physical reflectance or aesthetic quality. No measurements rank,
prefer, select, identify subjects or grant rights. Candidate array transport
ordering is normalized by groundHash/proposalHash, an identity ordering only.

After separate exact external admission, execute writes a new `presentation.png`
and ground/proposal/admission/projection records plus trace. It grants only
`presentation=true`; publication, printAdmission, motion, sound,
externalGeneration, characterCasting and sourceMutation remain false.
Create-only persistence compares every event-tree byte against independent
replay and refuses conflicting bytes. Output paths cannot enter any ancestor
custody directory. Multiple independently admitted grounds may produce sibling
projections without a universal selected presentation or source replacement.
The receipt retains the full 004 return basis, including every use identity,
LemonPRESS locator and 001/002/003/004 event lineage. No return is sent to a house.

## Executable doors

```sh
python -m haunted_blender.manga_presentation_cli prepare \
  SOURCE HARVEST RELEASE PERFORMED PIXEL_EVENT CANDIDATE_OUT \
  --use ADMITTED_USE_DIR --rgba8 255 255 255 255 --rgba8 0 0 0 255 \
  --rgba8 128 128 128 255 --intent 'unselected display comparison' \
  --authority-ref PROPOSER
# After a separate exact external admission exists:
python -m haunted_blender.manga_presentation_cli execute \
  SOURCE HARVEST RELEASE PERFORMED PIXEL_EVENT PROJECTION_OUT \
  --use ADMITTED_USE_DIR --ground ground.json --proposal proposal.json \
  --admission admission.json
python -m haunted_blender.manga_presentation_cli verify \
  SOURCE HARVEST RELEASE PERFORMED PIXEL_EVENT PROJECTION_OUT \
  --use ADMITTED_USE_DIR --ground ground.json --proposal proposal.json \
  --admission admission.json
```

`--use` is repeated for the exact three existing 003 bundles. `--rgba8` and intent
are required; there is no automatic white, paper or black fallback.

Run `python specimens/mangalize-005/prepare.py /tmp/ground-candidates` for the
founding numeric witness; compare it with `specimens/mangalize-005/prepared`.
The original three unselected probes are white `[255,255,255,255]`, black `[0,0,0,255]`
and encoded mid-gray `[128,128,128,255]`. They test encoded endpoints and the
positive-half-up midpoint; none is preferred. Exact hashes and complete numeric
evidence are in `ADMISSION_REQUIRED.md`, `prepared/TRACE.md` and `comparison.json`.
That prepared witness remains unchanged. `ADMISSION_REQUIRED.md`, `VERIFICATION.md`
and `prepared/TRACE.md` describe the earlier approval boundary. A later explicit
user decision separately selects and admits only the exact black pair:

- ground: `46cd7ab3f6db99f094ea2418b5a7714f9eef7f1b21e06475a557a72c31e8dc00`
- proposal: `b77659b847ae2d5721eb3d35fad22aa36e0de43d16a479c3f6ba1a85f33a3041`
- recorded selection SHA: `c14797ef1acd1947e525ee19ba6f7ee196edcdad388bc3c24985a9d913ff582d`
- admission: `8cc0badfb670ac12fec6cf68574a8d23353d42b8e7113b897552d5dc5944c7b0`
- projection: `adf2590208fd815728b3060b2a9c3fdab72272c11182e09b77ff2453b250510a`

The resulting `specimens/mangalize-005/projected/presentation.png` is a separate
opaque RGBA8 / 640×360 / 922098-byte descendant. Presentation matrix hash is
`a16a6d1528b88135c5ba901da6c36e14fcff49a3250ed137899716ef607f4a9a`;
encoded artifact SHA256 is
`bb9f9e41bb8694ee71f4d9316623e6cb4879881dc590f49eacb513ceaf622fe0`.
Its observations exactly match the prospective black comparison. The transparent
ancestor remains independently addressable at `specimens/mangalize-004/executed/manga-page.png`.

The user's diagnostic selection reason is recorded separately from measurement:
partial-alpha absolute encoded-luma difference 1–89 and 140 unique RGB colors.
This establishes no universal preference, canonical background, print stock,
source intent or value function. White and mid-gray retain only their original
unadmitted proposals and numeric observations; no real sibling projections exist.
New laws are retained in the recorded approval without changing the approved
ground, proposal or implementation witnesses: SELECTION != UNIVERSAL PREFERENCE;
ZERO PRESENTATION CONTRAST != ABSENT PERFORMED USE; VISIBILITY != ANCESTRY.

Run `python specimens/mangalize-005/verify_founding.py /tmp/independent-black`
to consume the exact recorded external selection and existing admission, replay
all earlier events and compare every byte of the real black projection tree.
It never issues admission or selects another ground. `EXECUTION_VERIFICATION.md`
and `FINAL_TRACE.md` record the later consequence with full custody.

Synthetic full-success tests use the existing synthetic four-event custody
fixture and fictional presentation authority. They prove distinct sibling
grounds, exact replay in a fresh process, opacity/hidden RGB, identity boundaries,
no transforms, ancestry, non-authorities, tampering and immutable ancestors.
The dedicated CI workflow requires the exact founding witness, runs the full
suite and independently replays both the numeric comparison and admitted black
projection. Foreign-ABI jobs test refusal while checking existing artifact identities.

Unproven: cross-witness pixel/file equivalence; calibrated display/print colors; physical
paper; procedural/material grounds; multiple translucent grounds; motion,
sound, publication, printing, external generation, casting and signed authority.

The candidate evidence exposes a precise boundary: all 10344 partial-alpha
white page pixels would match a white ground, while black and mid-gray yield
different bounded contrast distributions. A performed use and its ancestry
survive even when presentation contrast is zero. External selection now authors
one diagnostic black context; numeric observations did not make that decision.

The first real projection resolves every output alpha byte to 255. Its PNG has
no optional metadata and does not itself express which visible pixels were
ground versus page contributions; the bound transparent ancestor and receipts
retain those facts. This exposes presentation custody during viewing or exchange:
how can an opaque projection stay accompanied by its exact context, original
page and contribution identities without treating visible pixels as ancestry?
