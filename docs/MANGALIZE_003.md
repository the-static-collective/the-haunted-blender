# MANGALIZE-003 — performed use

A promoted artifact can acquire a structural role and explicit static placement
only through a separate external performed-use admission. The exact pixel
identity remains unchanged; use identity binds role, placement and admission.
No renderer is called. This experiment stacks directly on #65 at
`8b4f7da114e55150dfb564fea171c827bcf8759a`.

`manga_performed_use.py` reuses the canonical bytes, hashing, create-only
persistence and independent replay from 001/002. Five immutable schema families
separate role proposal, placement proposal, admission, performed use and layout.
Every event explicitly names MANGALIZE and MANGALIZE-003. There are no timestamps,
scores, implicit roles or generated geometry in the new path.

The founding grammar is deliberately static: explicit 64–16384 pixel canvas,
top-left origin/anchor, native-scale fit, canvas clipping, no crop and no time
range. Positions use integer millipixels, scale and opacity millionths, rotation
millidegrees, and z integer order. The fixed-point representation excludes bools,
floats, NaN, omitted transforms and implicit defaults. It is a composition
instruction, not a pixel result. Role vocabulary: poster, texture, cutaway, prop,
mask, insert. Semantic/object/character identity, source fact and semantic
segmentation are explicit nonclaims.

`stage_compost.plan` refuses automatic placement of material with an admitted-use
custody envelope or MANGALIZE event lineage. Earlier native experiments retain
their legacy path; generic provenance now travels on their layers and witnesses.
`stage_compost.admitted_plan` consumes exact proposals and separate admissions,
reconstructs each performed use, checks actual artifact bytes and returns a
static layout retaining the complete generic provenance envelope. It does not
return legacy renderable stage dressing. `apply_to_performance` cannot accept
the layout or route managed custody through the old execution door.

The generic envelope is deep copied, including unknown future extensions. Its
original authority remains historical. A new event-lineage entry records the
003 role/placement/admission hashes. The performed-use record carries the new
bounded action authority separately: performedUse true; render, motion, sound,
publication, external generation and character casting false. Existing pixel
permissions remain the material permission ceiling. No sibling inherits use.

The factories accept accountable external authority references, as in 001/002;
they do not authenticate humans or provide signatures. Issuing a real admission
requires separately recorded exact approval. Proposal and material-grant event
references cannot serve as performed-use admission. The CLI never issues an
admission; it must consume a separately supplied canonical declaration. Hash
verification establishes binding and replay, not the truth of an authority claim.

The executable doors are:

```sh
python -m haunted_blender.manga_performed_use_cli role \
  SOURCE_ROOT ANCESTOR_EVENT RELEASED_EVENT role.json \
  --asset EXACT_ASSET_ID --role poster \
  --authority-ref PROPOSER --rationale 'Bounded structural role proposal'
python -m haunted_blender.manga_performed_use_cli placement \
  SOURCE_ROOT ANCESTOR_EVENT RELEASED_EVENT placement.json \
  --role-proposal role.json --geometry explicit-geometry.json \
  --authority-ref PLACEMENT_AUTHOR --rationale 'Authored static placement'
# After separate authority exists, each USE_DIR holds role.json,
# placement.json and externally issued admission.json.
python -m haunted_blender.manga_performed_use_cli compose \
  SOURCE_ROOT ANCESTOR_EVENT RELEASED_EVENT EVENT_OUT --use USE_DIR
python -m haunted_blender.manga_performed_use_cli verify \
  SOURCE_ROOT ANCESTOR_EVENT RELEASED_EVENT EVENT_OUT --use USE_DIR
```

Every CLI door independently replays the complete 001/002 custody chain.
Composition and verification then independently reconstruct all admitted uses.
The event output contains original proposals/admissions, individual performed-use
records, a layout and readable trace; output is create-only and byte-identical
on replay, including across canonical file round trips and input ordering.
Conflicting persisted bytes refuse. No output may be written inside ancestor
evidence. Original pixels are referenced, never copied, rewritten or rendered.

The real specimen is prepared by:

```sh
python specimens/mangalize-003/prepare.py
```

It validates the exact promoted drawer then writes only three role/placement
pairs and a readable trace. The historical authority request with all exact SHAs, proposal
hashes and transforms is [ADMISSION_REQUIRED.md](../specimens/mangalize-003/ADMISSION_REQUIRED.md).
The actual page remains the pinned LemonPRESS synthetic page-05, never an
invented real-work admission. The complete foreign locator and 001/002 event
lineage are present in each proposal. All 57 historical 001/002 specimen files
are pinned byte for byte to #65.

Synthetic full-success tests use an independent temporary page with explicitly
fictional source identities and authorities. They prove deterministic proposals,
admission, performed-use and layout, no permission spread, no implicit placement,
multiple possible roles, distinct use identities for role/transform changes,
full custody through the repaired consumer, and refusal of tampered proposals,
admissions, layouts, pixels and persisted evidence. Tests also independently
replay the real approved composition and refuse reuse of its admissions with
otherwise-valid changed role or placement proposals.

The later explicit user approval is recorded separately in
`specimens/mangalize-003/authority/user-performed-use-approval.json`, exact SHA
`29bdefaa10ebb2605feaf7e84bb4e821ada3d2fc1848bb31bfed802ccb05ab5b`.
It binds all three exact prior proposal pairs, pixel identities, admittedUseIds,
roles and transforms. Each admission's external authority reference binds that
record's SHA. Approval permits performed use only; changing any bound proposal
requires a new admission. Prepared proposals and the earlier approval boundary
trace remain unchanged as historical evidence.

The actual approved composition has canvas 640×360, top-left origin/anchors,
native-scale fit, no crop/time range, zero rotation and explicit canvas clipping:

| Exact promoted material | Structural role | x/y pixels | z | Scale | Opacity |
|---|---|---|---|---|---|
| Panel | poster | 32 / 48 | 10 | 2 | 1 |
| Center crop | cutaway | 224 / 72 | 20 | 2.4 | 1 |
| Edge mask | texture | 448 / 48 | 30 | 2 | 0.35 |

The exact layout hash is
`fa198528b8454af1cb06ec3dde25c70d57db667f67591ac65234f3d12cebc46a`.
Original asset IDs/SHAs and material admittedUseIds survive. New use hashes:

- poster: `eff6dc9dfeb9fe550c2178f092497b2585366a5568250a996bd8268d1f6d65d3`
- cutaway: `ef892ad71e9925fe95fcf073c91309e4c1b8256f5968350a802b7c37a58756e5`
- texture: `7c77c2afb7f92d56464bf7c061b66c27eaaeb82c6ddf51ba5900fc515e97ebde`

Every performed-use record retains the exact LemonPRESS work, edition and hash,
issue, page, page hash, source-image SHA, pinned repository/commit and handoff
hash. It retains MANGALIZE-001 request/admission/execution/return and original
harvest recipe, MANGALIZE-002 quarantine/selection/grant/promotion identities,
the promoted admittedUseId and exact Parts Drawer, then adds MANGALIZE-003
role/placement/admission hashes. The original envelopes keep historical false
staging authority; a later performed-use authority lives on the new record.
All 22 unselected descendants remain quarantined. There are zero new pixels,
zero rendered artifacts and no house release change.

Inputs and separate admissions are archived in `admitted-inputs/`; canonical
uses, layout and the [complete event trace](../specimens/mangalize-003/performed/TRACE.md)
are in `performed/`. Verify and independently reproduce exact bytes with:

```sh
python specimens/mangalize-003/verify_founding.py /tmp/mangalize-003-replayed
```

This consumes the existing admissions and verifies their exact external
authority binding; it never issues new admissions or renders. The workflow
runs the complete inherited suite, checks pinned Blender/LemonPRESS witnesses,
replays both proposals and performed state, and uploads exact event artifacts.

Unproven: raster/video rendering,
motion, synthesized sound, publication, semantic recognition, character casting,
cropped/timed layouts, signatures, cross-system adapters beyond preserved
custody, permission expiry/revocation.

The first admitted composition exposes a precise remaining boundary: the crop's
2.4× scale and mask's 0.35 opacity are exact composition instructions, but no
pixel-execution witness yet binds sampling, alpha quantization or clipping to
that layout. A later separately authorized renderer would have to name those
choices and return exact pixels/receipts while retaining use identity. The
layout and material grants alone cannot open that door.
