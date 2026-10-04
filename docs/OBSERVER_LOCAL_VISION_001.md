# Observer-Local Vision 001 — camera as I/eye

This experiment makes the camera a first-class **observer of an authored world** rather than a neutral framing device.

The invariant is:

\[
\text{camera} = \text{I/eye}, \qquad
\text{receipt} = \text{memory}, \qquad
\text{environment} = \text{observer-responsive presentation}
\]

It deliberately does **not** make the camera an authority over occurrence. Moving the eye or opening a threshold changes what can be presented from that observation point; it does not rewrite the SceneWorld.

## Three states, kept separate

For an authored fact at a beat:

- **visible** — currently available to this camera;
- **threshold-withheld** — inside the camera's authored field, but blocked by a threshold such as a door;
- **outside-field** — occurred in the world but is not claimed to be available from this camera at all.

A fourth state appears only when a prior receipt is supplied:

- **memory-residue** — the same observer previously saw the fact, cannot see it now, and carries that prior observation forward as render guidance.

That residue is not a new occurrence and is not proof that a human audience remembers anything.

## Door Test

The first executable test is the bounded matrix discussed in design:

- three observers: hallway, threshold, room;
- three door states: 10%, 45%, 80%;
- nine independent projection cells.

Each observer declares its own baseline fact access, focus and threshold rules. The door's openness is numeric from 0.0 to 1.0. The matrix returns visible/withheld facts and a content-addressed projection digest for every cell.

The more interesting sequential case carries a receipt:

1. threshold camera sees the figure with the door open;
2. a receipt records that observation;
3. the same camera sees the door mostly closed;
4. the figure moves from **present_to_eye** to **memory_residue**.

The canonical world bytes remain identical throughout.

## Run

Create a JSON scenario with:

- \`world\`: a SceneWorld-like object containing at least \`facts\` with \`id\` and \`since_beat\`, plus \`beats\`;
- \`observers\`: observer contracts containing \`id\`, \`position\`, \`access_fact_ids\`, \`focus_fact_ids\`, and \`threshold_rules\`.

Then:

\`\`\`sh
python -m haunted_blender.observer_local_cli scenario.json \
  --beat 0 --door door-main --open 0.10 0.45 0.80
\`\`\`

For a memory-carrying single observer:

\`\`\`sh
python -m haunted_blender.observer_local_cli scenario.json \
  --beat 0 --door door-main --open 0.10 \
  --observer eye-threshold --prior prior-memory-receipt.json
\`\`\`

## Boundary

This slice stops before image synthesis or video rendering. \`environment_response\` is typed guidance for a later adapter:

- \`present_to_eye\`
- \`threshold_withheld\`
- \`memory_residue\`

A later renderer may map those modes into occlusion, focus, light, texture, persistence, feedback or other visual behavior, but this experiment does not claim a particular rendering semantics yet.

The next strong crossing is to feed these response modes into Door Feedback / Door Dance so that the same physical source take can be rendered differently for different observer histories while preserving the source and every transformation receipt.
