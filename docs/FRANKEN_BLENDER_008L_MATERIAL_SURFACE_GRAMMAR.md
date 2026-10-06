# FRANKEN BLENDER 008l — MATERIAL SURFACE GRAMMAR

008l adds a cheap material language to existing paper-stage actors, rooms, and parts.

```text
SAME RIG STRUCTURE
+ MATERIAL PROFILE
      ↓
DIFFERENT SURFACE
DIFFERENT MOTION FEEL
DIFFERENT WEAK DIRECTING BIAS
```

Material remains an aesthetic/compositional profile.

```text
MATERIAL != PHYSICS CLAIM
```

## Initial material presets

```text
paper
cardboard
wood
clay
felt
plastic
foil
stone
wax
inked
ghost
junk-collage
```

These are intentionally stylized, local, deterministic approximations.

## Three material surfaces

Each material profile has three independent groups:

```text
surface
motion
directing
```

### Surface

Controls deterministic Pillow treatment of the part image:

- posterization
- procedural grain
- edge treatment
- blur / softness
- gloss
- corrugation
- wood-grain lines
- foil highlights
- stone desaturation
- felt fuzz
- ghost translucency
- junk-collage patches

### Motion

Modifies existing transform keyframes:

- position amplitude
- rotation amplitude
- scale amplitude
- bounded lag
- deterministic jitter
- bounded drift

### Directing

Provides only a weak aesthetic preference:

```text
closeupBias
wideBias
insertBias
```

Material directing bias is weaker than punctuation, Doctor decisions, dialogue roles, and already-bound inserts.

## Source authority remains separate

Rig build now freezes both identities:

```text
ORIGINAL PART PNG
  sourceSha256
      ↓
DETERMINISTIC MATERIAL TREATMENT
      ↓
MATERIALIZED RENDER PNG
  renderSourceSha256
```

Both remain in the rig.

```text
MATERIALIZED ASSET != ORIGINAL SOURCE
SURFACE != SOURCE IDENTITY
```

## Rig syntax

Character-wide default:

```json
{
  "materialDefaults": "wood"
}
```

Part override:

```json
{
  "id": "head",
  "role": "head",
  "source": "head.png",
  "material": "clay"
}
```

Room material:

```json
{
  "roomMaterial": "cardboard"
}
```

This allows mixed rigs such as:

```text
wood body
clay face
foil halo
wax mouth prop
cardboard room
```

## Custom profile overrides

A preset may be locally modified without inventing a new global material type:

```json
{
  "material": {
    "type": "wood",
    "surface": {"woodGrain": 0.35},
    "motion": {"rotation": 0.55}
  }
}
```

The result receives its own content-addressed material profile id.

## Motion feel examples

```text
paper
  → direct / neutral limited animation

cardboard
  → stiffer position + rotation

wood
  → rigid hinge-like motion

clay
  → softer movement + slight squash

felt
  → slower / draggy response

plastic
  → cleaner / snappier movement

foil
  → deterministic micro-jitter

stone
  → heavy low-amplitude motion

wax
  → soft lag + slight squash

ghost
  → translucent surface + drift

junk-collage
  → rough surface + misaligned jitter
```

These are aesthetic motion modifiers, not simulation.

```text
MOTION FEEL != MATERIAL MEASUREMENT
```

## Mixed-material ensembles

008k cast members retain their own material defaults and material-type sets.

```text
WOOD CHARACTER
    +
CLAY CHARACTER
    +
CARDBOARD ROOM
      ↓
ONE ENSEMBLE
```

Each character still carries its own rig id, part-source hashes, material profile ids, and materialized render assets.

```text
MIXED MATERIAL CAST != COLLAPSED MATERIAL IDENTITY
```

## Material-aware 008j direction

Material may softly influence a normal shot choice:

```text
clay
  → close-up preference

wood / stone
  → wider silhouette preference

foil / junk-collage
  → insert preference when an insert already exists
```

But explicit signals remain stronger:

```text
?
  → REACTION

!
  → CLOSE_UP

Doctor intervention
  → retains Doctor authority

bound INSERT
  → remains bound
```

```text
MATERIAL BIAS IS WEAKER THAN EXPLICIT EDITORIAL SIGNALS
```

## Material receipts

Cutout-stage layer receipts now preserve:

```text
render source SHA
original source authority SHA
material profile
materialized asset id
```

The puppet performance receipt also reports:

```text
materialTypes
materializedLayerCount
```

## Command door

List presets:

```bash
python -m haunted_blender.material_cli presets
```

Inspect a profile:

```bash
python -m haunted_blender.material_cli profile wood
```

Materialize one image:

```bash
python -m haunted_blender.material_cli materialize \
  ./head.png \
  ./head-clay.png \
  --type clay
```

## Zero-dollar boundary

All material work is local Pillow/keyframe processing.

```text
externalGenerations = 0
providerCredits     = 0
usdMicros           = 0
```

## Laws

```text
MATERIAL != PHYSICS CLAIM
SURFACE != SOURCE IDENTITY
MOTION FEEL != MATERIAL MEASUREMENT
MATERIALIZED ASSET != ORIGINAL SOURCE
SURFACE TREATMENT IS DETERMINISTIC
ORIGINAL SOURCE SHA REMAINS AUTHORITY
SURFACE STYLE MAY MODIFY MOTION GRAMMAR
MATERIAL BIAS IS WEAKER THAN EXPLICIT EDITORIAL SIGNALS
MIXED MATERIAL CAST != COLLAPSED MATERIAL IDENTITY
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
008l  MATERIAL + TACTILE WORLD GRAMMAR
```

The same structural puppet can now become paper, wood, clay, foil, felt, stone, ghost-material, or mixed junk without asking a provider for new video.