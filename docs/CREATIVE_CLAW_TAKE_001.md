# Creative Claw Take 001 — one approved still to one candidate clip

**Experimental and additive.** This branch builds on `experimental/art-i-fact-constructor-001` and leaves its existing Scene Artifact, SceneWorld, Alchemy, N0 render and constructor schemas unchanged. The separate N2–N6 geometric-object experiments are not merged here.

## A bounded round trip

1. Accept a Scene Artifact with an actual cataloged synthetic frame. Its accepted beat, frame ID and frozen byte digest form the local parent.
2. Freeze one 3–10 second image-to-video request. `request` requires both `--assert-synthetic` and `--approve-disclosure`: approval of a local scene preview alone does not authorize uploading an image or prompt. The assertion is made by the operator; image classification is not implemented.
3. Upload the *exact* returned `frame` to Creative Claw using its local-file upload flow, then run **one** `video/gemini-omni-flash` image-to-video generation with the returned prompt and duration. The uploaded image is a literal first frame. This provider step is deliberately outside the local Python CLI: no unpublished provider protocol or hidden token is embedded in the project.
4. On successful completion, download the returned MP4 locally. `admit` validates the still and Scene Artifact afresh, probes for an actual video stream, copies the MP4 into the private vault and records its SHA-256, request digest and the *operator-reported* provider job ID. It cannot independently attest that this job ID produced the bytes.
5. `accept --approve` separately binds that admitted candidate to the accepted beat for a **private preview**. It does not edit the accepted story or static film, replace an existing shot, publish a film, or represent video motion as a witnessed event.

```sh
python -m haunted_blender.creative_take_cli request ~/HauntedBlender \
  /absolute/path/to/accepted-scene-artifact.json 0 \
  'The synthetic door opens slowly; fixed camera; no people.' \
  --duration 3 --assert-synthetic --approve-disclosure

# Perform one Creative Claw image-to-video request using the frozen fields.
# Download the finished MP4 after the provider job completes.

python -m haunted_blender.creative_take_cli admit ~/HauntedBlender \
  /absolute/path/to/frozen-creative-take-request.json \
  /private/path/to/downloaded-result.mp4 --provider-job-id ACTUAL_JOB_ID

# Only after inspecting the admitted clip:
python -m haunted_blender.creative_take_cli accept ~/HauntedBlender \
  /absolute/path/to/frozen-creative-take-request.json \
  /absolute/path/to/admitted-clip.mp4 --approve
```

The request contains an absolute local Scene Artifact path and the prompt. The admission receipt contains a provider job ID. Keep snapshots, videos, source photos and receipts **outside the public repository**. The source digest identifies bytes, not source rights. Before any nonsynthetic image, likeness, voice, publication workflow or additional generation, extend the disclosure and permission contract deliberately.

## Receipt scope and unfinished bridge

There are three separate witnesses: immutable proposed request, admission receipt for a playable local video, and optional filmmaker acceptance. An MP4 with a `.mp4` extension and no video stream is refused. Changed parent photos, scene snapshots and admitted clip bytes refuse downstream operations. Provider settings and job ID are reported inputs; this module has no Creative Claw API token, remote job verification, remote cost receipt, or output URL authentication. It does not compose the accepted take into a final film yet. That is the next build seam: a shot-scoped video-take render option that checks the accepted take witness, timebase and output lineage without rewriting N0 static-film meaning.

Verification: `python -m unittest discover -s tests -v`, `python -m haunted_blender.creative_take_cli --help`. CI uses synthetic source PNGs and locally encoded sample MP4s; it never spends Creative Claw credits or sends a real person's image to a provider.
