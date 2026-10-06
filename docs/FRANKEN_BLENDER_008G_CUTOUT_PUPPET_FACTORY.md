# FRANKEN BLENDER 008g — CUTOUT PUPPET FACTORY

008e guarantees enough movie exists.

008f finds the weakest windows.

008g adds a repeatable paper-puppet stage so weak windows can become scenes instead of immediately consuming more video ingredients.

```text
ONE PUPPET
+ ONE ROOM
+ LYRIC TIMING
      ↓
REUSABLE LIMITED ANIMATION
      ↓
ARBITRARY PROVIDER-FREE DURATION
```

## Puppet rig

A puppet is authored once from flat image parts:

```text
head
body
arm-left
arm-right
leg-left
leg-right
optional props
```

The rig stores source hashes, flat positions, z-order, mouth anchor, and the available pose grammar.

```text
RIG != PERFORMANCE
PART IMAGE != JOINT AUTHORITY
```

## Mouth atlas

008g creates six tiny reusable mouth shapes:

```text
closed
open
wide
round
teeth
shout
```

Full Measure lyric cues become deterministic word-time events. Words select crude mouth shapes by spelling patterns.

This is intentionally not speech recognition or phonetic truth.

```text
MOUTH SHAPE != PHONETIC CLAIM
```

The point is lots of cheap readable talking, not perfect lips.

## Pose grammar

The initial reusable pose vocabulary includes:

```text
idle
talk
yell
point
shrug
side-eye
look-left
look-right
pray
walk
fall
```

Each pose is only a small transform delta on flat body parts.

Deliberate hold frames are generated around lyric cues so characters can remain almost frozen while one arm, head, or mouth changes.

```text
HOLD FRAMES ARE A FEATURE
```

## Lyrics become geography

Lyric cues are not rendered merely as subtitles.

Each cue becomes a construction-paper scenery layer: words are laid into steps / ledges / sign-like blocks inside the room and appear during their cue.

```text
LYRIC TEXT
   ↓
PHYSICAL STAIR / SIGN / FLOOR GEOMETRY
```

The words can therefore function simultaneously as readable lyrics and world material.

## One room

If no room image is supplied, the factory generates a deliberately crude flat-paper room with wall, floor, window, door, and crooked baseboard.

The room is reusable across arbitrary performances.

## Cutaway Machine

008g consumes an 008f Weakest Window Doctor report before provider escalation.

Dominant weakness maps to a cheap interruption:

```text
stasis             → reaction
source overuse      → lyric sign
recent repetition   → prop gag
novelty deficit     → abrupt sign
transition jolt     → establishing shot
```

Cutaways are bounded construction-paper cards and props rendered locally.

```text
CUTAWAY BEFORE PROVIDER ESCALATION
ABRUPTNESS MAY BE STYLE
```

Cutaways do not delete the weak source or claim new evidence. They are cheap staging over the completed movie language.

## Doctor escalation changes

The post-008g ladder is:

```text
LEVEL 0  keep
LEVEL 1  deterministic remix
LEVEL 2  cutaway / owned-clip compost
LEVEL 3  topology / text / puppet treatment
LEVEL 4  repeatably-free provider
LEVEL 5  regenerating included allowance
LEVEL 6  finite credit
LEVEL 7  paid hero shot
```

A failed Level 1 now points at the Cutaway/Puppet layer before any provider.

## One-command studio

Build, compile, and render:

```bash
python -m haunted_blender.puppet_cli smash \
  puppet-spec.json \
  timing.json \
  ./film/puppet-pass
```

To let the Doctor choose cutaways:

```bash
python -m haunted_blender.puppet_cli smash \
  puppet-spec.json \
  timing.json \
  ./film/puppet-pass \
  --doctor-report doctor.before.json
```

Outputs include:

```text
rig/
  room.png
  mouth-atlas/
  puppet-rig.json

cutaway-plan.json        # when Doctor supplied
performance/
  lyric-geography/
  cutaways/

puppet-performance.json
puppet-movie.mp4
puppet-movie.mp4.puppet.json
```

## Economics

The puppet performance receipt explicitly carries:

```text
externalGenerations = 0
providerCredits     = 0
usdMicros           = 0
```

A longer performance reuses the same rig, same room, same mouth atlas, and same pose grammar.

That is the South-Park economic property:

```text
ONE CHARACTER ASSET
+ ONE SET
≈ LARGE AMOUNTS OF SCREEN TIME
```

## Relationship to Toaster

008g does not replace the live Toaster idea.

Instead it gives Toaster cheap controllable stage primitives:

```text
left hand
  → puppet / camera / reaction energy

right hand
  → lyric chunks / geography / cutaways

Toaster timing
  → puppet pose + mouth + stage placement
```

The same lyric chunks that act as text can become scenery under the character.

## Relationship to Flow / AI footage

Flow clips and generated candidates become objects inside the paper world rather than the only possible world:

```text
TV SCREEN
WINDOW
DREAM
PORTAL
FLASHBACK
ADVERTISEMENT
BACKGROUND
PROP
TEXTURE
```

This makes expensive or rare footage compositional seasoning.

## Laws

```text
ONE RIG MAY PRODUCE UNBOUNDED PROVIDER-FREE DURATION
WORDS MAY BECOME SCENERY
MOUTH FLIP != SPEECH RECOGNITION
POSE GRAMMAR != FULL-BODY GENERATION
HOLD FRAMES ARE A FEATURE
CUTAWAY BEFORE PROVIDER ESCALATION
ABRUPTNESS MAY BE STYLE
CUTAWAY != NEW EVIDENCE
PUPPET RENDER != FINAL CUT
LOCAL LIMITED ANIMATION != PROVIDER GENERATION
```
