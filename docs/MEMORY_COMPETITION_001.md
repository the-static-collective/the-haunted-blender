# Memory Competition 001 — one finite image, two valid memories

This experiment follows Memory Feedback 001 and Memory Strength 001. The camera
retains two separately witnessed visual captures, then sees both of their facts
as `memory_residue` in overlapping authored regions.

## The rule

Each output pixel has **at most 72% total memory-overlay opacity**, including
pixels claimed by both residues. Remaining opacity belongs to the present source
image. If two candidate weights exceed that budget, a deterministic
largest-remainder allocation scales them within it; ties resolve by stable fact
ID rather than region order. The renderer composites both residues against the
*same original current pixel*, never by stacking alpha layers in input order.

The input memory-strength schedule derives from the eye's earlier visible
dwell, authored focus, repeated encounters and recency. The allocation is a
cinematic treatment, not an assessment of truth, psychological importance or
which remembered event actually occurred.

## Boundary

- Exactly two authored normalized memory regions, with spatial overlap.
- One immutable observer/world projection timeline covering every decoded frame.
- Each ghost uses pixels captured only while **that specific fact** was
  `present_to_eye`; a receipt alone has no pixels.
- A render without simultaneously overlapping valid residues is refused.
- No scene admission, source rewrite, automatic release or human-memory claim.

The adapter uses the existing accepted-take input checks and FFmpeg transport
from Memory Feedback, but chooses a separate private output vault and a separate
receipt schema. Receipt includes observer/world, source/output SHA-256, strength
schedule digest, fact IDs, budget, allocation policy, per-frame overlap and
allocated-opacity statistics.

Run the same memory plan JSON as Memory Feedback 001, with two overlapping
regions and a timeline where each fact is visible before both become residual:

```sh
python -m haunted_blender.memory_competition_cli ~/HauntedBlender \
  /private/accepted-scene-artifact.json \
  /private/take-acceptance.json \
  /private/two-memory-plan.json \
  --out ~/HauntedBlender/renders/memory-competition/two-memories.mp4
```

The test uses synthetic pixels only. No personal media or footage is placed in Git.

## Next game-facing frontier

Turn each receipt into a revisitable room state: allow a player-controlled
camera path to modify **future rendering**, without using the current frame as
proof of a character's identity, an event, or human psychological memory.
