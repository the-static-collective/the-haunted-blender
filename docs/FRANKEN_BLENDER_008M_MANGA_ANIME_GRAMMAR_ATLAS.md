# FRANKEN BLENDER 008m — MANGA / ANIME GRAMMAR ATLAS

008m treats comic pages as two things at once:

```text
PAGE
 ├─ PIXELS / PARTS
 └─ GRAMMAR / RHYTHM
```

Those two authorities are deliberately separate.

A page may be useful for grammar even when its pixels are not authorized for reuse.

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
```

A report may belong to more than one family.

The atlas aggregates geometry/rhythm across reports while preserving every report's source identity.

```text
ATLAS AGGREGATES GRAMMAR NOT OWNERSHIP
OWNERSHIP DOES NOT TRANSFER BETWEEN SOURCES
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

## Intended next composition

008m establishes the rights/provenance and geometry layer required for:

```text
OWNED COMIC PAGE
      ↓
008m PAGE HARVEST
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
