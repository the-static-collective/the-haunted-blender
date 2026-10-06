"""FRANKEN BLENDER 008j — Paper Director / Shot Grammar.

Directs an already-complete puppet movie by cutting and reframing the same
rendered world. No provider generation is involved.

The Director does not change puppet motion, lyric timing, harvested-source
authority, or audio authority. It decides only *when and how the existing frame
is viewed*.
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

from .scene_growth import TIMING_SCHEMA

PLAN_SCHEMA = "haunted-blender/paper-director-plan/v1"
RECEIPT_SCHEMA = "haunted-blender/paper-director-render-receipt/v1"

SHOT_TYPES = (
    "ESTABLISH",
    "WIDE",
    "SPEAKER",
    "CLOSE_UP",
    "REACTION",
    "INSERT",
    "LYRIC_WORLD",
    "CHAOS",
    "RETURN",
)

DEFAULT_MAX_SHOT_SECONDS = 3.2
DEFAULT_MIN_SHOT_SECONDS = 0.45


def _stable(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _sha(value: object) -> str:
    return hashlib.sha256(_stable(value)).hexdigest()


def _file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _probe(path: Path) -> dict:
    proc = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries",
            "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate",
            "-of", "json", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    raw = json.loads(proc.stdout)
    video = next(
        (s for s in (raw.get("streams") or []) if s.get("codec_type") == "video"),
        None,
    )
    if not video:
        raise ValueError("Paper Director requires a video stream")
    audio = next(
        (s for s in (raw.get("streams") or []) if s.get("codec_type") == "audio"),
        None,
    )
    return {
        "durationSeconds": round(float((raw.get("format") or {}).get("duration") or 0), 6),
        "width": int(video.get("width") or 0),
        "height": int(video.get("height") or 0),
        "frameRate": str(video.get("r_frame_rate") or ""),
        "videoCodec": video.get("codec_name"),
        "hasAudio": audio is not None,
        "audioCodec": audio.get("codec_name") if audio else None,
    }


def _find_gate(timing: dict, at: float) -> dict | None:
    gates = sorted(timing.get("gates") or [], key=lambda row: float(row["at"]))
    current = None
    for gate in gates:
        if float(gate["at"]) <= at + 1e-9:
            current = gate
        else:
            break
    return current


def _insert_at(performance: dict | None, at: float) -> dict | None:
    if not performance:
        return None
    plan = performance.get("movingInsertPlan") or {}
    for row in plan.get("inserts") or []:
        if float(row["start"]) <= at <= float(row["end"]):
            return row
    return None


def _weakness_at(doctor_report: dict | None, at: float) -> dict | None:
    if not doctor_report:
        return None
    for row in doctor_report.get("windows") or []:
        if float(row["start"]) <= at < float(row["end"]):
            return row
    return None


def _cue_shot(
    cue: dict,
    index: int,
    *,
    gate: dict | None,
    insert: dict | None,
    weakness: dict | None,
) -> str:
    text = str(cue.get("text") or "")
    kind = str((gate or {}).get("kind") or "").lower()

    if weakness and float(weakness.get("weaknessScore") or 0) >= 0.68:
        dominant = weakness.get("dominantWeakness")
        if insert and dominant in {"stasis", "recentRepetition", "noveltyDeficit"}:
            return "INSERT"
        if dominant in {"stasis", "sourceOveruse", "recentRepetition"}:
            return "REACTION"

    if insert and index % 5 == 3:
        return "INSERT"
    if "!" in text:
        return "CLOSE_UP"
    if "?" in text:
        return "REACTION"
    if kind == "chorus":
        return ("WIDE", "CLOSE_UP", "LYRIC_WORLD")[index % 3]
    if kind in {"bridge", "breakdown"}:
        return ("LYRIC_WORLD", "REACTION", "CLOSE_UP")[index % 3]
    return ("SPEAKER", "REACTION", "WIDE", "LYRIC_WORLD")[index % 4]


def _append(
    shots: list[dict],
    *,
    start: float,
    end: float,
    shot_type: str,
    reason: str,
    gate: dict | None = None,
    cue_index: int | None = None,
    insert: dict | None = None,
    weakness: dict | None = None,
) -> None:
    if end - start < 1e-6:
        return
    if shot_type not in SHOT_TYPES:
        raise ValueError(f"Unknown shot type: {shot_type}")
    shots.append({
        "id": f"shot-{len(shots) + 1:04d}",
        "start": round(start, 6),
        "end": round(end, 6),
        "durationSeconds": round(end - start, 6),
        "type": shot_type,
        "reason": reason,
        "gateId": (gate or {}).get("id"),
        "gateKind": (gate or {}).get("kind"),
        "cueIndex": cue_index,
        "insertId": (insert or {}).get("id"),
        "insertRole": (insert or {}).get("role"),
        "weakWindowId": (weakness or {}).get("id"),
        "weaknessScore": (weakness or {}).get("weaknessScore"),
    })


def _split_long_shots(
    shots: list[dict],
    *,
    max_shot_seconds: float,
) -> list[dict]:
    result = []
    alternate = ("WIDE", "SPEAKER", "REACTION", "LYRIC_WORLD", "RETURN")
    for shot in shots:
        duration = float(shot["end"]) - float(shot["start"])
        if duration <= max_shot_seconds + 1e-9:
            result.append(shot)
            continue
        count = int(math.ceil(duration / max_shot_seconds))
        span = duration / count
        for i in range(count):
            child = dict(shot)
            start = float(shot["start"]) + i * span
            end = float(shot["end"]) if i == count - 1 else start + span
            child["start"] = round(start, 6)
            child["end"] = round(end, 6)
            child["durationSeconds"] = round(end - start, 6)
            if i:
                child["type"] = alternate[(len(result) + i) % len(alternate)]
                child["reason"] = "anti-boredom hard split"
            result.append(child)

    for i, row in enumerate(result, start=1):
        row["id"] = f"shot-{i:04d}"
    return result


def _repair_repetition(shots: list[dict], performance: dict | None) -> list[dict]:
    """No adjacent shot may repeat if a bounded alternative exists."""
    fixed = []
    fallback = ("WIDE", "SPEAKER", "REACTION", "LYRIC_WORLD", "RETURN")
    for index, shot in enumerate(shots):
        row = dict(shot)
        if fixed and row["type"] == fixed[-1]["type"]:
            at = (float(row["start"]) + float(row["end"])) / 2
            insert = _insert_at(performance, at)
            if insert and fixed[-1]["type"] != "INSERT":
                row["type"] = "INSERT"
                row["insertId"] = insert.get("id")
                row["insertRole"] = insert.get("role")
                row["reason"] = "anti-repeat insert"
            else:
                for candidate in fallback:
                    if candidate != fixed[-1]["type"]:
                        row["type"] = candidate
                        row["reason"] = "anti-repeat reframing"
                        break
        fixed.append(row)
    return fixed


def plan(
    timing: dict,
    *,
    performance: dict | None = None,
    doctor_report: dict | None = None,
    max_shot_seconds: float = DEFAULT_MAX_SHOT_SECONDS,
    min_shot_seconds: float = DEFAULT_MIN_SHOT_SECONDS,
) -> dict:
    if timing.get("schema") != TIMING_SCHEMA:
        raise ValueError("Paper Director expects normalized track timing")
    duration = float(timing["duration"])
    if duration <= 0:
        raise ValueError("Timing duration must be positive")
    if not (1.0 <= max_shot_seconds <= 8.0):
        raise ValueError("max_shot_seconds must be between 1 and 8")
    if not (0.2 <= min_shot_seconds <= 2.0):
        raise ValueError("min_shot_seconds must be between 0.2 and 2")

    cues = sorted(timing.get("lyricsCues") or [], key=lambda row: float(row["start"]))
    shots = []
    cursor = 0.0

    if cues:
        first_start = max(0.0, float(cues[0]["start"]))
        establish_end = min(duration, max(0.7, min(first_start, 1.4)))
    else:
        establish_end = min(duration, 1.2)
    _append(
        shots,
        start=0.0,
        end=establish_end,
        shot_type="ESTABLISH",
        reason="orient before first performance beat",
        gate=_find_gate(timing, 0.0),
    )
    cursor = establish_end

    for index, cue in enumerate(cues):
        cue_start = max(0.0, float(cue["start"]))
        cue_end = min(duration, max(cue_start + min_shot_seconds, float(cue["end"])))
        if cue_start > cursor + 0.08:
            gap_end = min(cue_start, cursor + max_shot_seconds)
            _append(
                shots,
                start=cursor,
                end=gap_end,
                shot_type="REACTION" if index else "RETURN",
                reason="hold/reaction between lyric cues",
                gate=_find_gate(timing, cursor),
                weakness=_weakness_at(doctor_report, cursor),
            )
            cursor = gap_end
            if cue_start > cursor + 0.08:
                _append(
                    shots,
                    start=cursor,
                    end=cue_start,
                    shot_type="WIDE",
                    reason="long inter-cue reset",
                    gate=_find_gate(timing, cursor),
                )
                cursor = cue_start

        start = max(cursor, cue_start)
        if start >= duration:
            break
        center = (start + cue_end) / 2
        gate = _find_gate(timing, center)
        insert = _insert_at(performance, center)
        weakness = _weakness_at(doctor_report, center)
        shot_type = _cue_shot(
            cue, index, gate=gate, insert=insert, weakness=weakness
        )
        _append(
            shots,
            start=start,
            end=cue_end,
            shot_type=shot_type,
            reason="lyric cue grammar",
            gate=gate,
            cue_index=cue.get("index"),
            insert=insert,
            weakness=weakness,
        )
        cursor = max(cursor, cue_end)

    if cursor < duration:
        _append(
            shots,
            start=cursor,
            end=duration,
            shot_type="RETURN",
            reason="return to stable world at tail",
            gate=_find_gate(timing, cursor),
            weakness=_weakness_at(doctor_report, cursor),
        )

    # Normalize to exact contiguous coverage.
    shots.sort(key=lambda row: (float(row["start"]), float(row["end"])))
    normalized = []
    cursor = 0.0
    for shot in shots:
        start = max(cursor, float(shot["start"]))
        end = min(duration, max(start, float(shot["end"])))
        if end - start < 1e-6:
            continue
        row = dict(shot)
        row["start"] = round(start, 6)
        row["end"] = round(end, 6)
        row["durationSeconds"] = round(end - start, 6)
        normalized.append(row)
        cursor = end
    if cursor < duration - 1e-6:
        _append(
            normalized,
            start=cursor,
            end=duration,
            shot_type="RETURN",
            reason="coverage repair",
            gate=_find_gate(timing, cursor),
        )

    normalized = _split_long_shots(
        normalized, max_shot_seconds=max_shot_seconds
    )
    normalized = _repair_repetition(normalized, performance)

    # Re-assign stable ids after all grammar repair.
    for index, row in enumerate(normalized, start=1):
        row["id"] = f"shot-{index:04d}"

    coverage = sum(float(row["durationSeconds"]) for row in normalized)
    counts = {}
    for row in normalized:
        counts[row["type"]] = counts.get(row["type"], 0) + 1

    body = {
        "schema": PLAN_SCHEMA,
        "timingId": timing["id"],
        "performanceId": (performance or {}).get("id"),
        "doctorReportId": (doctor_report or {}).get("id"),
        "durationSeconds": duration,
        "shotCount": len(normalized),
        "shots": normalized,
        "shotTypeCounts": counts,
        "coverageSeconds": round(coverage, 6),
        "coverageRatio": round(min(1.0, coverage / duration), 6),
        "grammar": {
            "maxShotSeconds": float(max_shot_seconds),
            "minShotSeconds": float(min_shot_seconds),
            "adjacentRepeatAllowed": False,
        },
        "cost": {"externalGenerations": 0, "providerCredits": 0, "usdMicros": 0},
        "laws": [
            "SHOT PLAN != NEW PERFORMANCE",
            "FRAMING != SOURCE AUTHORITY",
            "REACTION MAY REUSE EXISTING PERFORMANCE",
            "INSERT SHOT MUST BIND EXISTING MOVING SURFACE",
            "DIRECTING MAY CHANGE VIEW WITHOUT CHANGING WORLD",
            "FULL SONG COVERAGE MAY NOT DECREASE",
        ],
    }
    return {**body, "id": "paper-director-plan:" + _sha(body)[:24]}


def _crop_for_shot(
    shot: dict,
    *,
    width: int,
    height: int,
    performance: dict | None,
    index: int,
) -> dict:
    shot_type = shot["type"]

    if shot_type in {"ESTABLISH", "WIDE", "RETURN"}:
        return {"x": 0, "y": 0, "w": width, "h": height, "hflip": False}

    if shot_type == "SPEAKER":
        w = max(64, round(width * 0.72))
        h = max(64, round(height * 0.80))
        x = round((width - w) * 0.52)
        y = round((height - h) * 0.20)
        return {"x": x, "y": y, "w": w, "h": h, "hflip": False}

    if shot_type == "CLOSE_UP":
        w = max(64, round(width * 0.50))
        h = max(64, round(height * 0.60))
        x = round((width - w) * 0.52)
        y = round((height - h) * 0.07)
        return {"x": x, "y": y, "w": w, "h": h, "hflip": False}

    if shot_type == "REACTION":
        w = max(64, round(width * 0.58))
        h = max(64, round(height * 0.70))
        side = -1 if index % 2 else 1
        x_center = width * (0.50 + side * 0.08)
        x = round(max(0, min(width - w, x_center - w / 2)))
        y = round((height - h) * 0.12)
        return {"x": x, "y": y, "w": w, "h": h, "hflip": index % 3 == 0}

    if shot_type == "LYRIC_WORLD":
        w = width
        h = max(64, round(height * 0.68))
        return {
            "x": 0,
            "y": max(0, height - h),
            "w": w,
            "h": h,
            "hflip": False,
        }

    if shot_type == "INSERT":
        insert_id = shot.get("insertId")
        if performance and insert_id:
            for row in (performance.get("movingInsertPlan") or {}).get("inserts") or []:
                if row.get("id") == insert_id:
                    box = row["box"]
                    pad = max(4, int(box.get("border", 4)) * 3)
                    x = max(0, int(box["x"]) - pad)
                    y = max(0, int(box["y"]) - pad)
                    w = min(width - x, int(box["width"]) + pad * 2)
                    h = min(height - y, int(box["height"]) + pad * 2)
                    return {"x": x, "y": y, "w": max(16, w), "h": max(16, h), "hflip": False}
        # No admitted insert surface at this exact shot: degrade to prop-ish punch.
        w = max(64, round(width * 0.44))
        h = max(64, round(height * 0.52))
        return {
            "x": max(0, width - w - round(width * 0.05)),
            "y": round(height * 0.18),
            "w": w,
            "h": h,
            "hflip": False,
        }

    # CHAOS: deterministic corner punch with occasional flip.
    w = max(64, round(width * 0.62))
    h = max(64, round(height * 0.66))
    corners = (
        (0, 0),
        (width - w, 0),
        (0, height - h),
        (width - w, height - h),
    )
    x, y = corners[index % len(corners)]
    return {"x": x, "y": y, "w": w, "h": h, "hflip": index % 2 == 1}


def _shot_filter(crop: dict, *, width: int, height: int) -> str:
    filters = [
        f"crop={int(crop['w'])}:{int(crop['h'])}:{int(crop['x'])}:{int(crop['y'])}",
        f"scale={width}:{height}:flags=lanczos",
        "setsar=1",
    ]
    if crop.get("hflip"):
        filters.append("hflip")
    return ",".join(filters)


def render(
    base_video: str | Path,
    plan: dict,
    output_path: str | Path,
    *,
    performance: dict | None = None,
) -> dict:
    if plan.get("schema") != PLAN_SCHEMA:
        raise ValueError("Expected Paper Director plan")
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise RuntimeError("FFmpeg and FFprobe are required")

    base = Path(base_video).expanduser().resolve(strict=True)
    output = Path(output_path).expanduser().resolve()
    if output.exists():
        raise FileExistsError("Paper Director never overwrites")
    output.parent.mkdir(parents=True, exist_ok=True)

    probe = _probe(base)
    duration = float(plan["durationSeconds"])
    if probe["durationSeconds"] + 0.06 < duration:
        raise ValueError("Base movie does not cover director plan duration")

    width = int(probe["width"])
    height = int(probe["height"])
    if width < 64 or height < 64:
        raise ValueError("Base movie geometry is invalid")

    with tempfile.TemporaryDirectory(prefix="paper-director-") as td:
        temp = Path(td)
        segments = []
        receipt_shots = []

        for index, shot in enumerate(plan.get("shots") or []):
            start = float(shot["start"])
            end = float(shot["end"])
            span = end - start
            if span <= 0:
                raise ValueError("Director shot duration must be positive")
            crop = _crop_for_shot(
                shot,
                width=width,
                height=height,
                performance=performance,
                index=index,
            )
            seg = temp / f"shot-{index + 1:04d}.mp4"
            subprocess.run(
                [
                    "ffmpeg", "-nostdin", "-v", "error", "-y",
                    "-ss", f"{start:.6f}", "-i", str(base),
                    "-t", f"{span:.6f}",
                    "-vf", _shot_filter(crop, width=width, height=height),
                    "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart",
                    str(seg),
                ],
                check=True,
            )
            segments.append(seg)
            receipt_shots.append({
                "id": shot["id"],
                "type": shot["type"],
                "start": shot["start"],
                "end": shot["end"],
                "crop": crop,
                "segmentSha256": _file_sha(seg),
                "insertId": shot.get("insertId"),
                "weakWindowId": shot.get("weakWindowId"),
            })

        concat = temp / "shots.txt"
        concat.write_text(
            "".join(f"file '{seg.as_posix()}'\n" for seg in segments),
            encoding="utf-8",
        )
        video_only = temp / "directed-video.mp4"
        subprocess.run(
            [
                "ffmpeg", "-nostdin", "-v", "error", "-y",
                "-f", "concat", "-safe", "0", "-i", str(concat),
                "-t", f"{duration:.6f}",
                "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                str(video_only),
            ],
            check=True,
        )

        if probe["hasAudio"]:
            subprocess.run(
                [
                    "ffmpeg", "-nostdin", "-v", "error", "-y",
                    "-i", str(video_only), "-i", str(base),
                    "-map", "0:v:0", "-map", "1:a:0",
                    "-t", f"{duration:.6f}",
                    "-c:v", "copy", "-c:a", "aac",
                    "-movflags", "+faststart",
                    str(output),
                ],
                check=True,
            )
        else:
            shutil.copy2(video_only, output)

    observed = _probe(output)
    if observed["durationSeconds"] + 0.06 < duration:
        output.unlink(missing_ok=True)
        raise ValueError("Paper Director lost song coverage")

    receipt = {
        "schema": RECEIPT_SCHEMA,
        "status": "scoped_complete",
        "adapter": "ffmpeg-paper-director/v1",
        "planId": plan["id"],
        "baseSha256": _file_sha(base),
        "outputSha256": _file_sha(output),
        "durationSeconds": observed["durationSeconds"],
        "coverageRatio": round(min(1.0, observed["durationSeconds"] / duration), 6),
        "shotCount": len(receipt_shots),
        "shots": receipt_shots,
        "audioAuthority": "base-performance-only",
        "externalGenerations": 0,
        "providerCredits": 0,
        "usdMicros": 0,
        "laws": [
            "DIRECTOR CHANGES VIEW, NOT PERFORMANCE AUTHORITY",
            "BASE PERFORMANCE RETAINS AUDIO AUTHORITY",
            "SHOT SEGMENT != NEW SOURCE",
            "FULL SONG COVERAGE PRESERVED",
        ],
    }
    receipt_path = output.with_suffix(output.suffix + ".paper-director.json")
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt
