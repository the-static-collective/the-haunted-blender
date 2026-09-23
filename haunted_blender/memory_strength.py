"""Deterministic encounter-history weighting for observer-local visual memory.

The schedule uses only information available up to each frame. It never promotes
memory into occurrence and never invents pixels; it only determines how strongly
an already-valid visual memory residue may affect presentation.
"""
from __future__ import annotations

import hashlib

from . import project

SCHEMA = "haunted-blender/memory-strength-schedule/v0"
DWELL_HORIZON_FRAMES = 12
EXPOSURE_HORIZON = 3
DWELL_WEIGHT = 0.50
FOCUS_WEIGHT = 0.30
REPETITION_WEIGHT = 0.20
MIN_START_PERCENT = 40
START_RANGE_PERCENT = 40
MIN_RETENTION_PERCENT = 82
RETENTION_RANGE_PERCENT = 14


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _digest(value):
    return hashlib.sha256(project.stable_bytes(value)).hexdigest()


def _strength(history, age):
    dwell = min(1.0, history["visible_frames"] / DWELL_HORIZON_FRAMES)
    focus = (history["focused_visible_frames"] / history["visible_frames"]
             if history["visible_frames"] else 0.0)
    repetition = min(1.0, history["exposures"] / EXPOSURE_HORIZON)
    encounter = (
        dwell * DWELL_WEIGHT
        + focus * FOCUS_WEIGHT
        + repetition * REPETITION_WEIGHT
    )
    start = round(MIN_START_PERCENT + START_RANGE_PERCENT * encounter)
    retention = round(
        MIN_RETENTION_PERCENT + RETENTION_RANGE_PERCENT * encounter)
    strength = start
    for _ in range(max(0, age - 1)):
        strength = strength * retention // 100
    return {
        "strength_percent": strength,
        "encounter_score": round(encounter, 6),
        "start_percent": start,
        "retention_percent": retention,
        "age_frames": age,
        "dwell_score": round(dwell, 6),
        "focus_ratio": round(focus, 6),
        "repetition_score": round(repetition, 6),
    }


def build(compiled, frame_count):
    """Build a no-future-leak strength schedule from a compiled observer timeline."""
    _require(isinstance(compiled, dict) and compiled.get("segments"),
             "Compiled observer timeline required")
    _require(type(frame_count) is int and frame_count > 0,
             "Positive frame count required")
    _require(compiled["segments"][-1]["end_frame_exclusive"] == frame_count,
             "Strength schedule frame count mismatch")

    fact_ids = sorted(compiled.get("regions", {}))
    histories = {
        fid: {
            "visible_frames": 0,
            "focused_visible_frames": 0,
            "exposures": 0,
            "last_seen_frame": None,
            "was_present": False,
        }
        for fid in fact_ids
    }
    summaries = {
        fid: {
            "visible_frames": 0,
            "focused_visible_frames": 0,
            "exposures": 0,
            "residue_frames": 0,
            "first_residue_strength_percent": None,
            "peak_residue_strength_percent": 0,
            "last_residue_strength_percent": 0,
        }
        for fid in fact_ids
    }
    frames = []
    segment_index = 0

    for index in range(frame_count):
        while index >= compiled["segments"][segment_index]["end_frame_exclusive"]:
            segment_index += 1
        segment = compiled["segments"][segment_index]
        focused = set(segment["projection"].get("focus_visible_fact_ids", []))
        strengths = {}

        for fact_id in fact_ids:
            history = histories[fact_id]
            modes = segment["modes"].get(fact_id, set())
            present = "present_to_eye" in modes
            residue = "memory_residue" in modes

            if present:
                if not history["was_present"]:
                    history["exposures"] += 1
                history["visible_frames"] += 1
                if fact_id in focused:
                    history["focused_visible_frames"] += 1
                history["last_seen_frame"] = index
                history["was_present"] = True
            elif residue:
                _require(history["last_seen_frame"] is not None,
                         "Memory residue has no on-timeline visual capture")
                history["was_present"] = False
                age = index - history["last_seen_frame"]
                derived = _strength(history, age)
                strengths[fact_id] = derived
                summary = summaries[fact_id]
                summary["residue_frames"] += 1
                if summary["first_residue_strength_percent"] is None:
                    summary["first_residue_strength_percent"] = derived["strength_percent"]
                summary["peak_residue_strength_percent"] = max(
                    summary["peak_residue_strength_percent"],
                    derived["strength_percent"])
                summary["last_residue_strength_percent"] = derived["strength_percent"]
            else:
                history["was_present"] = False

        frames.append({"frame": index, "strengths": strengths})

    for fact_id, history in histories.items():
        summaries[fact_id]["visible_frames"] = history["visible_frames"]
        summaries[fact_id]["focused_visible_frames"] = history["focused_visible_frames"]
        summaries[fact_id]["exposures"] = history["exposures"]

    result = {
        "schema": SCHEMA,
        "observer_id": compiled["observer_id"],
        "world_sha256": compiled["world_sha256"],
        "frame_count": frame_count,
        "formula": {
            "dwell_horizon_frames": DWELL_HORIZON_FRAMES,
            "exposure_horizon": EXPOSURE_HORIZON,
            "weights": {
                "dwell": DWELL_WEIGHT,
                "focus": FOCUS_WEIGHT,
                "repetition": REPETITION_WEIGHT,
            },
            "start_percent": {
                "minimum": MIN_START_PERCENT,
                "range": START_RANGE_PERCENT,
            },
            "retention_percent": {
                "minimum": MIN_RETENTION_PERCENT,
                "range": RETENTION_RANGE_PERCENT,
            },
            "recency": "integer per-frame retention applied after last visible frame",
            "future_information_used": False,
        },
        "frames": frames,
        "facts": summaries,
        "nonclaims": [
            "Memory strength is a deterministic cinematic weight, not psychological measurement",
            "Focus is authored camera attention, not inferred human attention",
            "Longer visual persistence does not establish truth, importance or current presence",
        ],
    }
    result["schedule_sha256"] = _digest(result)
    return result


def validate(schedule):
    _require(isinstance(schedule, dict) and schedule.get("schema") == SCHEMA,
             "Unknown memory strength schedule")
    claimed = schedule.get("schedule_sha256")
    unsigned = dict(schedule)
    unsigned.pop("schedule_sha256", None)
    _require(isinstance(claimed, str) and _digest(unsigned) == claimed,
             "Memory strength schedule digest mismatch")
    return schedule
