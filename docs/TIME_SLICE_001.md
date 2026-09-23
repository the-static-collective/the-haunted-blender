# Time Slice 001 — a door whose width records time

**Experimental, local and additive.** `haunted_blender.time_slice` reads an independently accepted moving take via the existing acceptance and source validation chain. It samples up to ten seconds at eight derived frames per second, then assembles a 320 × 180 PNG from 32 vertical strips. Strip 0 comes from the beginning of the clip; strip 31 comes from the last sampled frame. The intermediate strips advance through sampled time. This image is a new material, not an edited source clip or an accepted scene take.

Run from the repository root with an existing private Blender library and an accepted synthetic take:

```sh
python -m haunted_blender.time_slice_cli ~/HauntedBlender \
  /private/accepted-scene-artifact.json /private/take-acceptance.json \
  --out ~/HauntedBlender/renders/time-slices/door-time-slice.png
```

Output is restricted to the library's `renders/time-slices` folder. The sibling `.png.receipt.json` records accepted source and acceptance digests, output digest, sample cadence, and the exact derived sample index chosen for each pixel strip. The nominal time labels are positions in FFmpeg's normalized eight-fps samples, **not verified timestamps of source frames**. Existing outputs are not overwritten. The PNG does not authorize publication or automatic placement into another cut. All source frames, accepted Scene Artifact, and takes remain unchanged.

Verification: `python -m unittest discover -s tests -p test_time_slice.py -v` and `python -m unittest discover -s tests -v`. Test media is synthetic and local. A real example is rendered from the private accepted synthetic door take when available; its image and receipt must stay outside this public repository.

The other candidates are kept in [Recajggers 001](RECAJGGERS_001.md).
