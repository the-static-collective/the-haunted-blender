# FRANKEN BLENDER 008k — ENSEMBLE STAGE / DIALOGUE GRAMMAR

008k turns reusable 008g puppet rigs into an actual cast.

```text
RIG A
+ RIG B
+ LYRIC / DIALOGUE TIMING
      ↓
SPEAKER / LISTENER / REACTION OWNERSHIP
      ↓
ENSEMBLE PERFORMANCE
      ↓
008j CHARACTER-AWARE DIRECTION
```

## Existing rigs remain authoritative

008k does not merge characters into a new character asset.

Each cast member preserves its original 008g rig id and source hashes.

The ensemble owns only:

- stage placement
- entrance / exit timing
- dialogue-turn assignment
- listener assignment
- eyeline pose grammar
- reaction ownership

```text
CAST PLACEMENT != CHARACTER AUTHORITY
```

## Cast size

The first implementation supports 2–4 characters on one paper stage.

Characters are scaled into deterministic left/right/interior slots while preserving each rig's own part images and mouth atlas.

## Dialogue turns

An ensemble spec may explicitly assign each lyric cue:

```json
{
  "cueIndex": 3,
  "speakerId": "a",
  "listenerIds": ["b"]
}
```

If a cue is not assigned, 008k uses deterministic round-robin assignment and marks that assignment as proposal-only.

```text
SPEAKER ASSIGNMENT != VOICE IDENTITY
```

## Speaker-only mouths

Only the assigned speaker receives mouth events for a cue.

Listeners do not lip-sync the speaker's words.

```text
ONLY ASSIGNED SPEAKER RECEIVES MOUTH EVENTS
```

## Listener eyelines

During another character's turn, listeners receive a simple inward eyeline pose:

```text
left-side listener  → look-right
right-side listener → look-left
```

This is staging grammar, not gaze evidence.

```text
EYELINE != GAZE EVIDENCE
```

## Reaction ownership

Each turn has a primary listener.

Near the latter part of the speaker's line, that listener receives a bounded reaction pose such as side-eye or shrug.

```text
SPEAKER
   ↓
LISTENER EYELINE
   ↓
OWNED REACTION
```

The reaction is editorial grammar, not a claim about inner state.

```text
LISTENER REACTION != INNER STATE
REACTION OWNERSHIP IS EDITORIAL GRAMMAR
```

## Entrances and exits

Each cast member can define:

```text
enterAt
exitAt
```

Before entrance and after exit, that character's parts and mouth layers are transparent and shifted offstage.

At the entrance/exit boundary the same hashed rig is animated into/out of view.

```text
ENTRANCE AND EXIT ARE STAGE GRAMMAR
```

## Ordinary puppet-performance compatibility

008k deliberately emits the existing:

```text
haunted-blender/puppet-performance/v1
```

with additional `ensemble` metadata.

That means the output can pass unchanged through:

```text
008h stage compost
008i moving insert stage
008j Paper Director
```

## Character-aware 008j direction

008j now understands:

```text
SPEAKER
LISTENER
TWO_SHOT
REACTION
CLOSE_UP
```

Each dialogue shot carries:

```text
speakerId
listenerId
```

and the Director resolves those ids against actual cast boxes.

### Speaker shot

Crop around the assigned speaker's box.

### Listener / reaction shot

Crop around the primary listener's box.

### Close-up

Tighter crop around the assigned speaker.

### Two-shot

Union of speaker + listener boxes with bounded padding.

```text
SHOT TYPE
   +
CHARACTER ROLE
   ↓
ACTUAL CAST BOX
```

## Dialogue-to-director chain

```text
cue 0
  A speaks
  B listens
  ↓
SPEAKER A

cue 1
  B asks a question
  A listens
  ↓
REACTION A

chorus cue
  A/B share frame
  ↓
TWO_SHOT
```

## One-command ensemble

```bash
python -m haunted_blender.ensemble_cli smash \
  ensemble-spec.json \
  timing.json \
  ./film/ensemble-pass \
  --direct
```

Optional existing layers remain available:

```bash
--parts-drawer ./film/parts/parts-drawer.json
--doctor-report ./film/doctor.before.json
```

Outputs include:

```text
performance/
ensemble-performance.json
ensemble-movie.mp4
paper-director.plan.json       # with --direct
ensemble-directed.mp4          # with --direct
```

## Receipt visibility

The standard puppet receipt now also records:

```text
ensembleId
ensembleCastCount
dialogueTurnCount
```

## Zero-dollar boundary

```text
externalGenerations = 0
providerCredits     = 0
usdMicros           = 0
```

008k reuses existing rigs and local timing.

## Laws

```text
SPEAKER ASSIGNMENT != VOICE IDENTITY
LISTENER REACTION != INNER STATE
EYELINE != GAZE EVIDENCE
CAST PLACEMENT != CHARACTER AUTHORITY
REACTION OWNERSHIP IS EDITORIAL GRAMMAR
ENSEMBLE PERFORMANCE != MULTIPLE SOURCE AUTHORITIES COLLAPSED
ONE ROOM MAY HOST MULTIPLE HASHED RIGS
ONLY ASSIGNED SPEAKER RECEIVES MOUTH EVENTS
LISTENER MAY REACT WITHOUT SPEAKING
ENTRANCE AND EXIT ARE STAGE GRAMMAR
```

## Stack consequence

```text
008e  COVERAGE
008f  TRIAGE
008g  ACTORS + SETS
008h  PARTS + BEHAVIORS
008i  MOVING SCREENS
008j  DIRECTOR
008k  CAST + DIALOGUE + REACTION OWNERSHIP
```

At this point the cheap paper system can support actual staged exchanges rather than simulating every beat with one character.