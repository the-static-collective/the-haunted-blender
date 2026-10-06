# MANGALIZE-002 — Quarantine release

A harvested artifact can receive a later authority event without acquiring a
different past. This experiment starts directly on draft PR #64 at
`268d31f4a5283ce96209e3f7957edcfa2df30a7b`. The original request, refusal,
harvest-only grant, execution, return, page source, and all pixels remain unchanged.
LemonPRESS remains read-only at `88978ff88f9b07a72040976b426b04afc2abd835`.

```text
MANGALIZE-001 closed return
    ↓ independently verified exact 25-member quarantine witness
explicit selection (no rights)
    ↓ independently supplied later grant, bound to selected ids + SHAs
promotion (new authority-use identity; original asset identity and pixels)
    ↓
008h Parts Drawer
    ↓ generic provenance envelope, proposal only
later role/stage boundary
```

## Immutable event grammar

| Schema | Exact binding |
| --- | --- |
| `static-collective/manga-quarantine-set/v0` | All four 001 event hashes, full foreign ancestry, complete ancestor file inventory, exact member ids/SHAs/kinds/recipes, source/harvest identities, six closed permission dimensions, quarantine reason. |
| `static-collective/manga-quarantine-selection/v0` | Quarantine identity/hash, prior event, ancestry, explicit unique selected ids and SHAs, selecting authority and mechanical reason; no permissions. |
| `static-collective/quarantined-asset-grant/v0` | Quarantine and selection hashes, exact 001/source ancestry, explicit subset of selected ids/SHAs, separate granting authority, all six boolean permissions, granted operations and non-grants. Harvest must remain false. |
| `static-collective/manga-quarantine-promotion/v0` | All prior bindings, each original asset identity/recipe/hash/ancestry, new authority-use identity, exact effective permissions, promoted subset, still-quarantined siblings, no artifact changes, no execution/publication/staging authority. |

Each record has `verb: MANGALIZE`, `experiment: MANGALIZE-002`, deterministic
content hash and identity. Existing 008m canonical JSON/SHA-256, 001 duplicate-key
reader, exact file binding, create-only persistence, and independent replay are
reused. There are no timestamps, value scores, source rewrites, automatic all-set
promotion, or revocation/expiry semantics.

The quarantine witness is rebuilt by independently replaying the original 001
event. It captures historical arrival with all six dimensions closed. A later
promotion never edits that witness. A selected but ungranted candidate remains
quarantined. Unselected siblings cannot inherit a later grant through a shared
source or harvest. Quarantine does not imply rejection or deletion.

## Rights and actual consequences

The external grant factory requires explicit candidate ids and six booleans.
It refuses harvest and refuses a selecting authority self-authorizing. No CLI
door creates or infers a grant. Declaration references are inspectable external
assertions, not signatures or proof of a person's identity. Human authorization
must precede issuing a real declaration.

| Grant | Consequence in 002 |
| --- | --- |
| reuse only | Cannot perform derivative operation or enter the creative drawer. |
| derivative only | Cannot supply pixel reuse or enter the drawer. |
| reuse + derivative | Only named exact assets may enter the creative candidate drawer. |
| publication/motion/sound false | Remain independently false; derivation cannot imply them. |
| harvest true | Refused: 002 does not perform or re-grant harvesting. |

The promotion executor performs only bounded reuse/derivative admission. Other
rights can be represented independently, but no publisher, animator, sound
engine, external generator, or final-page admission is implemented here.

## Same artifact, later authority

Drawer row `id` remains the original harvested asset id. `admittedUseId` is a
distinct content-addressed authority-use identity, not a replacement image.
The row retains the exact old PNG path, SHA and transform recipe. No image is
copied, encoded, rendered, or changed. Drawer files use `pathBase: material-root`;
resolve them with the original 001 event as explicit `artifact_root`.

008h's existing drawer schema and still/crop/mask vocabulary are reused through
a shared `index_materials` constructor. Legacy drawer output remains unchanged.
The original quarantined harvest still refuses its old drawer bridge.

The generic `haunted-blender/material-provenance/v1` envelope carries:

- original asset and pixel/source identities;
- exact foreign ancestry, including all seven LemonPRESS locator fields;
- original event payload plus all four 001 request/admission/execution/return hashes;
- quarantine, selection, grant and promotion identities/hashes;
- authority-use identity, original transform recipe, effective rights and excluded authority.

`parts_harvester.select_for_stage` now preserves that envelope and asset id when
producing **proposal-only** material. Legacy foreign rows also get an envelope;
opaque ancestry from other systems and future envelope extensions survive.
Envelope carriage grants no staging or semantic identity. The boundary is tested
without performing narrative staging or changing any scene.

## Command doors

```sh
python -m haunted_blender.manga_quarantine_cli quarantine \
  specimens/mangalize-001/lemonpress specimens/mangalize-001/executed \
  /tmp/quarantine-set.json
python -m haunted_blender.manga_quarantine_cli select \
  /tmp/quarantine-set.json /tmp/selection.json \
  --source-root specimens/mangalize-001/lemonpress \
  --ancestor-event specimens/mangalize-001/executed \
  --candidate EXACT_ASSET_ID --authority-ref EXPLICIT_SELECTOR \
  --reason 'explicit geometry selection' --trace /tmp/selection-trace.md
```

That door ends at `SELECTION READY — GRANT REQUIRED`. Once a valid independently
issued grant exists, `promote` and `verify` take the same six arguments:

```sh
python -m haunted_blender.manga_quarantine_cli promote \
  QUARANTINE_JSON SELECTION_JSON EXTERNAL_GRANT_JSON \
  SOURCE_ROOT ANCESTOR_EVENT_ROOT NEW_PROMOTION_DIRECTORY
python -m haunted_blender.manga_quarantine_cli verify \
  QUARANTINE_JSON SELECTION_JSON EXTERNAL_GRANT_JSON \
  SOURCE_ROOT ANCESTOR_EVENT_ROOT EXISTING_PROMOTION_DIRECTORY
```

Independent verification reconstructs quarantine from the unchanged ancestor,
selection from exact members, grant from its exact declaration, promotion from
that authority subset, and drawer/trace from those results. Full byte inventories
must match. Rehashed false claims in persisted records cannot bypass that replay.
Modifying a source, candidate, set, selection, grant, promotion or drawer refuses.
Output cannot be written inside ancestor evidence. The external declaration is
an input trust boundary, not self-authenticating rights evidence.

## Prepared founding selection and approval boundary

The [prepared quarantine](../specimens/mangalize-002/prepared/quarantine-set.json)
contains the exact 25 closed 001 descendants. The
[selection](../specimens/mangalize-002/prepared/selection.json) names exactly one
panel-crop, its center region, and its nonsemantic edge mask. This exercises three
drawer kinds with geometry alone and makes no character or panel-semantic claim.

The [prepared trace](../specimens/mangalize-002/prepared/TRACE.md) and
[bounded grant request](../specimens/mangalize-002/GRANT_REQUIRED.md) preserve the
historical `SELECTION READY / GRANT REQUIRED` boundary. The user then explicitly
approved only the three named asset ids and exact SHAs. The separate
[later grant](../specimens/mangalize-002/grants/selected-assets.grant.json) applies
only to those exact artifacts, with reuse/derivative true and harvest,
publication, motion and synthesized sound false. Neither selection nor the old
harvest-only grant supplied this later authority.

The [actual promotion](../specimens/mangalize-002/released/promotion.json) admits
exactly those three into the [real 008h drawer](../specimens/mangalize-002/released/parts-drawer.json):
one still, one crop, one mask. All 22 unselected siblings remain quarantined.
The complete [final event trace](../specimens/mangalize-002/released/TRACE.md)
names every promoted and still-quarantined identity and SHA.

```text
quarantineSetHash  3581496f5329becd1a0de79b1cbe1d8191f5efa00ef30f7ac23e37076109d0cd
selectionHash      a43dc069178e0ad83422bdc5390553675777d1c9c6a56fd9b5fe7b2291074be2
grantHash          fd74e477c58228ad08adc919dc8c89123d3b1dbe2b3be82611e563b71ea40c1b
promotionHash      a2012b0a796061566145ffadd63fa428c4ce19a55035f2bd9bb7b0cda089be8c
drawerId           parts-drawer:908a820fdbfdf1fa35dcf7a2
```

The [proposal boundary witness](../specimens/mangalize-002/witnesses/material-proposal-boundary.json)
mechanically carries the complete provenance envelope for every actual promoted
asset through 008h's existing generic role proposal. It remains `proposal-only`:
no narrative staging, placement, rendering, motion or sound is performed.

To replay the actual founding event:

```sh
python -m haunted_blender.manga_quarantine_cli promote \
  specimens/mangalize-002/prepared/quarantine-set.json \
  specimens/mangalize-002/prepared/selection.json \
  specimens/mangalize-002/grants/selected-assets.grant.json \
  specimens/mangalize-001/lemonpress specimens/mangalize-001/executed \
  /tmp/mangalize-002-replayed
python -m haunted_blender.manga_quarantine_cli verify \
  specimens/mangalize-002/prepared/quarantine-set.json \
  specimens/mangalize-002/prepared/selection.json \
  specimens/mangalize-002/grants/selected-assets.grant.json \
  specimens/mangalize-001/lemonpress specimens/mangalize-001/executed \
  specimens/mangalize-002/released
```

Independent full-success permission tests use newly generated temporary synthetic pixels,
distinct fictional publication identities, fictional granting authorities, and
their own harvest-only 001 event. They do not promote the real founding assets.

`ANCESTOR_PIN.json` and `check_parent.py` compare 47 old evidence/implementation
files byte for byte against the exact read-only #64 parent commit, including all
original source files, PNGs, refusal receipts and harvest-only authority.

## Validation

The complete inherited suite plus 35 new quarantine-release tests passes:
**355 tests, no skips**. The additional founding checks independently replay the
real approved promotion and its exact material-proposal witness.
The new suite proves deterministic quarantine/selection/grant/promotion replay,
exact bytes and ancestry, sibling isolation, selected-but-ungranted refusal,
independent permission dimensions, generic proposal envelope carriage, and
rehashed tamper refusal. Syntax checks, exact parent comparison (47 unchanged
files), and the pinned LemonPRESS foreign witness are checked alongside the real
founding promotion. CI verifies the committed receipt inventory independently.

## Founding laws and held meanings

```text
HARVESTED != REUSABLE
QUARANTINED != REJECTED
QUARANTINE != DELETION
SELECTION != AUTHORIZATION
NEW GRANT != EDIT TO OLD GRANT
NEW AUTHORITY != NEW PAST
LATER AUTHORITY DOES NOT REWRITE EARLIER CUSTODY
REUSE != DERIVATION
DERIVATION != PUBLICATION
DERIVATION != MOTION
DERIVATION != SOUND
SHARED SOURCE != SHARED AUTHORITY
SHARED EVENT != SHARED LATER GRANT
ANCESTRY CARRIAGE != STAGING AUTHORITY
PROMOTED DESCENDANT RETAINS FOREIGN ANCESTRY
PROMOTION != PUBLICATION
PROMOTION != STAGING
PROMOTION != ANIMATION
```

No revocation, expiry, semantic character recognition, narrative staging,
editorial admission, scene performance, animation, sound, publishing, or final
page construction is proven.

## Aperture exposed by the actual promoted material

The real drawer contains an exact still, crop, and nonsemantic mask with creative
material permission and complete custody. The repaired role/proposal boundary
carries that custody intact, while all staging authority remains closed.

Read-only inspection of the next existing stage-dressing consumer shows that it
still resolves raw paths directly and reduces its witnesses to source/artifact
hashes and harvest ids. It does not yet consume the new provenance envelope or
an independently admitted performed-use record. No stage-dressing call was made
with these founding assets.

The aperture exposed here is candidate/proposal → explicitly admitted performed
use: how can a later role, placement and transform bind the exact promoted asset,
its authority-use identity, full ancestry and applicable permissions without
turning a geometry candidate into semantic character evidence?
