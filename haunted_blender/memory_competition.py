"""Bounded competition between two legitimate observer-local visual memories.

Pixels are captured separately, exclusively while each fact is present_to_eye.
Every output pixel has one shared, finite afterimage-opacity budget. Memories
may compete for that budget but cannot change world facts or present visibility.
"""
from __future__ import annotations

from . import memory_feedback, memory_strength

SCHEMA = "haunted-blender/memory-competition-receipt/v0"
ADAPTER = "observer-local-memory-competition/v0"
PIXEL_BUDGET_PERCENT = 72
MAX_RESIDUES = 2


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _validate(compiled):
    regions = compiled["regions"]
    _require(len(regions) == MAX_RESIDUES,
             "Competition 001 requires exactly two authored memory regions")
    left, right = (region["pixels"] for region in regions.values())
    _require(max(left[0], right[0]) < min(left[2], right[2])
             and max(left[1], right[1]) < min(left[3], right[3]),
             "Competition requires overlapping authored regions")
    # Stable order is essential: JSON object order cannot choose a winner.
    return sorted(regions)


def _allocate(weights, budget=PIXEL_BUDGET_PERCENT):
    """Order-independent largest-remainder allocation over at most two facts."""
    _require(weights and all(type(w) is int and 0 <= w <= 100
                             for w in weights.values()),
             "Memory weights must be integer percentages")
    total = sum(weights.values())
    _require(type(budget) is int and 0 <= budget <= 100,
             "Invalid finite opacity budget")
    if total <= budget:
        return dict(weights)
    ordered = sorted(weights)
    granted = {key: budget * weights[key] // total for key in ordered}
    remaining = budget - sum(granted.values())
    remainders = sorted(ordered,
                        key=lambda key: (-(budget * weights[key] % total), key))
    for key in remainders[:remaining]:
        granted[key] += 1
    return granted


def _memory_frames(frames, compiled, strength_schedule=None):
    width, height = memory_feedback.WIDTH, memory_feedback.HEIGHT
    frame_bytes = width * height * 3
    _require(len(frames) > 0 and len(frames) % frame_bytes == 0,
             "Invalid source frame buffer")
    count = len(frames) // frame_bytes
    _require(compiled["segments"][-1]["end_frame_exclusive"] == count,
             "Timeline and decoded frames disagree")
    ids = _validate(compiled)
    schedule = strength_schedule or memory_strength.build(compiled, count)
    memory_strength.validate(schedule)
    _require(schedule["observer_id"] == compiled["observer_id"]
             and schedule["world_sha256"] == compiled["world_sha256"]
             and schedule["frame_count"] == count,
             "Strength schedule belongs to another observer, world or sample set")

    output = bytearray(len(frames))
    memories = {}
    statistics = {
        fid: {"captured_frames": 0, "residue_frames": 0,
              "last_seen_frame": None, "peak_granted_percent": 0}
        for fid in ids
    }
    allocation = []
    total_overlap_pixels = 0
    segment_index = 0
    for index in range(count):
        while index >= compiled["segments"][segment_index]["end_frame_exclusive"]:
            segment_index += 1
        segment = compiled["segments"][segment_index]
        source = memoryview(frames)[index * frame_bytes:(index + 1) * frame_bytes]
        frame = memoryview(output)[index * frame_bytes:(index + 1) * frame_bytes]
        frame[:] = source
        signals = schedule["frames"][index]["strengths"]
        candidates = {}
        for fid in ids:
            box = compiled["regions"][fid]["pixels"]
            modes = segment["modes"].get(fid, set())
            if "present_to_eye" in modes:
                memories[fid] = {
                    "pixels": memory_feedback._capture(source, box),
                    "seen": index,
                }
                statistics[fid]["captured_frames"] += 1
                statistics[fid]["last_seen_frame"] = index
            if "memory_residue" not in modes:
                continue
            _require(fid in memories,
                     "Memory residue has no on-timeline visual capture")
            _require(fid in signals and type(signals[fid].get("strength_percent")) is int,
                     "Memory residue lacks an inspectable strength")
            strength = signals[fid]["strength_percent"]
            _require(0 <= strength <= 100, "Strength outside opacity range")
            statistics[fid]["residue_frames"] += 1
            if strength == 0:
                continue
            x0, y0, x1, y1 = box
            shift = min(memory_feedback.MAX_SHIFT_X,
                        (index - memories[fid]["seen"]) * memory_feedback.SHIFT_X_PER_FRAME)
            remembered = memories[fid]["pixels"]
            cursor = 0
            for y in range(y0, y1):
                for x in range(x0, x1):
                    target_x = x + shift
                    source_offset = cursor * 3
                    cursor += 1
                    if target_x >= width:
                        continue
                    target = y * width + target_x
                    mr, mg, mb = remembered[source_offset:source_offset + 3]
                    ghost = (mr * 3 // 5, mg * 4 // 5,
                             min(255, mb + mb // 4 + 8))
                    candidates.setdefault(target, []).append(
                        (fid, strength, ghost))

        frame_overlap = 0
        peak_used = 0
        granted_totals = {fid: 0 for fid in ids}
        for pixel_index, contributors in candidates.items():
            weights = {fid: strength for fid, strength, _ in contributors}
            granted = _allocate(weights)
            used = sum(granted.values())
            _require(used <= PIXEL_BUDGET_PERCENT, "Memory opacity budget exceeded")
            if len(contributors) == 2:
                frame_overlap += 1
            peak_used = max(peak_used, used)
            for fid, percent in granted.items():
                granted_totals[fid] += percent
                statistics[fid]["peak_granted_percent"] = max(
                    statistics[fid]["peak_granted_percent"], percent)
            offset = pixel_index * 3
            for channel in range(3):
                value = source[offset + channel] * (100 - used)
                for fid, _, ghost in contributors:
                    value += granted[fid] * ghost[channel]
                frame[offset + channel] = value // 100
        total_overlap_pixels += frame_overlap
        allocation.append({
            "frame": index, "overlap_pixels": frame_overlap,
            "peak_used_percent": peak_used,
            "granted_percent_pixel_sum": granted_totals,
        })

    _require(total_overlap_pixels > 0,
             "No overlapping on-timeline memory residues were produced")
    receipt = {
        "schema": SCHEMA, "adapter": ADAPTER,
        "observer_id": compiled["observer_id"],
        "world_sha256": compiled["world_sha256"],
        "memory_fact_ids": ids,
        "strength_schedule_sha256": schedule["schedule_sha256"],
        "pixel_budget_percent": PIXEL_BUDGET_PERCENT,
        "allocation_rule": "largest remainder by fact id; composited against original source",
        "overlap_pixel_count": total_overlap_pixels,
        "per_frame_allocations": allocation,
        "nonclaims": [
            "Opacity allocation is cinematic presentation, not a truth or memory ranking",
            "Only pixels captured while each fact was present_to_eye can recur",
            "An afterimage does not establish current presence or human recollection",
            "No source video, world fact, or accepted scene is changed",
        ],
    }
    return bytes(output), statistics, receipt
