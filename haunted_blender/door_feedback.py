"""A bounded, local feedback study inspired by video-synth patching.

No Hydra package is embedded or executed. Each output frame consumes the
preceding *derived* trail and a difference from an accepted input take.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from . import catalog, project, take_cut

SCHEMA = "haunted-blender/door-feedback-receipt/v0"
ADAPTER = "local-motion-feedback/v0"
WIDTH, HEIGHT, FPS, MAX_FRAMES = 320, 180, 12, 120
SHIFT_X, SHIFT_Y, DECAY_PERCENT = 3, 1, 89
MOTION_FLOOR = 18


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _echo_frames(frames):
    """Recursive shifted motion trace, mixed over the current source frame."""
    pixels = WIDTH * HEIGHT
    frame_bytes = pixels * 3
    previous_source = None
    previous_trace = bytearray(pixels)
    output = bytearray(len(frames))
    for index in range(len(frames) // frame_bytes):
        source = memoryview(frames)[index * frame_bytes:(index + 1) * frame_bytes]
        frame = memoryview(output)[index * frame_bytes:(index + 1) * frame_bytes]
        if previous_source is None:
            frame[:] = source
            previous_source = bytes(source)
            continue
        trace = bytearray(pixels)
        for y in range(HEIGHT):
            for x in range(WIDTH):
                p = y * WIDTH + x
                offset = p * 3
                delta = max(abs(source[offset + c] - previous_source[offset + c])
                            for c in range(3))
                if delta < MOTION_FLOOR:
                    delta = 0
                shifted = ((previous_trace[(y - SHIFT_Y) * WIDTH + (x - SHIFT_X)]
                            * DECAY_PERCENT // 100)
                           if y >= SHIFT_Y and x >= SHIFT_X else 0)
                intensity = max(min(255, delta * 2), shifted)
                trace[p] = intensity
                # Cold echoes separate an older doorway edge from the warm source.
                frame[offset] = min(255, source[offset] + intensity // 8)
                frame[offset + 1] = min(255, source[offset + 1] + intensity * 2 // 5)
                frame[offset + 2] = min(255, source[offset + 2] + intensity * 3 // 4)
        previous_source = bytes(source)
        previous_trace = trace
    return bytes(output)


def render(root, artifact_snapshot, acceptance_snapshot, out):
    root = Path(root).expanduser().resolve()
    out = Path(out).expanduser().resolve()
    vault = root / "renders" / "door-feedback"
    _require(out.parent == vault and out.suffix.lower() == ".mp4",
             "Output must be an MP4 in the private renders/door-feedback vault")
    receipt_path = out.with_suffix(".mp4.receipt.json")
    _require(not out.exists() and not receipt_path.exists(), "Refusing to overwrite output or receipt")
    ffmpeg = shutil.which("ffmpeg")
    _require(ffmpeg is not None, "FFmpeg is required")
    artifact, artifact_sha, witness, request_sha, video = take_cut._accepted_take(
        root, artifact_snapshot, acceptance_snapshot)
    info = take_cut._probe(video, max_seconds=10)
    decoded = subprocess.run(
        [ffmpeg, "-nostdin", "-v", "error", "-i", str(video), "-map", "0:v:0",
         "-an", "-t", "10", "-vf",
         f"setpts=PTS-STARTPTS,fps={FPS},scale={WIDTH}:{HEIGHT}:flags=lanczos,format=rgb24",
         "-frames:v", str(MAX_FRAMES), "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"],
        capture_output=True, check=True, timeout=45,
    )
    frame_bytes = WIDTH * HEIGHT * 3
    _require(len(decoded.stdout) % frame_bytes == 0, "Decoder produced incomplete frames")
    count = len(decoded.stdout) // frame_bytes
    _require(2 <= count <= MAX_FRAMES, "Expected 2–120 sampled frames")
    output_frames = _echo_frames(decoded.stdout)
    _require(catalog.digest_file(video) == witness["video_sha256"],
             "Accepted take changed during feedback synthesis")
    vault.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="blender-feedback-", dir=vault) as folder:
        staged = Path(folder) / "echo.mp4"
        subprocess.run(
            [ffmpeg, "-nostdin", "-v", "error", "-f", "rawvideo", "-pixel_format", "rgb24",
             "-video_size", f"{WIDTH}x{HEIGHT}", "-framerate", str(FPS), "-i", "pipe:0",
             "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
             "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(staged)],
            input=output_frames, capture_output=True, check=True, timeout=60,
        )
        take_cut._probe(staged, max_seconds=10)
        output_sha = catalog.digest_file(staged)
        _require(catalog.digest_file(video) == witness["video_sha256"],
                 "Accepted take changed before output was committed")
        receipt = {
            "schema": SCHEMA, "adapter": ADAPTER, "status": "scoped_complete",
            "artifact_sha256": artifact_sha, "artifact_id": artifact["id"],
            "beat": witness["beat"], "request_sha256": request_sha,
            "acceptance_sha256": catalog.digest_file(Path(acceptance_snapshot)),
            "source_video_sha256": witness["video_sha256"],
            "source_duration_seconds": info["duration_seconds"],
            "frame_sampling": "normalized start, FFmpeg fps filter; original PTS not retained",
            "fps": FPS, "sample_count": count, "width": WIDTH, "height": HEIGHT,
            "feedback": {"type": "source-frame difference plus recursive shifted trace",
                         "shift_x_px": SHIFT_X, "shift_y_px": SHIFT_Y,
                         "decay_percent": DECAY_PERCENT, "motion_floor": MOTION_FLOOR,
                         "first_frame": "source copy, trace zero"},
            "output_sha256": output_sha, "distribution_authorized": False,
            "hydra_engine_executed": False,
            "nonclaims": ["Hydra inspired this topology; Hydra did not render the MP4",
                          "The echo is an interpretation, not witnessed action",
                          "The output has no inherited permission or scene placement"],
        }
        created = False
        try:
            with out.open("xb") as dst, staged.open("rb") as src:
                created = True
                shutil.copyfileobj(src, dst)
            _require(catalog.digest_file(out) == output_sha, "Copy changed derived video")
            with receipt_path.open("xb") as handle:
                handle.write(project.stable_bytes(receipt) + b"\n")
        except Exception:
            if created:
                out.unlink(missing_ok=True)
            raise
    return {"video": str(out), "receipt": str(receipt_path),
            "output_sha256": output_sha, "sample_count": count}
