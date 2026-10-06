# FRANKEN BLENDER 008m — MANGA / ANIME GRAMMAR ATLAS

008m treats comic pages as two things at once:

```text
PAGE
 ├─ PIXELS / PARTS
 └─ GRAMMAR / RHYTHM
```

Those two authorities are deliberately separate.

A page may be useful for grammar even when its pixels are not authorized for reuse.

## Owned Drive batch 001

The user explicitly confirmed that the eight inspected pages from Drive folder `1wt_hKrvkmWAOgmNBDi-KQPW0H2E9tkv5` are owned pixels and may be reused.

That authority is frozen in:

```text
docs/fixtures/008m-owned-drive-batch-001.json
```

The declaration is intentionally **exact-file-list scoped**. Later additions to the Drive folder do not inherit ownership authority automatically.

```text
OWNED BATCH AUTHORITY
  → pixel reuse YES
  → derivative reuse YES
  → publication reuse YES

BUT

REMOTE FILE ID != BYTE SHA
```

Each downloaded page must still be materialized locally and SHA-256 frozen before 008m exports derivatives.

## Founding source classes

008m begins with two distinct specimen classes from the current experiment.

### Owned Static Collective page

The Static Collective kitchen / table / chair page is treated as an **owned harvest anchor** when the user marks it owned.

Its useful domains include:

```text
cozy ensemble blocking
room ecology
table staging
object continuity
environment pauses
quiet-surreal rhythm
return tableau
```

When its manifest grants pixel + derivative reuse, every pixel may be disassembled into candidate parts.

### Anime / MangaBoom page

The anime action/reaction page is useful as an **anime grammar source**:

```text
eye inserts
speed lines
impact composition
reaction beats
chibi deformation
foreshortened action
dramatic close-ups
panel overlap
```

If its output rights are not explicitly established, its source class remains `reference`.

That means:

```text
GRAMMAR ANALYSIS: YES
PIXEL EXPORT:      NO
```

until a manifest explicitly grants otherwise.

## Owned collection policy

The Static Collective manga folder is now modeled as a rights-bearing collection:

```text
haunted-blender/page-source-collection/v1
```

The current privacy-safe repository snapshot contains **14 PNG members**:

```text
specimens/008m/static-collective-owned-page-collection-001.json
```

The user explicitly declares the collection's pixels owned and reusable for:

```text
pixel reuse
derivative reuse
recomposition
publication
```

The collection also freezes:

```text
futureMembersInherit = true
```

A future page deliberately placed into this owned collection may inherit the same rights policy when ingested.

Collection authority never replaces byte custody:

```text
COLLECTION RIGHTS
      ↓
membership authority

ACTUAL INGESTED PAGE
      ↓
fresh SHA-256
      ↓
page-source manifest
      ↓
harvest authority
```

```text
COLLECTION RIGHTS APPLY TO DECLARED MEMBERSHIP NOT UNKNOWN BYTES
EACH INGESTED PAGE STILL REQUIRES ITS OWN SOURCE SHA
```

The repository collection snapshot intentionally omits private Drive URLs and Drive file ids. Current member filenames plus later per-page SHA custody are sufficient for the public artifact.

## Source manifest

Every page enters through:

```text
haunted-blender/page-source/v1
```

The manifest freezes:

- exact source SHA-256
- dimensions
- source class
- reuse rights
- rights note
- grammar families

Source classes:

```text
owned
licensed
reference
```

Reuse rights are independent booleans:

```text
pixelReuse
derivativeReuse
publicationReuse
```

A `reference` source is forbidden from self-granting reuse rights.

```text
SOURCE OWNERSHIP DETERMINES HARVEST AUTHORITY
GRAMMAR ANALYSIS != PIXEL REUSE AUTHORITY
```

## Geometry-only panel map

008m performs a deterministic whitespace XY-cut pass using Pillow only.

It finds large gutter-separated regions and records:

```text
x / y
width / height
area ratio
aspect ratio
geometry class
edge density
clean-plate candidate
```

Geometry classes:

```text
wide
tall
balanced
insert
```

The detector makes no character or object claims.

The founding uploaded specimens also showed that manga pages may use heavy dark borders and overlapping composition instead of clean white gutters. 008m therefore has a second continuous-dark-border fallback. It only activates when the whitespace pass finds no useful subdivision.

```text
WHITE GUTTER DETECTION
        OR
DARK BORDER DETECTION
        ↓
GEOMETRIC PANEL CANDIDATES
```

```text
PANEL MAP IS GEOMETRY, NOT SEMANTIC UNDERSTANDING
```

## Owned-page pixel harvest

If and only if the source manifest grants both:

```text
pixelReuse = true
derivativeReuse = true
```

008m may export pixels.

Current first-pass derivatives:

- full panel crop
- center region candidate
- NW / NE / SW / SE region candidates
- non-semantic edge mask

Every derivative binds:

- source id
- source SHA-256
- panel id
- derivative SHA-256
- exact transform recipe

```text
OWNED OR LICENSED PAGE MAY BE DISASSEMBLED
HARVESTED ASSET != CHARACTER IDENTITY
EDGE MASK != SEMANTIC SEGMENTATION
```

This is deliberately the safe primitive layer below later character/prop/FX selection.

## Grammar families

Initial atlas families:

```text
cozy-ensemble
anime-action
reaction
panel-rhythm
room-ecology
fx
threshold-transition
environmental-establishing
intimate-dialogue
object-detail
silhouette-negative-space
vertical-motion
recurring-location-continuity
sequence-rhythm
```

A report may belong to more than one family.

The atlas aggregates geometry/rhythm across reports while preserving every report's source identity.

```text
ATLAS AGGREGATES GRAMMAR NOT OWNERSHIP
OWNERSHIP DOES NOT TRANSFER BETWEEN SOURCES
```

## Registered owned collection snapshot

The earlier eight-page batch has been superseded by the rights-bearing **14-page owned collection** described above.

The old private-location witness is no longer the canonical public specimen. Current and future collection members inherit the user-declared ownership policy, while each actual image still receives an exact SHA-256 at ingestion.

```text
FOLDER MEMBERSHIP POLICY
        +
PER-PAGE SHA CUSTODY
        ↓
OWNED PAGE HARVEST AUTHORITY
```

## Multi-page sequence grammar

The new eight-page Drive batch adds something the first two specimens did not provide strongly enough: **continuity across pages**.

008m therefore accepts explicit page annotations:

```text
pageRole
continuityGroup
motifs
sequenceIndex
```

Supported initial page roles:

```text
establish
dialogue
threshold
detail
impact
vertical-transition
return
environment
mixed
```

These are annotations supplied by a human/tool workflow. They are not inferred semantic facts from pixels.

```text
PAGE ROLE IS ANNOTATION NOT PIXEL INFERENCE
```

A sequence grammar can then record:

- page-role order
- same-world / continuity grouping
- shared motifs between adjacent pages
- motifs recurring across the whole run
- per-page panel geometry rhythm

Example:

```text
ESTABLISH
  door + room
      ↓
DIALOGUE
  door + chair
      ↓
THRESHOLD
  door + light
      ↓
RETURN
  door + room
```

The recurring `door` may then become a callback candidate for 008j without requiring pixel reuse from every page.

```text
SHARED MOTIF MAY GUIDE CALLBACK
WITHOUT REQUIRING PIXEL REUSE
```

Sequence roles also map to weak shot-pattern proposals:

```text
establish            → ESTABLISH / WIDE
dialogue             → TWO_SHOT / SPEAKER / LISTENER / REACTION
threshold            → WIDE / CLOSE_UP / INSERT / RETURN
detail               → INSERT / CLOSE_UP / RETURN
impact               → CLOSE_UP / CHAOS / REACTION
vertical-transition  → WIDE / LYRIC_WORLD / CLOSE_UP / RETURN
return               → RETURN / WIDE
environment          → WIDE / INSERT / RETURN
```

Again:

```text
SEQUENCE PRESCRIPTION != EDITORIAL KEEP
```

## Page rhythm → Director proposal

008m can translate panel geometry into weak 008j-style shot suggestions:

```text
wide      → WIDE
tall      → CLOSE_UP
balanced  → SPEAKER
insert    → INSERT
```

Adjacent duplicate shot suggestions are repaired with a reaction / return beat.

This is grammar proposal only.

```text
PANEL RHYTHM MAY GUIDE SHOT RHYTHM
PANEL RHYTHM != SHOT PLAN
GRAMMAR PROPOSAL != EDITORIAL KEEP
```

## Command door

Create or refresh a local owned collection declaration:

```bash
python -m haunted_blender.manga_atlas_cli collection \
  ./owned-collection.json \
  --label "Static Collective Manga" \
  --collection-id static-collective-manga-owned-001 \
  --class owned \
  --pixel-reuse \
  --derivative-reuse \
  --publication-reuse \
  --future-members-inherit \
  --rights-note "User-declared owned manga collection."
```

Bind actual page bytes to that collection:

```bash
python -m haunted_blender.manga_atlas_cli source-from-collection \
  ./new-page.png \
  ./owned-collection.json \
  new-page.png \
  ./new-page.source.json
```

The second command hashes the real page bytes before harvest authority is exercised.

Create an owned page source:

```bash
python -m haunted_blender.manga_atlas_cli source \
  ./static-page.png \
  ./static-page.source.json \
  --class owned \
  --pixel-reuse \
  --derivative-reuse \
  --publication-reuse \
  --rights-note "User-owned Static Collective generated page." \
  --family cozy-ensemble \
  --family room-ecology \
  --family panel-rhythm
```

Create a reference-only anime source:

```bash
python -m haunted_blender.manga_atlas_cli source \
  ./anime-page.png \
  ./anime-page.source.json \
  --class reference \
  --family anime-action \
  --family reaction \
  --family panel-rhythm
```

Analyze either:

```bash
python -m haunted_blender.manga_atlas_cli analyze \
  ./page.source.json \
  ./page.report.json
```

Harvest authorized pixels:

```bash
python -m haunted_blender.manga_atlas_cli harvest \
  ./owned-page.source.json \
  ./film/manga-harvest
```

Bridge an authorized page harvest directly into the existing 008h Parts Drawer:

```bash
python -m haunted_blender.manga_atlas_cli drawer \
  ./film/manga-harvest/page-harvest.json \
  ./film/manga-parts-drawer.json
```

The bridge maps:

```text
panel             → still
region-candidate  → crop
edge-mask         → mask
```

and preserves the original page SHA and page-harvest id.

```text
PAGE PROVENANCE SURVIVES DRAWER BRIDGE
```

Build the atlas:

```bash
python -m haunted_blender.manga_atlas_cli atlas \
  ./manga-atlas.json \
  ./static.report.json \
  ./anime.report.json
```

Convert a report to Director proposals:

```bash
python -m haunted_blender.manga_atlas_cli director \
  ./static.report.json \
  ./static.director.json
```

Build multi-page sequence grammar:

```bash
python -m haunted_blender.manga_atlas_cli sequence \
  ./sequence.json \
  ./page-01.report.json \
  ./page-02.report.json \
  ./page-03.report.json
```

Translate that sequence into weak Director beat patterns:

```bash
python -m haunted_blender.manga_atlas_cli sequence-director \
  ./sequence.json \
  ./sequence.director.json
```

## Intended next composition

008m now directly bridges authorized owned-page pixels into the existing parts ecology:

```text
OWNED COMIC PAGE
      ↓
008m PAGE HARVEST
      ↓
008m → 008h DRAWER BRIDGE
      ↓
008h PARTS DRAWER
      ↓
008l MATERIAL GRAMMAR
      ↓
008k CAST / TABLE STAGING
      ↓
008j PAPER DIRECTOR
```

The important long-term target is not "turn comic into video" as one opaque operation.

It is:

```text
COMIC PAGE
   ↓
ACTORS
FX
PROPS
BACKGROUND PLATES
PANEL RHYTHM
ROOM GRAMMAR
REACTION GRAMMAR
   ↓
RECOMPOSABLE LOCAL FILM LANGUAGE
```

## Laws

```text
PAGE != FINAL FRAME
PANEL MAY BE DISASSEMBLED WHEN RIGHTS ALLOW
SOURCE OWNERSHIP DETERMINES HARVEST AUTHORITY
GRAMMAR ANALYSIS != PIXEL REUSE AUTHORITY
REFERENCE SOURCE MAY INFORM GRAMMAR WITHOUT EXPORTING PIXELS
PANEL MAP IS GEOMETRY, NOT SEMANTIC UNDERSTANDING
HARVESTED ASSET != CHARACTER IDENTITY
EDGE MASK != SEMANTIC SEGMENTATION
PANEL RHYTHM != SHOT PLAN
ATLAS AGGREGATES GRAMMAR NOT OWNERSHIP
OWNERSHIP DOES NOT TRANSFER BETWEEN SOURCES
```

## Stack consequence

```text
008e  COVERAGE
008f  TRIAGE
008g  ACTORS + SETS
008h  PARTS + BEHAVIORS
008i  MOVING SCREENS
008j  DIRECTOR
008k  CAST + DIALOGUE
008l  MATERIAL
008m  MANGA / ANIME GRAMMAR + OWNED PAGE HARVEST
```
