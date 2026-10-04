"""Experimental spatial strips sampled from an independently accepted moving take."""
from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

from . import catalog, project, take_cut

SCHEMA = "haunted-blender/time-slice-receipt/v0"
ADAPTER = "ffmpeg-time-slice/v0"
WIDTH, HEIGHT, SAMPLE_FPS, STRIPS = 320, 180, 8, 32


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def render(root, artifact_snapshot, acceptance_snapshot, out):
    """Render a private PNG; strip position indexes time in the accepted clip."""
    root = Path(root).expanduser().resolve()
    out = Path(out).expanduser().resolve()
    vault = root / "renders" / "time-slices"
    _require(out.parent == vault and out.suffix.lower() == ".png",
             "Output must be a PNG in the private renders/time-slices vault")
    receipt_path = out.with_suffix(".png.receipt.json")
    _require(not out.exists() and not receipt_path.exists(), "Refusing to overwrite output or receipt")
    ffmpeg = shutil.which("ffmpeg")
    _require(ffmpeg is not None, "FFmpeg is required")
    artifact, artifact_sha, witness, request_sha, video = take_cut._accepted_take(
        root, artifact_snapshot, acceptance_snapshot)
    info = take_cut._probe(video, max_seconds=10)
    # Decode at fixed, normalized sampling cadence. Bounded output is < 14 MB.
    decoded = subprocess.run(
        [ffmpeg, "-nostdin", "-v", "error", "-i", str(video), "-map", "0:v:0",
         "-an", "-t", "10", "-vf",
         f"setpts=PTS-STARTPTS,fps={SAMPLE_FPS},scale={WIDTH}:{HEIGHT}:flags=lanczos,format=rgb24",
         "-frames:v", "80", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"],
        capture_output=True, check=True, timeout=45,
    )
    frame_bytes = WIDTH * HEIGHT * 3
    _require(len(decoded.stdout) % frame_bytes == 0, "Decoder produced incomplete frames")
    count = len(decoded.stdout) // frame_bytes
    _require(2 <= count <= 80, "Expected 2–80 sampled frames")
    pixels = bytearray(frame_bytes)
    strips = []
    pitch = WIDTH * 3
    for index in range(STRIPS):
        start_x, end_x = index * WIDTH // STRIPS, (index + 1) * WIDTH // STRIPS
        sample = index * (count - 1) // (STRIPS - 1)
        frame_offset = sample * frame_bytes
        for y in range(HEIGHT):
            offset = y * pitch + start_x * 3
            pixels[offset:offset + (end_x - start_x) * 3] = decoded.stdout[
                frame_offset + offset:frame_offset + offset + (end_x - start_x) * 3]
        strips.append({"x_start": start_x, "x_end_exclusive": end_x,
                       "sample_index": sample,
                       "nominal_sample_time_seconds": round(sample / SAMPLE_FPS, 3)})
    encoded = subprocess.run(
        [ffmpeg, "-nostdin", "-v", "error", "-f", "rawvideo", "-pixel_format", "rgb24",
         "-video_size", f"{WIDTH}x{HEIGHT}", "-i", "pipe:0", "-frames:v", "1",
         "-f", "image2pipe", "-vcodec", "png", "pipe:1"],
        input=bytes(pixels), capture_output=True, check=True, timeout=30,
    )
    _require(encoded.stdout.startswith(b"\x89PNG\r\n\x1a\n"), "Encoder did not produce PNG")
    _require(catalog.digest_file(video) == witness["video_sha256"],
             "Accepted take changed during rendering")
    receipt = {
        "schema": SCHEMA, "adapter": ADAPTER, "status": "scoped_complete",
        "artifact_sha256": artifact_sha, "artifact_id": artifact["id"],
        "beat": witness["beat"], "request_sha256": request_sha,
        "acceptance_sha256": catalog.digest_file(Path(acceptance_snapshot)),
        "source_video_sha256": witness["video_sha256"],
        "source_duration_seconds": info["duration_seconds"],
        "sampling": "normalized video start; ffmpeg fps filter; frame indices are derived samples",
        "sample_fps": SAMPLE_FPS, "sample_count": count,
        "width": WIDTH, "height": HEIGHT, "strips": strips,
        "output_sha256": hashlib.sha256(encoded.stdout).hexdigest(),
        "distribution_authorized": False,
        "nonclaims": ["Strip time labels are nominal sample positions, not original frame timestamps",
                      "The spatial composite is an interpretation, not a witnessed event",
                      "A derived image has no inherited authority to publish or enter a scene"],
    }
    vault.mkdir(parents=True, exist_ok=True)
    created = False
    try:
        with out.open("xb") as handle:
            created = True
            handle.write(encoded.stdout)
        with receipt_path.open("xb") as handle:
            handle.write(project.stable_bytes(receipt) + b"\n")
    except Exception:
        if created:
            out.unlink(missing_ok=True)
        raise
    return {"image": str(out), "receipt": str(receipt_path),
            "output_sha256": receipt["output_sha256"], "sample_count": count}
