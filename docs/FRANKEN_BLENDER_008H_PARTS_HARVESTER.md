# FRANKEN BLENDER 008h — PARTS HARVESTER / COMPOST MILL

008h changes the unit of video reuse.

```text
VIDEO
  ↓
DIGEST
  ↓
PARTS + BITS + BEHAVIORS
```

One clip is no longer merely one clip.

## Harvest outputs

Every source video can yield:

```text
STILLS
CROPS
TEXTURES
LUMINANCE MASKS
FORWARD LOOP
REVERSE LOOP
PING-PONG LOOP
ENTRANCE FRAGMENT
MIDDLE FRAGMENT
EXIT FRAGMENT
PALETTE
MOTION BEHAVIOR
```

All artifacts bind the original source SHA-256 and an explicit transform recipe.

```text
PART != SOURCE
DERIVATIVE != NEW EVIDENCE
```

## No fake semantic vision

008h deliberately does not claim that a crop contains a character, that a threshold mask is an object segmentation, or that a motion centroid belongs to a particular object.

```text
CROP != OBJECT IDENTITY
MASK != SEMANTIC SEGMENTATION
CHANGE CENTROID != OBJECT TRACK
```

This keeps the cheap local extraction honest and reusable.

## Motion behavior

The harvester samples low-resolution grayscale frames and records frame-to-frame change energy plus the centroid of changed pixels.

That becomes a small content-addressed motion-behavior artifact.

```text
appearance A
motion behavior B
      ↓
behavior transplant
      ↓
appearance A moves using B's observed motion pattern
```

Critically:

```text
BEHAVIOR != APPEARANCE
SOURCE MOTION != TARGET IDENTITY
TRANSPLANT != SEMANTIC CORRESPONDENCE
```

## Parts Drawer

Multiple harvests compose into one deduplicated `parts-drawer.json`.

The drawer indexes artifacts by kind while preserving each source and harvest identity.

```text
225 FLOW VIDEOS
      ↓
FLOW PANTRY
      ↓
BATCH HARVEST
      ↓
THOUSANDS OF REUSABLE BITS
      ↓
ONE PARTS DRAWER
```

Batch command:

```bash
python -m haunted_blender.parts_harvester_cli batch \
  /path/to/225-flow-videos \
  ./film/parts
```

An existing Flow Pantry manifest may also be supplied.

## Single clip

```bash
python -m haunted_blender.parts_harvester_cli harvest \
  candidate-001.mp4 \
  ./film/parts/candidate-001
```

## Stage selection

The drawer can propose material for:

```text
poster
screen
texture
cutaway
motion
```

Selection is proposal-only.

```text
DRAWER INDEX != SELECTION
SELECTION != EDITORIAL KEEP
```

## Puppet-world composition

008h adds a stage dresser for the 008g paper-puppet world.

It can use harvested stills/textures as posters and wall material. More importantly, it can animate a harvested crop with motion behavior from a different source.

```text
FLOW CLIP A
  → crop / appearance

FLOW CLIP B
  → motion behavior

A.appearance + B.behavior
  ↓
new paper-stage prop
```

Both provenances remain separate in the dressing witness.

## Moving bits remain moving

Loops and bounded fragments are not silently flattened into stills.

They remain explicit moving-insert proposals for:

```text
TELEVISION
WINDOW
PORTAL
DREAM
FLASHBACK
ADVERTISEMENT
BACKGROUND
```

The current still-image Cutout Stage does not automatically place them. That is deliberate: moving insert placement remains a separate compositional crossing.

## Puppet Studio integration

008g can now consume a drawer:

```bash
python -m haunted_blender.puppet_cli smash \
  puppet-spec.json \
  timing.json \
  ./film/puppet-pass \
  --parts-drawer ./film/parts/parts-drawer.json
```

The puppet receipt records the number of harvested stage layers and moving insert proposals.

## Derivative yield

The harvest receipt reports how many reusable artifacts one source produced.

That creates a useful economic measure:

```text
DERIVATIVE YIELD
=
reusable local ingredients / source clip
```

A rare generated video can therefore be valuable even if only a few seconds long, because its downstream local yield may be large.

```text
AI SECOND != ONE EDITED SECOND
ONE SOURCE MAY YIELD MANY DERIVATIVES
```

## Zero-dollar law

Harvesting, drawer construction, behavior transplantation, and stage dressing are local operations.

```text
externalGenerations = 0
providerCredits     = 0
usdMicros           = 0
```

## Laws

```text
PART != SOURCE
DERIVATIVE != NEW EVIDENCE
CROP != OBJECT IDENTITY
MASK != SEMANTIC SEGMENTATION
CHANGE CENTROID != OBJECT TRACK
BEHAVIOR != APPEARANCE
EVERY HARVESTED ARTIFACT BINDS SOURCE SHA256
DRAWER INDEX != SELECTION
APPEARANCE AUTHORITY != BEHAVIOR AUTHORITY
MOVING INSERT PROPOSAL != AUTOMATIC PLACEMENT
```
