import copy
import unittest

from haunted_blender import observer_local


WORLD = {
    "id": "world-observer-test",
    "beats": [{"id": "beat-0", "index": 0}, {"id": "beat-1", "index": 1}],
    "facts": [
        {"id": "fact-room", "since_beat": 0},
        {"id": "fact-light", "since_beat": 0},
        {"id": "fact-figure", "since_beat": 0},
        {"id": "fact-name", "since_beat": 1},
    ],
}


def eye(name, position, access, focus, figure_min):
    return {
        "id": name,
        "position": position,
        "access_fact_ids": access,
        "focus_fact_ids": focus,
        "threshold_rules": [
            {"threshold_id": "door-main", "fact_id": "fact-figure",
             "min_open": figure_min}
        ],
    }


OUTSIDE = eye("eye-outside", "hallway", ["fact-room"], ["fact-figure"], 0.80)
THRESHOLD = eye("eye-threshold", "threshold", ["fact-room", "fact-light"],
                ["fact-figure"], 0.40)
INSIDE = eye("eye-inside", "room", ["fact-room", "fact-light", "fact-figure"],
             ["fact-figure"], 0.0)


class ObserverLocalTests(unittest.TestCase):
    def test_threshold_changes_visibility_not_world(self):
        original = copy.deepcopy(WORLD)
        closed = observer_local.project(WORLD, 0, THRESHOLD, {"door-main": 0.10})
        opened = observer_local.project(WORLD, 0, THRESHOLD, {"door-main": 0.45})
        self.assertEqual(WORLD, original)
        self.assertEqual(closed["visible_fact_ids"], ["fact-light", "fact-room"])
        self.assertEqual(closed["withheld_fact_ids"], ["fact-figure"])
        self.assertIn("fact-figure", opened["visible_fact_ids"])
        self.assertEqual(opened["focus_visible_fact_ids"], ["fact-figure"])

    def test_receipt_carries_memory_when_door_closes_again(self):
        first = observer_local.project(WORLD, 0, THRESHOLD, {"door-main": 0.60})
        second = observer_local.project(
            WORLD, 0, THRESHOLD, {"door-main": 0.10}, first["memory_receipt"])
        self.assertNotIn("fact-figure", second["visible_fact_ids"])
        self.assertIn("fact-figure", second["memory_receipt"]["memory_fact_ids"])
        self.assertEqual(second["memory_receipt"]["residual_memory_fact_ids"],
                         ["fact-figure"])
        self.assertIn({"fact_id": "fact-figure", "mode": "memory_residue"},
                      second["environment_response"])

    def test_camera_is_an_observer_not_a_truth_rewriter(self):
        outside = observer_local.project(WORLD, 0, OUTSIDE, {"door-main": 0.45})
        threshold = observer_local.project(WORLD, 0, THRESHOLD, {"door-main": 0.45})
        inside = observer_local.project(WORLD, 0, INSIDE, {"door-main": 0.45})
        self.assertNotIn("fact-figure", outside["visible_fact_ids"])
        self.assertIn("fact-figure", threshold["visible_fact_ids"])
        self.assertIn("fact-figure", inside["visible_fact_ids"])
        self.assertEqual(outside["world_sha256"], threshold["world_sha256"])
        self.assertEqual(threshold["world_sha256"], inside["world_sha256"])

    def test_three_by_three_door_test_is_nine_independent_cells(self):
        matrix = observer_local.door_matrix(
            WORLD, 0, [OUTSIDE, THRESHOLD, INSIDE], "door-main", [0.10, 0.45, 0.80])
        self.assertEqual(len(matrix["rows"]), 9)
        keyed = {(r["observer_id"], r["openness"]): r for r in matrix["rows"]}
        self.assertNotIn("fact-figure", keyed[("eye-outside", 0.45)]["visible_fact_ids"])
        self.assertIn("fact-figure", keyed[("eye-outside", 0.80)]["visible_fact_ids"])
        self.assertNotIn("fact-figure", keyed[("eye-threshold", 0.10)]["visible_fact_ids"])
        self.assertIn("fact-figure", keyed[("eye-threshold", 0.45)]["visible_fact_ids"])
        self.assertIn("fact-figure", keyed[("eye-inside", 0.10)]["visible_fact_ids"])

    def test_memory_receipt_rejects_wrong_observer_world_and_future(self):
        first = observer_local.project(WORLD, 0, THRESHOLD, {"door-main": 0.60})
        receipt = first["memory_receipt"]
        with self.assertRaisesRegex(ValueError, "another observer"):
            observer_local.project(WORLD, 0, OUTSIDE, {"door-main": 0.90}, receipt)
        other = copy.deepcopy(WORLD)
        other["facts"][0]["extra"] = "changed"
        with self.assertRaisesRegex(ValueError, "another world"):
            observer_local.project(other, 0, THRESHOLD, {"door-main": 0.60}, receipt)
        future = dict(receipt)
        future["beat"] = 1
        with self.assertRaisesRegex(ValueError, "future"):
            observer_local.project(WORLD, 0, THRESHOLD, {"door-main": 0.60}, future)


if __name__ == "__main__":
    unittest.main()
