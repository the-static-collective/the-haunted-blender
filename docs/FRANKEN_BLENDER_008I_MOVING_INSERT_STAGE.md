# FRANKEN BLENDER 008i — MOVING INSERT STAGE

008h harvested moving loops and fragments but deliberately kept them as proposals.

008i gives those moving bits an actual place inside the 008g paper world.

```text
PAPER PUPPET WORLD
   +
HARVESTED LOOP / FRAGMENT
   ↓
BOUNDED MOVING SURFACE
```

Supported surface roles begin with:

```text
TELEVISION
WINDOW
PORTAL
ADVERTISEMENT
```

The layout catalog also reserves room for:

```text
DREAM
BACKGROUND SCREEN
```

## Separate compositor

The still-image Cutout Stage remains unchanged.

008i renders the paper performance first, then a second local FFmpeg compositor places moving harvested media into bounded rectangles.

```text
008g/008h still stage
      ↓
paper-stage-base.mp4
      +
harvested MP4 bits
      ↓
008i moving insert compositor
      ↓
puppet movie with living screens
```

This keeps video ingredients from pretending to be still-image layers.

## Source custody

Every moving insert is admitted from an 008h harvest witness.

Planning verifies the current bytes against the harvested SHA-256.

Rendering verifies the bytes again immediately before FFmpeg reads them.

```text
HARVEST SHA
   =
PLAN SHA
   =
RENDER-TIME SHA
```

If the file changed after planning, rendering stops.

```text
SOURCE SHA MUST MATCH HARVEST WITNESS
```

## Bounded surfaces

Each insert records:

- role
- source path
- exact source SHA-256
- original source provenance SHA-256
- harvest id
- start/end time
- x/y/width/height
- border width
- loop policy
- mute policy

The first available moving ingredient is normally a long-lived television surface. Additional ingredients are staggered into window, portal, and advertisement surfaces.

```text
MOVING SURFACE IS BOUNDED
MOVING INSERT != SCENE AUTHORITY
```

## Cardboard bezel

After each moving video is placed, the compositor draws a visible black frame around it.

The moving footage therefore reads as a television/window/portal object inside the paper set rather than an accidental full-screen edit.

## Audio authority

Harvested inserts are visual material only.

```text
INSERT AUDIO != PERFORMANCE AUDIO
```

Only the base performance audio stream is mapped to the result. Insert audio is never allowed to take over the film.

```text
BASE PERFORMANCE RETAINS AUDIO AUTHORITY
```

## Looping

Short harvested loops/fragments may repeat internally for the duration of their assigned surface.

That repetition does not create a new source or new evidence.

```text
HARVESTED LOOP MAY REPEAT WITHOUT BECOMING NEW SOURCE
```

## Puppet Studio integration

No extra user-facing command is needed when a Parts Drawer is supplied.

```bash
python -m haunted_blender.puppet_cli smash \
  puppet-spec.json \
  timing.json \
  ./film/puppet-pass \
  --parts-drawer ./film/parts/parts-drawer.json
```

008h builds the stage dressing.

008i automatically converts its moving insert proposals into a real moving-insert plan.

The Puppet Studio then:

1. renders the paper stage
2. composites moving harvested surfaces
3. verifies final duration
4. writes the moving-insert receipt
5. reports moving inserts in the puppet performance receipt

## Receipt

The moving-insert receipt records:

```text
plan id
base movie SHA-256
final movie SHA-256
duration
insert count
role
harvest id
insert SHA-256
original source provenance SHA-256
time bounds
screen bounds
audio authority
```

## Zero-dollar boundary

```text
externalGenerations = 0
providerCredits     = 0
usdMicros           = 0
```

008i consumes material we already own.

## Ecology

```text
008e  MAKE ENOUGH FILM
 ↓
008f  FIND WEAK WINDOWS
 ↓
008g  BUILD PAPER WORLD
 ↓
008h  HARVEST ALL VIDEO INTO BITS
 ↓
008i  PUT THE MOVING BITS
      INSIDE THE PAPER WORLD
```

Now a Flow/AI clip no longer needs to interrupt the puppet movie.

It can become a television broadcast, a window view, a portal, an advertisement, or another bounded moving object within the same deterministic scene.

## Laws

```text
MOVING INSERT != SCENE AUTHORITY
INSERT AUDIO != PERFORMANCE AUDIO
BASE PERFORMANCE RETAINS AUDIO AUTHORITY
HARVESTED LOOP MAY REPEAT WITHOUT BECOMING NEW SOURCE
MOVING SURFACE IS BOUNDED
SOURCE SHA MUST MATCH HARVEST WITNESS
MOVING INSERT DOES NOT REPLACE BASE PERFORMANCE
```
