"""An accepted door take, re-performed by editing its sampled frame order."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from . import catalog, project, take_cut

SCHEMA = "haunted-blender/door-hinge-dance-receipt/v0"
ADAPTER = "local-frame-reorder/v0"
WIDTH, HEIGHT, FPS, MAX_FRAMES = 320, 180, 24, 240


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def score(count):
    """Return a complete output-frame → sampled-source-frame edit map."""
    _require(type(count) is int and 12 <= count <= MAX_FRAMES,
             "Door dance requires 12–240 sampled source frames")
    hinge = round((count - 1) * 0.50)
    retreat = round((count - 1) * 0.36)
    _require(hinge - retreat >= 2 and count - hinge >= 3,
             "Not enough frames to make a continuous hesitation")
    phases = [
        ("open_partway", list(range(hinge + 1))),
        ("pause_partway", [hinge] * 4),
        ("close_a_little", list(range(hinge - 1, retreat - 1, -1))),
        ("pause_reclosed", [retreat] * 2),
        ("open_again", list(range(retreat + 1, count))),
    ]
    mapping = []
    spans = []
    for name, indices in phases:
        start = len(mapping)
        mapping.extend(indices)
        spans.append({"action": name, "output_start": start,
                      "output_end_exclusive": len(mapping),
                      "source_start": indices[0], "source_end": indices[-1]})
    _require(all(abs(a - b) <= 1 for a, b in zip(mapping, mapping[1:])),
             "Edit contains a discontinuous source-frame jump")
    return {"source_frame_indices": mapping, "phases": spans,
            "hinge_frame": hinge, "retreat_frame": retreat}


def render(root, artifact_snapshot, acceptance_snapshot, out):
    root = Path(root).expanduser().resolve()
    out = Path(out).expanduser().resolve()
    vault = root / "renders" / "door-dances"
    _require(out.parent == vault and out.suffix.lower() == ".mp4",
             "Output must be an MP4 in the private renders/door-dances vault")
    receipt_path = out.with_suffix(".mp4.receipt.json")
    _require(not out.exists() and not receipt_path.exists(), "Refusing to overwrite output or receipt")
    ffmpeg = shutil.which("ffmpeg")
    _require(ffmpeg is not None, "FFmpeg is required")
    artifact, artifact_sha, witness, request_sha, source = take_cut._accepted_take(
        root, artifact_snapshot, acceptance_snapshot)
    source_info = take_cut._probe(source, max_seconds=10)
    decoded = subprocess.run(
        [ffmpeg, "-nostdin", "-v", "error", "-i", str(source), "-map", "0:v:0",
         "-an", "-t", "10", "-vf",
         f"setpts=PTS-STARTPTS,fps={FPS},scale={WIDTH}:{HEIGHT}:flags=lanczos,format=rgb24",
         "-frames:v", str(MAX_FRAMES), "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"],
        capture_output=True, check=True, timeout=45,
    )
    frame_bytes = WIDTH * HEIGHT * 3
    _require(len(decoded.stdout) % frame_bytes == 0, "Decoder produced incomplete frames")
    count = len(decoded.stdout) // frame_bytes
    edit = score(count)
    edited = b"".join(decoded.stdout[i * frame_bytes:(i + 1) * frame_bytes]
                      for i in edit["source_frame_indices"])
    _require(catalog.digest_file(source) == witness["video_sha256"],
             "Accepted door changed during decoding")
    vault.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="blender-door-dance-", dir=vault) as folder:
        staged = Path(folder) / "dance.mp4"
        subprocess.run(
            [ffmpeg, "-nostdin", "-v", "error", "-f", "rawvideo", "-pixel_format", "rgb24",
             "-video_size", f"{WIDTH}x{HEIGHT}", "-framerate", str(FPS), "-i", "pipe:0",
             "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
             "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(staged)],
            input=edited, capture_output=True, check=True, timeout=60,
        )
        result_info = take_cut._probe(staged, max_seconds=20)
        output_sha = catalog.digest_file(staged)
        _require(catalog.digest_file(source) == witness["video_sha256"],
                 "Accepted door changed before output was committed")
        receipt = {
            "schema": SCHEMA, "adapter": ADAPTER, "status": "scoped_complete",
            "artifact_sha256": artifact_sha, "artifact_id": artifact["id"],
            "beat": witness["beat"], "request_sha256": request_sha,
            "acceptance_sha256": catalog.digest_file(Path(acceptance_snapshot)),
            "source_video_sha256": witness["video_sha256"],
            "source_duration_seconds": source_info["duration_seconds"],
            "sampling": "normalized start, FFmpeg fps filter; original frame PTS not retained",
            "fps": FPS, "width": WIDTH, "height": HEIGHT,
            "source_sample_count": count, "output_frame_count": len(edit["source_frame_indices"]),
            "output_duration_seconds": result_info["duration_seconds"],
            "edit": edit, "output_sha256": output_sha,
            "sound": "omitted for the private performance preview",
            "distribution_authorized": False,
            "nonclaims": ["The reversal reorders derived source frames; it does not show a witnessed second closing",
                          "The output is a new proposal, not an accepted take for any scene",
                          "Source acceptance does not authorize publication or reuse of the derivative"],
        }
        created = False
        try:
            with out.open("xb") as dst, staged.open("rb") as src:
                created = True
                shutil.copyfileobj(src, dst)
            _require(catalog.digest_file(out) == output_sha, "Copy changed the edited video")
            with receipt_path.open("xb") as handle:
                handle.write(project.stable_bytes(receipt) + b"\n")
        except Exception:
            if created:
                out.unlink(missing_ok=True)
            raise
    return {"video": str(out), "receipt": str(receipt_path),
            "output_sha256": output_sha, "source_frames": count,
            "output_frames": len(edit["source_frame_indices"])}
