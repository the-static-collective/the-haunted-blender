# Take Cut 001 — the moving take enters the cut

**Experimental additive branch** on top of Creative Claw Take 001. This adapter does not modify SceneWorld, frozen Scene Artifacts, film/v1, the N0 silent storyboard renderer, accepted static shots or the original moving clip.

One separately filmmaker-accepted Creative Claw take replaces the *presentation* of its accepted beat in a new private cut. Every other accepted beat remains the same still image at its already declared duration. The moving clip plays for its probed input duration. FFmpeg normalizes picture to 1280×720, 24 fps H.264 and concatenates the segments. This first cut is intentionally **silent**: any source audio is omitted and the receipt says so. It cannot claim dialogue, acting, real-world occurrence, release permission or an actual audience response.

## Run on a private local library

Start with the accepted Scene Artifact, request, admitted video and receipt from [Creative Claw Take 001](CREATIVE_CLAW_TAKE_001.md). After reviewing the admitted candidate, accept its use as a private take:

```sh
python -m haunted_blender.creative_take_cli accept ~/HauntedBlender \
  /private/path/to/take-request.json \
  /private/path/to/admitted-video.mp4 --approve

python -m haunted_blender.take_cut_cli ~/HauntedBlender \
  /private/path/to/accepted-scene-artifact.json \
  /private/path/to/take-acceptance.json \
  --out ~/HauntedBlender/renders/cut-with-moving-beat.mp4
```

The output has a distinct `.mp4.take-cut.json` receipt recording exact source clip and still digests, accepted snapshot identity, normalized segment digests, output digest, probed dimensions/duration, no-audio scope and nonclaims. Every parent Scene Artifact, request, acceptance, admission receipt, static source, and moving video is revalidated before rendering. Inputs are checked again before the output is issued. Changed inputs, a take accepted for a different scene, a missing video stream, and existing output paths refuse.

The acceptance witness proves that an explicit local selection was stored; it does not prove that a provider job ran or authorize publication. This is a bounded **private preview cut**, not the three-scene dramatic film release gate. It currently supports one moving take per render; adding multiple takes, sound, captions, independent shot caches and scene revisions needs new explicit contracts. Keep private output, photo sources and receipts outside Git.

`python -m unittest discover -s tests -v` includes a three-beat synthetic movie proof that measures decoded frames: the chosen beat moves, adjacent beats stay visually static, and stale or mismatched take witnesses fail before output.
