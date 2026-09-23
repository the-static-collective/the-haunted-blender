# Visual Dream 001 — authored graph, door, observer camera

An isolated private research cartridge. The filmmaker supplies a frozen **fictional** SceneWorld, a small graph of world fact IDs, authored association/contradiction/residue edges, and a score of camera positions and door angles. The walk selects an unvisited outgoing edge in relation order, then node ID order. It stops after 12 steps or at a dead end. A repeated, authored motif is reported as recurrence; the engine assigns no meaning.

Each step distinguishes (1) a fictional fact already established at the chosen beat, (2) the audience knowledge recorded in the frozen world, and (3) what this camera can depict at this angle. The `front` camera needs 90°, `threshold` needs 17°, and `behind` needs 43°. These are declared *creative rules*, not measurements of real optics. The renderer interpolates angle over 12 frames per step, reevaluates the gate for each frame, and records the angle and depiction decision for every output frame. Neither the graph walk nor moving the camera edits the SceneWorld's facts or knowledge.

## Use

Install locally with `pip install -e '.[dream]'` and FFmpeg available. Prepare a SceneWorld via the existing Alchemy → Scene Weave path and freeze it. Author a JSON score with the following structure, replacing the snapshot path and hash with your real frozen world:

```json
{
  "schema": "haunted-blender/visual-dream-score/v0",
  "world_snapshot": "/private/HauntedBlender/snapshots/scene-weave/world-0123456789abcdef/HASH.json",
  "world_sha256": "64-hex-character-sha256-of-frozen-world",
  "beat": 0,
  "start": "door",
  "nodes": [
    {"id": "door", "fact_id": "sealed", "motif": "hinge"},
    {"id": "return", "fact_id": "sender", "motif": "hinge"}
  ],
  "edges": [{"from": "door", "to": "return", "relation": "residue"}],
  "camera_score": [
    {"camera": "threshold", "door_degrees": 25},
    {"camera": "behind", "door_degrees": 55}
  ],
  "max_steps": 2
}
```

`sender` will stay held if the audience has not been given knowledge of it at the chosen beat, even though the authored graph can traverse that node. The private plan contains fact IDs for audit; the rendered card only shows a fact ID and motif when both gates pass.

```sh
python -m haunted_blender.visual_dream_cli ~/HauntedBlender freeze /private/dream-score.json
python -m haunted_blender.visual_dream_cli ~/HauntedBlender plan /private/HauntedBlender/snapshots/visual-dream/SCORE_HASH.json
python -m haunted_blender.visual_dream_cli ~/HauntedBlender render /private/HauntedBlender/snapshots/visual-dream/SCORE_HASH.json --out ~/HauntedBlender/renders/visual-dream/door-dream.mp4
```

The silent schematic MP4 and `.mp4.receipt.json` are private derived proposals. Receipt includes source score and world hashes, graph walk, per-frame angles/visibility, output digest and explicit nonclaims. This does **not** import MEMENTO memories, execute Dogram mathematics, run 3rdi, inspect photographs, synthesize photo-real footage, or approve scene placement. A future adapter can accept selected fragments with their individual occurrence/availability/focus/known-at claims, preserve the source digests, and map only *filmmaker-approved* facts into this score. A photographic door layer and sound leakage need separate visual/audio admission and receipts.
