"""FRANKEN BLENDER 005 — KEEP -> timed scene -> rare accepted awakening.

Timing may come from PlayDeck-style section gates and/or Full Measure lyric cues.
Neither timing source grants motion authority. A DREAMBREEDER KEEP authorizes
continuation into a longer deterministic scene. Accepted moving takes remain a
separate, reverified substitution.
"""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from .cutout_stage import render_cutout
from .dream_cutout_compiler import compile_proposal
from .dreambreeder import DESCENDANT_SCHEMA, ECOLOGY_SCHEMA
from . import catalog, video_resolver

TIMING_SCHEMA = "haunted-blender/track-timing/v1"
SCENE_SCHEMA = "haunted-blender/kept-scene/v1"
SCENE_RECEIPT_SCHEMA = "haunted-blender/kept-scene-receipt/v1"
AWAKENED_RECEIPT_SCHEMA = "haunted-blender/awakened-scene-receipt/v1"

_SECTION_GRAMMAR = {
    "intro": ["hold", "parallax"],
    "verse": ["hold", "wind", "parallax"],
    "pre-chorus": ["step", "drift-up", "wind"],
    "chorus": ["step", "raise-world", "reveal-sky", "backlight"],
    "bridge": ["freeze", "echo", "misregister"],
    "breakdown": ["separate", "misregister"],
    "outro": ["return", "open-late"],
}


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _hash(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _file_sha(path: Path) -> str:
    return catalog.digest_file(path)


def _unique(values):
    out = []
    seen = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def normalize_timing(track: dict, lyrics: dict | None = None) -> dict:
    if not isinstance(track, dict) or track.get("schemaVersion") != "0.1":
        raise ValueError("Expected PlayDeck TrackSpec 0.1-compatible timing input.")
    duration = float(track.get("duration", 0))
    if duration <= 0:
        raise ValueError("Track duration must be positive.")

    raw_gates = track.get("gates") or [{"id": "whole", "at": 0, "kind": "verse", "label": "whole track"}]
    gates = []
    for gate in raw_gates:
        at = float(gate.get("at", -1))
        if at < 0 or at >= duration:
            raise ValueError("Section gate falls outside track duration.")
        gates.append(
            {
                "id": str(gate.get("id") or f"gate-{len(gates):02d}"),
                "at": round(at, 6),
                "kind": str(gate.get("kind") or "section"),
                "label": str(gate.get("label") or gate.get("kind") or "section"),
            }
        )
    gates.sort(key=lambda g: (g["at"], g["id"]))
    if gates[0]["at"] != 0:
        gates.insert(0, {"id": "auto-start", "at": 0.0, "kind": "intro", "label": "arrival"})
    if any(a["at"] == b["at"] for a, b in zip(gates, gates[1:])):
        raise ValueError("Section gates must have unique times.")

    cues = []
    if lyrics is not None:
        if not isinstance(lyrics, dict) or lyrics.get("schema") != "full-measure.lyrics.v1":
            raise ValueError("Expected full-measure.lyrics.v1 cues.")
        for index, cue in enumerate(lyrics.get("cues") or []):
            start = float(cue.get("start", -1))
            end = float(cue.get("end", start))
            text = str(cue.get("text") or "").strip()
            if text and 0 <= start < duration:
                cues.append(
                    {
                        "index": index,
                        "start": round(start, 6),
                        "end": round(max(start, min(duration, end)), 6),
                        "text": text,
                    }
                )
        cues.sort(key=lambda c: (c["start"], c["index"]))

    sections = []
    for index, gate in enumerate(gates):
        end = gates[index + 1]["at"] if index + 1 < len(gates) else duration
        bound = [c for c in cues if gate["at"] <= c["start"] < end]
        sections.append(
            {
                **gate,
                "end": round(end, 6),
                "duration": round(end - gate["at"], 6),
                "lyricCueIndices": [c["index"] for c in bound],
            }
        )

    awakening_windows = []
    eligible = [s for s in sections if s["kind"] in {"chorus", "bridge"} and s["duration"] >= 0.75]
    for section in eligible[:3]:
        bound = [c for c in cues if c["index"] in section["lyricCueIndices"]]
        anchor = bound[0]["start"] if bound else section["at"] + section["duration"] * 0.35
        max_len = min(2.5, max(0.75, section["duration"] * 0.28))
        start = max(section["at"], anchor - 0.15)
        end = min(section["end"], start + max_len)
        if end - start < 0.5:
            continue
        awakening_windows.append(
            {
                "id": f"awaken-{section['id']}",
                "sectionId": section["id"],
                "kind": section["kind"],
                "start": round(start, 6),
                "end": round(end, 6),
                "duration": round(end - start, 6),
                "authorityClass": "proposal-only",
                "reason": "bounded section-gate aperture",
            }
        )

    body = {
        "schema": TIMING_SCHEMA,
        "trackId": str(track.get("id") or "track"),
        "duration": round(duration, 6),
        "sections": sections,
        "lyricsSchema": lyrics.get("schema") if lyrics else None,
        "lyricsCues": cues,
        "awakeningWindows": awakening_windows,
        "laws": [
            "TIMING != MOTION AUTHORITY",
            "LYRIC CUE != GENERATION COMMAND",
            "AWAKENING WINDOW != ACCEPTED TAKE",
        ],
    }
    return {**body, "id": f"track-timing:{_hash(body)[:24]}"}


def _validate_keep(keep_result: dict):
    if not isinstance(keep_result, dict):
        raise ValueError("KEEP result is required.")
    ecology = keep_result.get("ecology")
    descendant = keep_result.get("descendant")
    if not isinstance(ecology, dict) or ecology.get("schema") != ECOLOGY_SCHEMA:
        raise ValueError("KEEP result lacks a DREAMBREEDER ecology.")
    disposition = ecology.get("disposition") or {}
    if disposition.get("kind") != "KEEP":
        raise ValueError("Long scene growth requires an explicit KEEP.")
    if not isinstance(descendant, dict) or descendant.get("schema") != DESCENDANT_SCHEMA:
        raise ValueError("KEEP result lacks its descendant.")
    if descendant.get("id") != disposition.get("resultDescendantId"):
        raise ValueError("KEEP descendant identity mismatch.")
    if descendant.get("status") != "unrendered-descendant":
        raise ValueError("Scene growth requires an unrendered KEEP descendant.")
    proposal_id = disposition.get("proposalId")
    proposal = next((p for p in ecology["proposals"] if p["id"] == proposal_id), None)
    if proposal is None:
        raise ValueError("KEEP proposal no longer belongs to ecology.")
    return ecology, descendant, proposal


def _section_ecology(ecology: dict, proposal_id: str, extra_grammar: list[str]) -> dict:
    local = copy.deepcopy(ecology)
    local["disposition"] = None
    for proposal in local["proposals"]:
        if proposal["id"] == proposal_id:
            proposal["motionGrammar"] = _unique(list(proposal.get("motionGrammar") or []) + extra_grammar)
    return local


def grow_kept_scene(
    keep_result: dict,
    timing: dict,
    kit: dict,
    output_dir: str | Path,
    *,
    fps: int = 12,
    donor_freeze: str | Path | None = None,
) -> dict:
    ecology, descendant, proposal = _validate_keep(keep_result)
    if not isinstance(timing, dict) or timing.get("schema") != TIMING_SCHEMA:
        raise ValueError("Normalized track timing is required.")
    if fps < 1:
        raise ValueError("fps must be positive.")

    root = Path(output_dir).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    segments = []

    for index, section in enumerate(timing["sections"]):
        local_ecology = _section_ecology(
            ecology,
            proposal["id"],
            _SECTION_GRAMMAR.get(section["kind"], ["hold"]),
        )
        compiled = compile_proposal(
            local_ecology,
            proposal["id"],
            kit,
            duration=section["duration"],
            fps=fps,
            donor_freeze=donor_freeze,
        )
        segment_path = root / f"section-{index:02d}-{section['id']}.mp4"
        render_receipt = render_cutout(compiled["cutoutPlan"], segment_path)
        segments.append(
            {
                "sectionId": section["id"],
                "kind": section["kind"],
                "start": section["at"],
                "end": section["end"],
                "compiledPlanId": compiled["id"],
                "path": str(segment_path),
                "sha256": render_receipt["outputSha256"],
            }
        )

    output = root / "kept-scene.mp4"
    if output.exists():
        raise FileExistsError("Kept scene renderer never overwrites existing output.")
    playlist = root / "sections.txt"
    playlist.write_text(
        "".join(f"file '{Path(s['path']).name}'\n" for s in segments),
        encoding="utf-8",
    )
    subprocess.run(
        [
            "ffmpeg", "-v", "error", "-y",
            "-f", "concat", "-safe", "1",
            "-i", str(playlist),
            "-c", "copy", "-movflags", "+faststart", str(output),
        ],
        check=True,
    )

    scene = {
        "schema": SCENE_SCHEMA,
        "authorityClass": "continuation-permission",
        "descendantId": descendant["id"],
        "keptProposalId": proposal["id"],
        "timingId": timing["id"],
        "duration": timing["duration"],
        "segments": segments,
        "awakeningWindows": timing["awakeningWindows"],
        "status": "deterministic-kept-scene",
        "distributionAuthorized": False,
    }
    scene["id"] = f"kept-scene:{_hash(scene)[:24]}"

    receipt = {
        "schema": SCENE_RECEIPT_SCHEMA,
        "sceneId": scene["id"],
        "descendantId": descendant["id"],
        "timingId": timing["id"],
        "outputSha256": _file_sha(output),
        "outputByteLength": output.stat().st_size,
        "segmentSha256": [s["sha256"] for s in segments],
        "status": "scoped_complete",
        "sound": "omitted",
        "distributionAuthorized": False,
        "laws": [
            "KEEP AUTHORIZES CONTINUATION, NOT PUBLICATION",
            "DETERMINISTIC SCENE != RESOLVED PERFORMANCE",
            "AWAKENING WINDOW != MOVING TAKE",
        ],
    }
    scene_path = root / "scene.json"
    receipt_path = root / "scene.receipt.json"
    scene_path.write_text(json.dumps(scene, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "scene": scene,
        "receipt": receipt,
        "videoPath": str(output),
        "scenePath": str(scene_path),
        "receiptPath": str(receipt_path),
    }


def awaken_kept_scene(
    root: str | Path,
    grown_scene: dict,
    window_id: str,
    accepted_video_address: str,
    output_path: str | Path,
) -> dict:
    scene = grown_scene.get("scene")
    receipt = grown_scene.get("receipt")
    source_video = Path(grown_scene.get("videoPath", "")).expanduser().resolve()
    if not isinstance(scene, dict) or scene.get("schema") != SCENE_SCHEMA:
        raise ValueError("A grown kept scene is required.")
    if not isinstance(receipt, dict) or receipt.get("schema") != SCENE_RECEIPT_SCHEMA:
        raise ValueError("A kept-scene receipt is required.")
    if not source_video.is_file() or _file_sha(source_video) != receipt.get("outputSha256"):
        raise ValueError("Kept-scene video no longer matches its receipt.")

    window = next((w for w in scene.get("awakeningWindows", []) if w["id"] == window_id), None)
    if window is None:
        raise ValueError("Unknown awakening window.")

    descriptor, accepted_path = video_resolver.resolve_accepted_video_for_serve(root, accepted_video_address)
    duration = float(window["duration"])
    if float(descriptor["durationSeconds"]) < duration:
        raise ValueError("Accepted moving take is shorter than the awakening window.")

    out = Path(output_path).expanduser().resolve()
    if out.exists():
        raise FileExistsError("Awakened scene renderer never overwrites output.")
    out.parent.mkdir(parents=True, exist_ok=True)

    probe = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "json", str(source_video),
        ],
        check=True, capture_output=True, text=True,
    )
    stream = json.loads(probe.stdout)["streams"][0]
    width, height = int(stream["width"]), int(stream["height"])

    start, end = float(window["start"]), float(window["end"])
    with tempfile.TemporaryDirectory(prefix="blender-awaken-", dir=out.parent) as td:
        tmp = Path(td)
        parts = []
        if start > 0:
            before = tmp / "before.mp4"
            subprocess.run(
                ["ffmpeg", "-v", "error", "-y", "-i", str(source_video), "-t", f"{start:.6f}",
                 "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(before)],
                check=True,
            )
            parts.append(before)

        middle = tmp / "awaken.mp4"
        subprocess.run(
            [
                "ffmpeg", "-v", "error", "-y", "-i", str(accepted_path),
                "-t", f"{duration:.6f}",
                "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                       f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1",
                "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(middle),
            ],
            check=True,
        )
        parts.append(middle)

        if end < float(scene["duration"]):
            after = tmp / "after.mp4"
            subprocess.run(
                [
                    "ffmpeg", "-v", "error", "-y", "-ss", f"{end:.6f}", "-i", str(source_video),
                    "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(after),
                ],
                check=True,
            )
            parts.append(after)

        playlist = tmp / "playlist.txt"
        playlist.write_text("".join(f"file '{p.name}'\n" for p in parts), encoding="utf-8")
        subprocess.run(
            [
                "ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "1",
                "-i", str(playlist), "-c", "copy", "-movflags", "+faststart", str(out),
            ],
            check=True,
        )

    awakened_receipt = {
        "schema": AWAKENED_RECEIPT_SCHEMA,
        "status": "scoped_complete",
        "sourceSceneId": scene["id"],
        "sourceSceneSha256": receipt["outputSha256"],
        "awakeningWindowId": window_id,
        "acceptedVideoAddress": accepted_video_address,
        "acceptedVideoSha256": descriptor["sha256"],
        "acceptanceSha256": descriptor["acceptanceSha256"],
        "requestSha256": descriptor["requestSha256"],
        "outputSha256": _file_sha(out),
        "distributionAuthorized": False,
        "laws": [
            "WINDOW != ACCEPTANCE",
            "ACCEPTANCE != PUBLICATION",
            "ACCEPTED TAKE MAY REPLACE ONLY ITS BOUNDED WINDOW",
        ],
    }
    receipt_path = out.with_suffix(out.suffix + ".receipt.json")
    receipt_path.write_text(json.dumps(awakened_receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"output": str(out), "receipt": str(receipt_path), "descriptor": descriptor}
