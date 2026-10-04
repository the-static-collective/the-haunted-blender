# Memory Feedback 001 — the environment remembers what the eye saw

This experiment crosses **Observer-Local Vision 001** with the local recursive
video work from **Door Feedback 001**.

The governing distinction is:

\[
\text{memory receipt} \neq \text{stored image}
\]

The receipt records that a camera/I-eye previously had an authored fact
available. It does not invent or retain hidden pixels. The renderer may acquire
visual memory only while that fact is actually `present_to_eye` in the supplied
projection timeline.

When a later projection marks the same fact as `memory_residue`, the adapter
can replay the last genuinely seen pixels as a decaying, displaced afterimage.

That gives us:

\[
\text{present perception}
\rightarrow
\text{visual capture}
\rightarrow
\text{occlusion}
\rightarrow
\text{memory residue}
\rightarrow
\text{observer-responsive image}
\]

without changing the authored world.

## First bounded behavior

For each authored memory region:

1. while its fact is `present_to_eye`, capture the latest source pixels;
2. when the fact becomes `memory_residue`, blend those captured pixels over
   the current source;
3. shift the residue slightly each frame and decay its strength;
4. stop treating the effect as present evidence at every step.

The current effect is deliberately simple: one cool displaced afterimage with a
fixed decay law. It is a proof of the observer/memory/render contract, not the
final visual language.

## Why regions are authored

Observer-Local Vision knows *which fact* is available; it does not infer where a
person or object is inside a frame.

Memory Feedback therefore requires an explicit normalized region such as:

```json
{
  "fact-figure": [0.20, 0.20, 0.50, 0.70]
}
```

Those coordinates are filmmaker spatial assertions. They are not object
tracking, face recognition, identity inference, or evidence that a photographed
subject is the fictional entity named by the fact.

## Plan shape

A memory plan contains a complete frame timeline plus regions:

```json
{
  "timeline": [
    {
      "start_frame": 0,
      "end_frame_exclusive": 18,
      "projection": {"schema": "haunted-blender/observer-local-projection/v0"}
    },
    {
      "start_frame": 18,
      "end_frame_exclusive": 36,
      "projection": {"schema": "haunted-blender/observer-local-projection/v0"}
    }
  ],
  "regions": {
    "fact-figure": [0.20, 0.20, 0.50, 0.70]
  }
}
```

The real projection objects include their content-addressed projection and
memory-receipt digests.

The timeline must cover every normalized source frame exactly. All projections
must belong to one observer and one authored world state. Beats may advance but
cannot run backward.

## Run

```sh
python -m haunted_blender.memory_feedback_cli ~/HauntedBlender \
  /private/accepted-scene-artifact.json \
  /private/take-acceptance.json \
  /private/memory-plan.json \
  --out ~/HauntedBlender/renders/memory-feedback/door-memory.mp4
```

The output is a new private MP4 plus a sibling receipt. The receipt includes
source and output digests, projection and memory-receipt digests, authored
regions, the exact visual policy, and per-fact capture/residue statistics.

## Critical boundary

A memory receipt alone cannot produce a ghost.

If a timeline begins with `memory_residue` but this adapter never saw the fact
during a prior `present_to_eye` frame, rendering fails. Fact memory is not pixel
memory.

Likewise, the afterimage is never evidence that the remembered entity remains
present. It is a cinematic response of this observer-conditioned rendering.

## Next frontier

The clean next experiment is **Memory Strength 001**: derive residue weight from
measurable encounter history—dwell duration, recency, repetition and clarity—
rather than one fixed decay law. After that, two memories can compete for visual
attention, and contradictory present evidence can destabilize an old residue
without rewriting either history.
