"""The finite image does not grant two memories unlimited visual authority."""
import unittest
import json
import shutil
from pathlib import Path

from haunted_blender import catalog, memory_competition, memory_feedback, memory_strength
from haunted_blender import observer_local

WORLD = {
    "id": "world-two-memories",
    "beats": [{"id": "beat-0", "index": 0}],
    "facts": [{"id": "fact-A", "since_beat": 0},
              {"id": "fact-B", "since_beat": 0}],
}
EYE = {
    "id": "eye-threshold",
    "position": "threshold",
    "access_fact_ids": [],
    "focus_fact_ids": ["fact-A", "fact-B"],
    "threshold_rules": [
        {"threshold_id": "door-A", "fact_id": "fact-A", "min_open": 0.5},
        {"threshold_id": "door-B", "fact_id": "fact-B", "min_open": 0.5},
    ],
}
REGIONS = {
    "fact-A": [0.2, 0.2, 0.5, 0.6],
    "fact-B": [0.3, 0.3, 0.6, 0.7],
}


def fixture():
    a = observer_local.project(WORLD, 0, EYE, {"door-A": 1.0, "door-B": 0.0})
    b = observer_local.project(WORLD, 0, EYE, {"door-A": 0.0, "door-B": 1.0},
                               a["memory_receipt"])
    both = observer_local.project(WORLD, 0, EYE, {"door-A": 0.0, "door-B": 0.0},
                                  b["memory_receipt"])
    timeline = [
        {"start_frame": 0, "end_frame_exclusive": 2, "projection": a},
        {"start_frame": 2, "end_frame_exclusive": 4, "projection": b},
        {"start_frame": 4, "end_frame_exclusive": 6, "projection": both},
    ]
    compiled = memory_feedback._compile_timeline(6, timeline, REGIONS)
    size = memory_feedback.WIDTH * memory_feedback.HEIGHT * 3
    first = bytes((120, 40, 10)) * (size // 3)
    second = bytes((30, 180, 90)) * (size // 3)
    black = bytes(size)
    return compiled, first + first + second + second + black + black


class CompetitionTests(unittest.TestCase):
    def test_largest_remainder_is_order_independent_and_bounded(self):
        a = memory_competition._allocate({"fact-B": 80, "fact-A": 80})
        b = memory_competition._allocate({"fact-A": 80, "fact-B": 80})
        self.assertEqual(a, b)
        self.assertEqual(sum(a.values()), memory_competition.PIXEL_BUDGET_PERCENT)
        self.assertEqual(a, {"fact-A": 36, "fact-B": 36})

    def test_two_seen_memories_compete_without_changing_current_frame(self):
        compiled, frames = fixture()
        schedule = memory_strength.build(compiled, 6)
        output, stats, receipt = memory_competition._memory_frames(
            frames, compiled, schedule)
        size = memory_feedback.WIDTH * memory_feedback.HEIGHT * 3
        self.assertEqual(output[:size], frames[:size])
        self.assertEqual(stats["fact-A"]["captured_frames"], 2)
        self.assertEqual(stats["fact-B"]["captured_frames"], 2)
        self.assertGreater(receipt["overlap_pixel_count"], 0)
        self.assertLessEqual(
            max(x["peak_used_percent"] for x in receipt["per_frame_allocations"]),
            memory_competition.PIXEL_BUDGET_PERCENT)
        self.assertNotEqual(output[4 * size:5 * size], frames[4 * size:5 * size])
        self.assertEqual(receipt["strength_schedule_sha256"],
                         schedule["schedule_sha256"])

    def test_region_order_cannot_choose_winner(self):
        compiled, frames = fixture()
        reversed_regions = dict(reversed(list(REGIONS.items())))
        timeline = [
            {"start_frame": s["start_frame"],
             "end_frame_exclusive": s["end_frame_exclusive"],
             "projection": s["projection"]}
            for s in compiled["segments"]
        ]
        other = memory_feedback._compile_timeline(6, timeline, reversed_regions)
        left = memory_competition._memory_frames(frames, compiled)[0]
        right = memory_competition._memory_frames(frames, other)[0]
        self.assertEqual(left, right)

    def test_no_pixels_from_receipt_without_prior_sight(self):
        compiled, frames = fixture()
        only_residue = memory_feedback._compile_timeline(
            2, [{"start_frame": 0, "end_frame_exclusive": 2,
                 "projection": compiled["segments"][2]["projection"]}], REGIONS)
        with self.assertRaisesRegex(ValueError, "no on-timeline visual capture"):
            memory_competition._memory_frames(
                frames[:2 * memory_feedback.WIDTH * memory_feedback.HEIGHT * 3],
                only_residue)

    def test_nonoverlapping_regions_are_refused(self):
        compiled, frames = fixture()
        bad = dict(REGIONS)
        bad["fact-B"] = [0.7, 0.7, 0.9, 0.9]
        timeline = [
            {"start_frame": s["start_frame"],
             "end_frame_exclusive": s["end_frame_exclusive"],
             "projection": s["projection"]}
            for s in compiled["segments"]
        ]
        other = memory_feedback._compile_timeline(6, timeline, bad)
        with self.assertRaisesRegex(ValueError, "overlapping authored regions"):
            memory_competition._memory_frames(frames, other)




@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
class AcceptedCompetitionVideoTests(unittest.TestCase):
    def setUp(self):
        from test_memory_feedback import AcceptedMemoryFeedbackTests
        AcceptedMemoryFeedbackTests.setUp(self)
        self.out = self.root / "renders" / "memory-competition" / "two-memories.mp4"

    def test_real_video_receipt_and_accepted_source_remain_separate(self):
        a = observer_local.project(WORLD, 0, EYE, {"door-A": 1.0, "door-B": 0.0})
        b = observer_local.project(WORLD, 0, EYE, {"door-A": 0.0, "door-B": 1.0},
                                   a["memory_receipt"])
        both = observer_local.project(WORLD, 0, EYE, {"door-A": 0.0, "door-B": 0.0},
                                      b["memory_receipt"])
        timeline = [
            {"start_frame": 0, "end_frame_exclusive": 4, "projection": a},
            {"start_frame": 4, "end_frame_exclusive": 8, "projection": b},
            {"start_frame": 8, "end_frame_exclusive": 12, "projection": both},
        ]
        result = memory_feedback.render(
            self.root, self.artifact["snapshot"], self.acceptance["acceptance"],
            timeline, REGIONS, self.out, competition=True)
        receipt = json.loads(Path(result["receipt"]).read_text())
        competition = receipt["memory_competition"]
        self.assertEqual(receipt["schema"], memory_competition.SCHEMA)
        self.assertEqual(receipt["output_sha256"], catalog.digest_file(self.out))
        self.assertEqual(receipt["source_video_sha256"], self.source_sha)
        self.assertEqual(competition["memory_fact_ids"], ["fact-A", "fact-B"])
        self.assertGreater(competition["overlap_pixel_count"], 0)
        self.assertFalse(receipt["distribution_authorized"])
        self.assertEqual(catalog.digest_file(self.source), self.source_sha)
        with self.assertRaisesRegex(ValueError, "overwrite"):
            memory_feedback.render(
                self.root, self.artifact["snapshot"], self.acceptance["acceptance"],
                timeline, REGIONS, self.out, competition=True)

if __name__ == "__main__":
    unittest.main()
