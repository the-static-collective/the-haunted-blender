# Door Feedback 001 — the doorway remembers its previous frames

**Two related experiments, separately labeled.** Hydra is a live browser/WebGL video synthesizer that routes sources and output buffers back into compositing chains. This branch implements one **Hydra-inspired** recurrence using local Python and FFmpeg; it does **not** execute, vendor, or claim Hydra-generated MP4 output. The Hydra patch below is a live-jam sketch for a separately installed local Hydra environment, not the recipe that produced the Blender clip.

## Executable Blender slice

The adapter validates one accepted moving take and its Scene Artifact before decoding any frames. At 320 × 180 and 12 derived samples per second, it computes a motion difference between adjacent samples, injects that difference into a blue-cyan trace, then shifts and fades the trace from one output frame into the next. The first output frame copies the accepted source. The last frame still carries a history of earlier motion. Maximum input duration: 10 seconds.

```sh
python -m haunted_blender.door_feedback_cli ~/HauntedBlender \
  /private/accepted-scene-artifact.json /private/take-acceptance.json \
  --out ~/HauntedBlender/renders/door-feedback/door-echo.mp4
```

The private `.mp4.receipt.json` includes source and acceptance digests, derived output digest, frame count and the exact fixed feedback parameters. The MP4 has a new material identity; its accepted parent is unchanged. No publication, scene placement, future asset admission or cross-product import is inferred from that parent. Source time stamps are not preserved by the normalized sampling pass.

## Live Hydra patch sketch

The **other** door is an operator-controlled live instrument. In a local Hydra installation, select a local MP4 with a browser file picker and give its resulting `File` object to a video element as `selectedFile`. Then:

```js
const video = document.createElement('video')
video.src = URL.createObjectURL(selectedFile)
video.loop = true
video.muted = true
video.playsInline = true
await video.play()
s0.init({src: video})
src(s0)
  .blend(src(o0).scale(1.012).scrollX(0.003).scrollY(0.001), 0.32)
  .out(o0)
render(o0)
```

Here `o0` feeds back into itself. Vary the scale, scroll, and blend amount while the video plays. The Blender adapter is a **motion-mask trail**, whereas this Hydra sketch feeds back the *whole image*; its output will differ. Capture, version pinning, deterministic frame timing and admission into Blender remain future work. If embedded into a distributed Blender app, Hydra's AGPL-3.0 license needs deliberate handling. The local Python adapter has no Hydra dependency.

Next distinct experiment: feedback *only inside* the open doorway, composited against the unchanged surrounding frame. Keep the authored aperture mask and the source clip separately identifiable in the next receipt.

Verification: `python -m unittest discover -s tests -p test_door_feedback.py -v` and the full repo suite. The synthetic door MP4 and receipt live outside the public repo.
