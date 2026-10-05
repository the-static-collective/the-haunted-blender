# FRANKEN BLENDER 004 — CUTOUT COMPILER

Status: experimental descendant of DREAMBREEDER 003.

## The crossing

003 made unborn films addressable.

004 makes them **watchable without making them history**.

```text
DREAM ECOLOGY
  p1 p2 p3 p4 p5 p6
   |  |  |  |  |  |
   v  v  v  v  v  v
CUTOUT COMPILER
   |  |  |  |  |  |
   v  v  v  v  v  v
six cheap puppet previews
          ↓
      human watches
          ↓
      KEEP / SCRAPE
```

This is an inversion of the normal generative-video workflow.

We do not spend expensive moving-world generation to discover whether an idea is
worth continuing. We first render a deterministic, inspectable puppet hypothesis.

## Cutout kit

A kit is a local manifest of still-image organs:

- background
- actor/body
- head
- arms
- props
- foreground
- light
- portal/window
- any other authored role

Each layer has a source image, z-order and initial transform.

DREAMBREEDER's `motionGrammar` mutates the authored transform path rather than
requiring new pixels.

Current motion words include:

- hold
- drift-up
- open-late
- hinge
- wind
- parallax
- freeze
- echo
- misregister
- separate
- answer
- assemble
- layer
- backlight
- return
- step
- raise-world
- reveal-sky

The vocabulary is intentionally small and deterministic.

## Flow gene → donor freeze

If a proposal names a Flow donor and the local machine provides the corresponding
video path, 004 may extract one deterministic source frame with FFmpeg and place it
into the preview as a moving/hinged donor window.

This is not yet "understanding" the Flow clip.

It proves the more important architecture:

```text
ADDRESSED FLOW SPECIMEN
        ↓
local byte path supplied
        ↓
deterministic frame extraction
        ↓
reusable visual organ
        ↓
puppet relation
```

The same specimen can later donate a different organ without changing its source
identity.

## Six-up contact movie

`render_sixup` renders all six proposals and then composes them into one 3×2
contact-sheet MP4.

The contact movie is a **possibility viewer**.

It is deliberately forbidden from changing the ecology disposition.

```text
WATCHING != KEEP
PREVIEW != HISTORY
PREVIEW RECEIPT != PERFORMANCE RECEIPT
```

A person can therefore look at six actual moving futures before granting one
continuation permission.

## Why this matters economically

Suppose each proposal preview is two seconds at 12 fps.

Those six futures cost:

- local still assets;
- deterministic arithmetic;
- Pillow frames;
- FFmpeg encoding.

Not six generative-video jobs.

Only after KEEP do we decide whether the chosen future deserves an expensive
awakening from Flow / Screel / Krea / Creative Claw / another organ.

## Command door

```bash
python -m haunted_blender.dream_cutout_cli compile \
  ecology.json dream-proposal:... kit.json \
  --out proposal.plan.json

python -m haunted_blender.dream_cutout_cli sixup \
  ecology.json kit.json ./sixup \
  --donor-map donor-paths.json
```

## Next door

005 should bind this viewer back to disposition:

```text
SIX-UP MP4
   ↓
human KEEP p4
   ↓
compile p4 as a longer scene
   ↓
PlayDeck / Toaster timing inheritance
   ↓
rare AWAKEN requests only at earned thresholds
   ↓
accepted takes return into Blender
```

That would turn the possibility viewer into an actual **movie-growing instrument**.
