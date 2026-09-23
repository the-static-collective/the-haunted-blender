# Door Dance 001 — open, hesitate, retreat, open again

The first intentional performance edit of one **accepted moving take**. This experiment reorders decoded source frames locally and writes a new silent private MP4, with its own digest and a complete output-frame-to-source-frame map. It never modifies the original clip, its Scene Artifact, or the take acceptance.

From 72 sampled frames of the synthetic three-second door clip at 24 fps:

| Beat | Output frames | Source frame path | Intention |
| --- | ---: | --- | --- |
| Open partway | 0–36 | 0→36 | Reach an unmistakably partly open door. |
| Pause | 37–40 | 36 held | Give the turn a beat. |
| Close a little | 41–50 | 35→26 | Return along actual photographed/generated source frames. |
| Pause | 51–52 | 26 held | Let the hesitation register. |
| Open again | 53–97 | 27→71 | Resume the original opening trajectory. |

The 98-frame result lasts about 4.08 seconds. The change of direction has no source-frame discontinuity greater than one; the brief repeated frames are authored pauses. The exact frame ranges are derived from the source's normalized 24-fps samples and a fixed score (50% turn, 36% retreat), so the first cartridge also runs on short accepted clips of at least 12 samples. Reported source times are nominal; original frame presentation timestamps are not retained. The reverse is an editorial construction, not evidence the original door actually closed again.

Run with an existing accepted moving take:

```sh
python -m haunted_blender.door_dance_cli ~/HauntedBlender \
  /private/accepted-scene-artifact.json /private/take-acceptance.json \
  --out ~/HauntedBlender/renders/door-dances/door-hesitation.mp4
```

The sibling `.mp4.receipt.json` records exact source, acceptance and output digests, all 98 output-to-input frame indices for this clip, phase boundaries, output duration, and nonclaims. The new performance requires its own filmmaker decision before any later scene placement or Pantry import. An optional later experiment could run [Door Feedback 001](DOOR_FEEDBACK_001.md) on the *separately admitted* performance, with both transformations visible in the lineage.

Verification: `python -m unittest discover -s tests -p test_door_dance.py -v` and the full suite. The private synthetic door video and receipt are retained outside the public repository.
