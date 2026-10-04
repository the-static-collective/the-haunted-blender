"""Encounter history, not one global constant, weights visual memory."""
import unittest

from haunted_blender import memory_feedback, memory_strength, observer_local


WORLD = {
    "id": "world-memory-strength-test",
    "beats": [{"id": "beat-0", "index": 0}],
    "facts": [
        {"id": "fact-room", "since_beat": 0},
        {"id": "fact-figure", "since_beat": 0},
    ],
}
REGIONS = {"fact-figure": [0.2, 0.2, 0.5, 0.7]}


def eye(focused=True):
    return {
        "id": "eye-threshold",
        "position": "threshold",
        "access_fact_ids": ["fact-room"],
        "focus_fact_ids": ["fact-figure"] if focused else [],
        "threshold_rules": [
            {"threshold_id": "door-main", "fact_id": "fact-figure",
             "min_open": 0.4}
        ],
    }


def pair(focused=True):
    observer = eye(focused)
    visible = observer_local.project(
        WORLD, 0, observer, {"door-main": 0.7})
    residue = observer_local.project(
        WORLD, 0, observer, {"door-main": 0.1},
        visible["memory_receipt"])
    return visible, residue


def compile_pattern(visible_frames, residue_frames, focused=True):
    visible, residue = pair(focused)
    total = visible_frames + residue_frames
    timeline = [
        {"start_frame": 0, "end_frame_exclusive": visible_frames,
         "projection": visible},
        {"start_frame": visible_frames, "end_frame_exclusive": total,
         "projection": residue},
    ]
    return memory_feedback._compile_timeline(total, timeline, REGIONS)


class MemoryStrengthTests(unittest.TestCase):
    def test_longer_dwell_starts_stronger_and_decays_slower(self):
        short = memory_strength.build(compile_pattern(1, 4), 5)
        long = memory_strength.build(compile_pattern(8, 4), 12)
        short_first = short["facts"]["fact-figure"]["first_residue_strength_percent"]
        long_first = long["facts"]["fact-figure"]["first_residue_strength_percent"]
        short_last = short["facts"]["fact-figure"]["last_residue_strength_percent"]
        long_last = long["facts"]["fact-figure"]["last_residue_strength_percent"]
        self.assertGreater(long_first, short_first)
        self.assertGreater(long_last, short_last)

    def test_authored_focus_increases_weight_without_becoming_psychology(self):
        focused = memory_strength.build(compile_pattern(4, 2, True), 6)
        unfocused = memory_strength.build(compile_pattern(4, 2, False), 6)
        self.assertGreater(
            focused["facts"]["fact-figure"]["first_residue_strength_percent"],
            unfocused["facts"]["fact-figure"]["first_residue_strength_percent"])
        self.assertFalse(focused["formula"]["future_information_used"])

    def test_repeated_encounter_strengthens_later_residue(self):
        visible, residue = pair(True)
        timeline = [
            {"start_frame": 0, "end_frame_exclusive": 2, "projection": visible},
            {"start_frame": 2, "end_frame_exclusive": 3, "projection": residue},
            {"start_frame": 3, "end_frame_exclusive": 5, "projection": visible},
            {"start_frame": 5, "end_frame_exclusive": 6, "projection": residue},
        ]
        compiled = memory_feedback._compile_timeline(6, timeline, REGIONS)
        schedule = memory_strength.build(compiled, 6)
        first = schedule["frames"][2]["strengths"]["fact-figure"]["strength_percent"]
        second = schedule["frames"][5]["strengths"]["fact-figure"]["strength_percent"]
        self.assertGreater(second, first)
        self.assertEqual(schedule["facts"]["fact-figure"]["exposures"], 2)

    def test_schedule_is_content_addressed(self):
        schedule = memory_strength.build(compile_pattern(3, 2), 5)
        self.assertIs(memory_strength.validate(schedule), schedule)
        schedule["facts"]["fact-figure"]["visible_frames"] = 99
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            memory_strength.validate(schedule)


if __name__ == "__main__":
    unittest.main()
