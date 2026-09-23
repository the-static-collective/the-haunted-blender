"""Shot-scoped private cut: one accepted moving take among verified static beats."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import catalog, creative_take, project, scene_artifact
from .render import FPS, HEIGHT, WIDTH

SCHEMA = "haunted-blender/accepted-take-cut-receipt/v0"
ADAPTER = "ffmpeg-one-accepted-take-cut/v0"


def _require(value, message):
    if not value:
        raise ValueError(message)


def _probe(path, *, max_seconds=30):
    ffprobe = shutil.which("ffprobe")
    _require(ffprobe is not None, "ffprobe is required")
    result = subprocess.run([ffprobe, "-v", "error", "-show_entries",
                             "format=duration:stream=index,codec_type,width,height",
                             "-of", "json", str(path)], capture_output=True, text=True,
                            check=True, timeout=30)
    info = json.loads(result.stdout)
    video = [s for s in info.get("streams", []) if s.get("codec_type") == "video"]
    _require(len(video) == 1 and video[0].get("width", 0) > 0
             and video[0].get("height", 0) > 0, "Expected one playable video stream")
    duration = float(info["format"]["duration"])
    _require(0 < duration <= max_seconds, "Video duration outside this adapter's bounds")
    return {"duration_seconds": duration, "width": video[0]["width"],
            "height": video[0]["height"]}


def _accepted_take(root, artifact_snapshot, acceptance_snapshot):
    root = Path(root).expanduser().resolve()
    acceptance_path = Path(acceptance_snapshot).expanduser().resolve(strict=True)
    witness = json.loads(acceptance_path.read_text(encoding="utf-8"))
    _require(witness.get("schema") == "haunted-blender/accepted-creative-take/v0"
             and witness.get("status") == "filmmaker_accepted_private_preview"
             and witness.get("distribution_authorized") is False
             and acceptance_path == root / "snapshots" / "creative-take-acceptances" /
             (creative_take._sha(witness) + ".json"),
             "Take acceptance witness changed or is outside its vault")
    artifact, artifact_sha = scene_artifact.load(root, artifact_snapshot)
    _require(witness["artifact_sha256"] == artifact_sha,
             "Take was accepted for a different Scene Artifact")
    request_path = root / "snapshots" / "creative-takes" / (witness["request_sha256"] + ".json")
    request, request_sha = creative_take.load_request(root, request_path)
    _require(request_sha == witness["request_sha256"]
             and request["artifact_sha256"] == artifact_sha
             and request["beat"] == witness["beat"],
             "Take request does not match accepted beat")
    video = root / "renders" / "creative-takes" / (request_sha + "-" + witness["video_sha256"] + ".mp4")
    receipt_path = video.with_suffix(".mp4.receipt.json")
    _require(video.is_file() and not video.is_symlink() and receipt_path.is_file()
             and catalog.digest_file(video) == witness["video_sha256"]
             and catalog.digest_file(receipt_path) == witness["admission_receipt_sha256"],
             "Accepted take video or admission receipt changed")
    admission = json.loads(receipt_path.read_text(encoding="utf-8"))
    _require(admission.get("schema") == creative_take.RECEIPT_SCHEMA
             and admission.get("status") == "candidate_admitted_not_filmmaker_accepted"
             and admission.get("request_sha256") == request_sha
             and admission.get("output_sha256") == witness["video_sha256"]
             and admission.get("artifact_sha256") == artifact_sha
             and admission.get("beat") == witness["beat"],
             "Admission receipt is inconsistent with accepted take")
    _require(sum(s["beat"] == witness["beat"] for s in artifact["shots"]) == 1,
             "Accepted take beat is absent from Scene Artifact")
    return artifact, artifact_sha, witness, request_sha, video


def _sources(root, artifact):
    con = catalog.connect(Path(root))
    try:
        entries = []
        for shot in artifact["shots"]:
            row = con.execute("SELECT path,sha256 FROM assets WHERE id=?",
                              (shot["frame_asset_id"],)).fetchone()
            _require(row is not None and row["sha256"] == shot["frame_sha256"],
                     "Static source differs from accepted shot")
            path = Path(row["path"])
            _require(path.is_file() and catalog.digest_file(path) == shot["frame_sha256"],
                     "Static source bytes changed")
            entries.append({"beat": shot["beat"], "frame": path,
                            "sha256": shot["frame_sha256"], "duration_ms": shot["duration_ms"]})
        return entries
    finally:
        con.close()


def render(root, artifact_snapshot, acceptance_snapshot, out):
    """Render exactly one accepted motion take, keeping every other beat static."""
    root = Path(root).expanduser().resolve()
    out = Path(out).expanduser().resolve()
    receipt_path = out.with_suffix(out.suffix + ".take-cut.json")
    _require(not out.exists() and not receipt_path.exists(),
             "Refusing to overwrite a cut or receipt")
    _require(out.suffix.lower() == ".mp4", "Cut output must be MP4")
    ffmpeg = shutil.which("ffmpeg")
    _require(ffmpeg is not None, "FFmpeg is required")
    artifact, artifact_sha, witness, request_sha, video = _accepted_take(
        root, artifact_snapshot, acceptance_snapshot)
    sources = _sources(root, artifact)
    take_info = _probe(video)
    scale = (f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease:flags=lanczos,"
             f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={FPS},format=yuv420p")
    shots = []
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="blender-take-cut-", dir=out.parent) as folder:
        tmp = Path(folder)
        segments = []
        for index, source in enumerate(sources):
            moving = source["beat"] == witness["beat"]
            segment = tmp / f"shot-{index:06d}.mp4"
            command = [ffmpeg, "-nostdin", "-v", "error", "-y"]
            if moving:
                command += ["-i", str(video), "-map", "0:v:0"]
            else:
                command += ["-loop", "1", "-framerate", str(FPS), "-i", str(source["frame"]),
                            "-t", f"{source['duration_ms'] / 1000:.3f}"]
            command += ["-vf", scale, "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-video_track_timescale", "12288", str(segment)]
            subprocess.run(command, check=True, capture_output=True, timeout=90)
            segments.append(segment)
            shots.append({"beat": source["beat"], "kind": "accepted_video_take" if moving else "static_still",
                          "source_sha256": witness["video_sha256"] if moving else source["sha256"],
                          "segment_sha256": catalog.digest_file(segment)})
        playlist = tmp / "playlist.txt"
        playlist.write_text("".join(f"file '{s.name}'\n" for s in segments), encoding="utf-8")
        rendered = tmp / "cut.mp4"
        subprocess.run([ffmpeg, "-nostdin", "-v", "error", "-y", "-f", "concat", "-safe", "1",
                        "-i", str(playlist), "-c", "copy", "-movflags", "+faststart", str(rendered)],
                       check=True, capture_output=True, timeout=90)
        _accepted_take(root, artifact_snapshot, acceptance_snapshot)
        for source in sources:
            _require(catalog.digest_file(source["frame"]) == source["sha256"],
                     "Static source changed during render; no receipt issued")
        output_info = _probe(rendered, max_seconds=600)
        _require(output_info["width"] == WIDTH and output_info["height"] == HEIGHT,
                 "Cut dimensions differ from render contract")
        try:
            with out.open("xb") as handle, rendered.open("rb") as src:
                shutil.copyfileobj(src, handle)
        except Exception:
            out.unlink(missing_ok=True)
            raise
    receipt = {
        "schema": SCHEMA, "status": "scoped_complete", "adapter": ADAPTER,
        "artifact_sha256": artifact_sha,
        "acceptance_sha256": catalog.digest_file(Path(acceptance_snapshot)),
        "request_sha256": request_sha, "take_input": take_info,
        "shot_count": len(shots), "shots": shots, "output_sha256": catalog.digest_file(out),
        "output_duration_seconds": output_info["duration_seconds"],
        "output_width": WIDTH, "output_height": HEIGHT, "output_fps": FPS,
        "sound": "omitted for this silent private preview",
        "distribution_authorized": False,
        "nonclaims": ["A moving take does not establish a real-world event",
                      "This cut does not modify or supersede the N0 still storyboard",
                      "A scoped preview is not a finished dramatic film or a release"],
    }
    try:
        with receipt_path.open("xb") as handle:
            handle.write(project.stable_bytes(receipt) + b"\n")
    except Exception:
        out.unlink(missing_ok=True)
        raise
    return {"output": str(out), "receipt": str(receipt_path),
            "output_sha256": receipt["output_sha256"], "shots": len(shots)}
