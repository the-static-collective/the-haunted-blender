# FRANKEN BLENDER 002 — Deck / Pantry Cutout Machine

Status: experimental descendant of Franken Blender 001.

## Hypothesis

A useful long-form music-video system does not need to generate every second as
new video. It can spend most of its runtime moving existing things.

```text
GENERATE ASSETS, NOT EVERY FRAME
MOST MOTION = DETERMINISTIC RELATION
GENERATIVE VIDEO = RARE AWAKENING
```

## Three new executable doors

### 1. Flow Pantry

`haunted_blender.flow_pantry` indexes a local folder of user-owned video files.

It records:

- relative path
- byte length
- SHA-256
- Toaster-compatible canonical specimen identity
- optional FFprobe technical facts

It does **not** infer meaning from filenames or pixels and does not place local
absolute paths into the portable manifest.

The user's 225 Google Flow videos can therefore remain on the local computer while
Blender obtains stable byte identities.

### 2. Toaster / PlayDeck proposal bridges

The Toaster bridge maps unique Flow specimens into bounded proposal batches.

Haunted Toaster Pantry Composition v1 allows at most 16 ordered ingredients.
Therefore:

```text
225 unique Flow videos
→ 14 full 16-clip batches
→ 1 final 1-clip batch
→ 15 bounded proposal batches
```

This is not renderer authority. Toaster still performs its own VSPantry admission.

The PlayDeck bridge emits the public `DeckSpec 0.1` shape with logical
`flow://sha256/...` sources. Video cards begin **sleeping** and carry
`awaken: true`. They are not falsely marked render-ready because PlayDeck's current
folder ingest and `CardLayer` are image-oriented; freeze-frame or awakening
materialization remains a separate step.

### 3. Cutout Stage

`haunted_blender.cutout_stage` is a deliberately simple local compositor:

- background
- body
- head
- arms
- props
- foreground
- light/effect still layers
- authored x/y/scale/rotation/opacity keyframes
- Pillow frame composition
- FFmpeg MP4 encoding
- content-bound receipt
- immutable output

This is the "South Park layer" mechanically, without depending on any one visual
style. It is a puppet-film substrate.

## Cross-system composition

```text
LOCAL FLOW CORPUS
  ↓ hashes / probe
FLOW PANTRY
  ├─→ TOASTER VSPantry proposal batches
  │       ↓
  │    score / timing / digestion / selection
  │
  └─→ PLAYDECK DeckSpec proposal
          ↓
       cards / relations / world rules
          ↓
       freeze or AWAKEN only when earned
          ↓
CUTOUT STAGE ← generated stills / transparent puppet parts
          ↓
BLENDER TAKE / SCENE / MEMORY / ACCEPTANCE
          ↓
finished deterministic cut + receipts
```

## Why generated video becomes rare

A 4-second generated clip is expensive if it replaces four seconds of film.

It is cheap if it becomes:

- a looping window
- a background environment
- a moving texture
- an accepted "awakening" of one sleeping card
- a source for extracted frame reservoirs
- a reusable body/prop/motion witness

The unit of value changes from **seconds generated** to **relations enabled**.

## Command door

```bash
python -m haunted_blender.franken_cli index-flow /path/to/Flow --out flow.json
python -m haunted_blender.franken_cli plan-toaster flow.json --out toaster-plan.json
python -m haunted_blender.franken_cli plan-playdeck flow.json --deck-id flow-225 --out deck-proposal.json
python -m haunted_blender.franken_cli render-cutout cutout-plan.json preview.mp4 --receipt preview-receipt.json
```

## Nonclaims

- Flow videos are not committed to Git.
- A filename is not semantic evidence.
- A Deck proposal is not a PlayDeck render.
- A Toaster batch plan is not a Toaster recipe admission.
- An awakening request is not an accepted take.
- A cutout render is not publication authorization.
