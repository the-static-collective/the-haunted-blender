# Memory Strength 001 — encounter history changes how the image remembers

Memory Feedback 001 proved that a camera/I-eye can retain a visual residue after
a fact leaves present sight. This layer removes the universal ghost strength.

The new rule is:

\[
\text{residue strength}_t =
f(\text{dwell},\text{authored focus},\text{repetition},\text{recency})
\]

The inputs are deliberately narrow and inspectable.

- **dwell** — how many normalized render frames this camera actually carried the
  fact as `present_to_eye`;
- **authored focus** — the fraction of those visible frames in which the fact was
  in the camera contract's `focus_visible_fact_ids`;
- **repetition** — how many distinct visible encounters occurred;
- **recency** — how many frames have elapsed since the last visible frame.

No future frame contributes to an earlier strength value.

## Current formula

The first model is intentionally simple and bounded.

Encounter score:

```text
0.50 * min(1, visible_frames / 12)
+ 0.30 * focus_ratio
+ 0.20 * min(1, exposures / 3)
```

That score chooses:

- initial residue strength from 40–80%;
- per-frame retention from 82–96%.

Recency then applies that retention repeatedly after the last visible frame.

This means a brief glimpse fades faster than a sustained, repeatedly revisited,
camera-focused encounter, while both remain explicitly cinematic transforms.

## What this is not

This is not a model of human memory, trauma, emotion, salience or psychology.

`focus_visible_fact_ids` is authored camera attention. Dwell is render-frame
history. Repetition is a counted camera encounter. The resulting strength is a
deterministic visual parameter and nothing more.

That separation matters because the system can create a psychologically charged
film language without pretending it measured a person's interior state.

## Receipt surface

Memory Feedback v1 records:

- the content-addressed strength schedule;
- the exact formula and constants;
- per-fact visible/focused/exposure counts;
- first, peak and final residue strengths;
- the same source, projection, memory and output lineage already required by
  Memory Feedback 001.

The schedule itself is content-addressed and explicitly states
`future_information_used: false`.

## Resulting cinematic grammar

The environment can now respond differently to two remembered things even if
both are currently hidden.

A thing barely glimpsed can flicker away.

A thing held in frame can linger.

A thing returned to repeatedly can become difficult for the image to release.

The film is not declaring what matters. It is showing the accumulated history of
what this particular I/eye has actually encountered.

## Next frontier

The next clean breach is **Memory Competition 001**: when two valid residues
occupy the same frame, a bounded attention budget forces them to interfere,
occlude, alternate or composite instead of both receiving unlimited visual
authority.
