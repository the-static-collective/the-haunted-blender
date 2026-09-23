"""Observer-local memory feedback: remembered sight becomes a bounded visual residue.

A memory receipt establishes that one camera/I-eye previously had an authored
fact available. It does not contain pixels. This adapter captures pixels only
while that fact is actually present_to_eye in the supplied projection timeline,
then may replay those captured pixels after the fact becomes memory_residue.
"""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import catalog, observer_local, project, take_cut

SCHEMA = "haunted-blender/memory-feedback-receipt/v0"
ADAPTER = "observer-local-memory-feedback/v0"
WIDTH, HEIGHT, FPS, MAX_FRAMES = 320, 180, 12, 120
RESIDUE_START_PERCENT = 64
DECAY_PERCENT = 88
SHIFT_X_PER_FRAME = 1
MAX_SHIFT_X = 8


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _digest(value):
    return hashlib.sha256(project.stable_bytes(value)).hexdigest()


def _validate_projection(projection):
    _require(isinstance(projection, dict)
             and projection.get("schema") == observer_local.PROJECTION_SCHEMA,
             "Unknown observer-local projection")
    claimed = projection.get("projection_sha256")
    _require(isinstance(claimed, str), "Projection digest missing")
    unsigned = dict(projection)
    unsigned.pop("projection_sha256", None)
    _require(_digest(unsigned) == claimed, "Observer-local projection digest mismatch")

    receipt = projection.get("memory_receipt")
    _require(isinstance(receipt, dict)
             and receipt.get("schema") == observer_local.RECEIPT_SCHEMA,
             "Projection needs an observer memory receipt")
    receipt_claimed = receipt.get("receipt_sha256")
    unsigned_receipt = dict(receipt)
    unsigned_receipt.pop("receipt_sha256", None)
    _require(isinstance(receipt_claimed, str)
             and _digest(unsigned_receipt) == receipt_claimed,
             "Observer memory receipt digest mismatch")
    _require(receipt.get("observer_id") == projection.get("observer_id")
             and receipt.get("world_sha256") == projection.get("world_sha256")
             and receipt.get("beat") == projection.get("beat"),
             "Projection and memory receipt disagree")

    responses = projection.get("environment_response")
    _require(isinstance(responses, list), "Projection response must be a list")
    allowed = {"present_to_eye", "threshold_withheld", "memory_residue"}
    modes = {}
    for item in responses:
        _require(isinstance(item, dict) and set(item) == {"fact_id", "mode"},
                 "Malformed environment response")
        _require(isinstance(item["fact_id"], str) and item["mode"] in allowed,
                 "Unknown environment response")
        modes.setdefault(item["fact_id"], set()).add(item["mode"])
    residual = set(receipt.get("residual_memory_fact_ids", []))
    _require(residual == {fid for fid, values in modes.items()
                          if "memory_residue" in values},
             "Projection residue and memory receipt disagree")
    return modes


def _normalize_regions(regions):
    _require(isinstance(regions, dict) and regions,
             "Provide one or more authored memory regions")
    result = {}
    for fact_id, box in regions.items():
        _require(isinstance(fact_id, str) and fact_id,
                 "Memory region fact id must be a string")
        _require(isinstance(box, list) and len(box) == 4
                 and all(type(v) in (int, float) and not isinstance(v, bool) for v in box),
                 "Memory region must be [x0,y0,x1,y1]")
        x0, y0, x1, y1 = map(float, box)
        _require(0.0 <= x0 < x1 <= 1.0 and 0.0 <= y0 < y1 <= 1.0,
                 "Memory region coordinates must be normalized and ordered")
        px0 = min(WIDTH - 1, int(x0 * WIDTH))
        py0 = min(HEIGHT - 1, int(y0 * HEIGHT))
        px1 = max(px0 + 1, min(WIDTH, int(round(x1 * WIDTH))))
        py1 = max(py0 + 1, min(HEIGHT, int(round(y1 * HEIGHT))))
        result[fact_id] = {
            "normalized": [x0, y0, x1, y1],
            "pixels": [px0, py0, px1, py1],
        }
    return result


def _compile_timeline(frame_count, timeline, regions):
    _require(type(frame_count) is int and 1 <= frame_count <= MAX_FRAMES,
             "Invalid sampled frame count")
    _require(isinstance(timeline, list) and timeline,
             "Memory feedback requires a projection timeline")
    normalized_regions = _normalize_regions(regions)
    compiled = []
    cursor = 0
    observer_id = None
    world_sha = None
    previous_beat = -1
    residue_facts = set()

    for segment in timeline:
        _require(isinstance(segment, dict)
                 and set(segment) == {"start_frame", "end_frame_exclusive", "projection"},
                 "Timeline segments require start_frame, end_frame_exclusive and projection")
        start = segment["start_frame"]
        end = segment["end_frame_exclusive"]
        _require(type(start) is int and type(end) is int and start == cursor
                 and start < end <= frame_count,
                 "Timeline must cover sampled frames contiguously from frame zero")
        projection = segment["projection"]
        modes = _validate_projection(projection)
        if observer_id is None:
            observer_id = projection["observer_id"]
            world_sha = projection["world_sha256"]
        _require(projection["observer_id"] == observer_id,
                 "Timeline cannot change camera/I-eye")
        _require(projection["world_sha256"] == world_sha,
                 "Timeline cannot switch authored world state")
        _require(type(projection["beat"]) is int and projection["beat"] >= previous_beat,
                 "Timeline beats cannot run backward")
        previous_beat = projection["beat"]

        residue_here = sorted(fid for fid, values in modes.items()
                              if "memory_residue" in values)
        residue_facts.update(residue_here)
        _require(all(fid in normalized_regions for fid in residue_here),
                 "Every memory-residue fact needs an authored spatial region")
        compiled.append({
            "start_frame": start,
            "end_frame_exclusive": end,
            "projection": projection,
            "modes": modes,
            "residue_fact_ids": residue_here,
        })
        cursor = end

    _require(cursor == frame_count,
             "Projection timeline must cover every sampled frame exactly")
    return {
        "observer_id": observer_id,
        "world_sha256": world_sha,
        "segments": compiled,
        "regions": normalized_regions,
        "residue_fact_ids": sorted(residue_facts),
    }


def _capture(source, box):
    x0, y0, x1, y1 = box
    width = x1 - x0
    captured = bytearray(width * (y1 - y0) * 3)
    cursor = 0
    for y in range(y0, y1):
        start = (y * WIDTH + x0) * 3
        stop = (y * WIDTH + x1) * 3
        row = source[start:stop]
        captured[cursor:cursor + len(row)] = row
        cursor += len(row)
    return bytes(captured)


def _overlay(frame, remembered, box, age):
    x0, y0, x1, y1 = box
    width = x1 - x0
    strength = RESIDUE_START_PERCENT
    for _ in range(max(0, age - 1)):
        strength = strength * DECAY_PERCENT // 100
    if strength <= 0:
        return strength
    shift = min(MAX_SHIFT_X, age * SHIFT_X_PER_FRAME)
    cursor = 0
    for y in range(y0, y1):
        for x in range(x0, x1):
            target_x = x + shift
            memory_offset = cursor * 3
            cursor += 1
            if target_x >= WIDTH:
                continue
            out = (y * WIDTH + target_x) * 3
            # Cool, displaced afterimage: recognizable memory material, not a
            # claim that the current source still contains the remembered fact.
            mr = remembered[memory_offset]
            mg = remembered[memory_offset + 1]
            mb = remembered[memory_offset + 2]
            ghost = (mr * 3 // 5, mg * 4 // 5, min(255, mb + mb // 4 + 8))
            for channel in range(3):
                frame[out + channel] = (
                    frame[out + channel] * (100 - strength)
                    + ghost[channel] * strength
                ) // 100
    return strength


def _memory_frames(frames, compiled):
    frame_bytes = WIDTH * HEIGHT * 3
    _require(len(frames) % frame_bytes == 0, "Frame buffer is incomplete")
    count = len(frames) // frame_bytes
    _require(count > 0, "No frames to render")
    _require(compiled["segments"][-1]["end_frame_exclusive"] == count,
             "Compiled timeline does not match frame buffer")

    output = bytearray(len(frames))
    memories = {}
    stats = {
        fid: {"captured_frames": 0, "residue_frames": 0,
              "max_residue_age": 0, "last_strength_percent": 0}
        for fid in compiled["regions"]
    }
    segment_index = 0
    for index in range(count):
        while index >= compiled["segments"][segment_index]["end_frame_exclusive"]:
            segment_index += 1
        segment = compiled["segments"][segment_index]
        source = memoryview(frames)[index * frame_bytes:(index + 1) * frame_bytes]
        frame = memoryview(output)[index * frame_bytes:(index + 1) * frame_bytes]
        frame[:] = source

        for fact_id, region in compiled["regions"].items():
            modes = segment["modes"].get(fact_id, set())
            if "present_to_eye" in modes:
                memories[fact_id] = {
                    "pixels": _capture(source, region["pixels"]),
                    "age": 0,
                    "last_seen_frame": index,
                }
                stats[fact_id]["captured_frames"] += 1
            if "memory_residue" in modes:
                _require(fact_id in memories,
                         "Memory residue has no on-timeline visual capture")
                memories[fact_id]["age"] += 1
                strength = _overlay(frame, memories[fact_id]["pixels"],
                                    region["pixels"], memories[fact_id]["age"])
                stats[fact_id]["residue_frames"] += 1
                stats[fact_id]["max_residue_age"] = max(
                    stats[fact_id]["max_residue_age"], memories[fact_id]["age"])
                stats[fact_id]["last_strength_percent"] = strength
    return bytes(output), stats


def render(root, artifact_snapshot, acceptance_snapshot, timeline, regions, out):
    root = Path(root).expanduser().resolve()
    out = Path(out).expanduser().resolve()
    vault = root / "renders" / "memory-feedback"
    _require(out.parent == vault and out.suffix.lower() == ".mp4",
             "Output must be an MP4 in the private renders/memory-feedback vault")
    receipt_path = out.with_suffix(".mp4.receipt.json")
    _require(not out.exists() and not receipt_path.exists(),
             "Refusing to overwrite output or receipt")
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
    compiled = _compile_timeline(count, timeline, regions)
    output_frames, stats = _memory_frames(decoded.stdout, compiled)

    _require(catalog.digest_file(video) == witness["video_sha256"],
             "Accepted take changed during memory synthesis")
    vault.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="blender-memory-", dir=vault) as folder:
        staged = Path(folder) / "memory.mp4"
        subprocess.run(
            [ffmpeg, "-nostdin", "-v", "error", "-f", "rawvideo",
             "-pixel_format", "rgb24", "-video_size", f"{WIDTH}x{HEIGHT}",
             "-framerate", str(FPS), "-i", "pipe:0", "-an", "-c:v", "libx264",
             "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
             "-movflags", "+faststart", str(staged)],
            input=output_frames, capture_output=True, check=True, timeout=60,
        )
        take_cut._probe(staged, max_seconds=10)
        output_sha = catalog.digest_file(staged)
        _require(catalog.digest_file(video) == witness["video_sha256"],
                 "Accepted take changed before output was committed")

        segment_receipts = []
        for segment in compiled["segments"]:
            projection = segment["projection"]
            segment_receipts.append({
                "start_frame": segment["start_frame"],
                "end_frame_exclusive": segment["end_frame_exclusive"],
                "projection_sha256": projection["projection_sha256"],
                "memory_receipt_sha256": projection["memory_receipt"]["receipt_sha256"],
                "visible_fact_ids": projection["visible_fact_ids"],
                "residue_fact_ids": segment["residue_fact_ids"],
            })
        receipt = {
            "schema": SCHEMA, "adapter": ADAPTER, "status": "scoped_complete",
            "artifact_sha256": artifact_sha, "artifact_id": artifact["id"],
            "beat": witness["beat"], "request_sha256": request_sha,
            "acceptance_sha256": catalog.digest_file(Path(acceptance_snapshot)),
            "source_video_sha256": witness["video_sha256"],
            "source_duration_seconds": info["duration_seconds"],
            "frame_sampling": "normalized start, FFmpeg fps filter; original PTS not retained",
            "fps": FPS, "sample_count": count, "width": WIDTH, "height": HEIGHT,
            "observer_id": compiled["observer_id"],
            "world_sha256": compiled["world_sha256"],
            "projection_segments": segment_receipts,
            "timeline_sha256": _digest([
                {"start_frame": row["start_frame"],
                 "end_frame_exclusive": row["end_frame_exclusive"],
                 "projection_sha256": row["projection"]["projection_sha256"]}
                for row in compiled["segments"]
            ]),
            "memory_regions": compiled["regions"],
            "residue_fact_ids": compiled["residue_fact_ids"],
            "memory_statistics": stats,
            "visual_policy": {
                "capture": "last source pixels while fact is present_to_eye",
                "residue_start_percent": RESIDUE_START_PERCENT,
                "decay_percent_per_residue_frame": DECAY_PERCENT,
                "shift_x_per_frame": SHIFT_X_PER_FRAME,
                "max_shift_x": MAX_SHIFT_X,
            },
            "output_sha256": output_sha,
            "distribution_authorized": False,
            "nonclaims": [
                "A memory receipt contains fact history, not pixels",
                "Residual pixels were captured only while the fact was present_to_eye in this timeline",
                "The afterimage is observer-conditioned cinematic presentation, not evidence of current presence",
                "Authored regions are filmmaker spatial assertions, not inferred tracking or identity",
                "The output is a derived proposal with no inherited publication or scene authority",
            ],
        }
        created = False
        try:
            with out.open("xb") as dst, staged.open("rb") as src:
                created = True
                shutil.copyfileobj(src, dst)
            _require(catalog.digest_file(out) == output_sha,
                     "Copy changed memory-feedback video")
            with receipt_path.open("xb") as handle:
                handle.write(project.stable_bytes(receipt) + b"\n")
        except Exception:
            if created:
                out.unlink(missing_ok=True)
            raise
    return {"video": str(out), "receipt": str(receipt_path),
            "output_sha256": output_sha, "sample_count": count,
            "residue_fact_ids": compiled["residue_fact_ids"]}
