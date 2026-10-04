"""An authored synthetic fiction: check camera and audience disclosure boundaries."""
import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from haunted_blender import scene_weave, visual_dream
from test_scene_weave import make_world


class VisualDreamTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.world = make_world()
        world_path = scene_weave._path(self.root, self.world["id"])
        world_path.parent.mkdir(parents=True)
        world_path.write_text(json.dumps(self.world), encoding="utf-8")
        self.snapshot = scene_weave.freeze(self.root, self.world["id"])
        self.score = {
            "schema": visual_dream.SCORE, "world_snapshot": str(self.snapshot),
            "world_sha256": scene_weave.sha(self.world), "beat": 0,
            "start": "door", "nodes": [
                {"id": "door", "fact_id": "sealed", "motif": "hinge"},
                {"id": "shadow", "fact_id": "sender", "motif": "hinge"},
                {"id": "return", "fact_id": "sealed", "motif": "hinge"},
            ], "edges": [
                {"from": "door", "to": "shadow", "relation": "association"},
                {"from": "shadow", "to": "return", "relation": "residue"},
            ], "camera_score": [
                {"camera": "threshold", "door_degrees": 17},
                {"camera": "behind", "door_degrees": 55},
                {"camera": "front", "door_degrees": 90},
            ], "max_steps": 3,
        }

    def test_camera_availability_is_separate_from_known_at(self):
        before = self.snapshot.read_bytes()
        snap = visual_dream.freeze(self.root, self.score)
        self.assertEqual(snap, visual_dream.freeze(self.root, self.score))
        walk = visual_dream.plan(self.root, snap)["walk"]
        self.assertEqual([x["incoming_relation"] for x in walk], [None, "association", "residue"])
        self.assertTrue(walk[0]["depict_fact"])
        self.assertTrue(walk[1]["optically_available"])
        self.assertFalse(walk[1]["audience_known_at_beat"])
        self.assertFalse(walk[1]["depict_fact"])
        self.assertEqual(self.snapshot.read_bytes(), before)
        self.assertEqual(visual_dream.plan(self.root, snap)["authored_motif_recurrences"], ["hinge"])

    def test_changed_camera_and_beat_do_not_backdate_world_knowledge(self):
        altered = copy.deepcopy(self.score)
        altered["camera_score"][0]["door_degrees"] = 16
        self.assertEqual(visual_dream.compile_plan(self.root, altered)["walk"][0]["gate"],
                         "door_or_camera_held")
        altered["beat"] = 1
        self.assertFalse(visual_dream.compile_plan(self.root, altered)["walk"][1]["depict_fact"])

    def test_tampered_snapshot_and_undeclared_fact_fail_closed(self):
        snap = visual_dream.freeze(self.root, self.score)
        changed = copy.deepcopy(self.score)
        changed["nodes"][0]["fact_id"] = "invented"
        with self.assertRaisesRegex(ValueError, "Invalid dream node"):
            visual_dream.compile_plan(self.root, changed)
        snap.write_text(json.dumps(changed), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            visual_dream.plan(self.root, snap)

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg required")
    def test_procedural_render_writes_per_frame_receipt_and_never_overwrites(self):
        try:
            import PIL  # noqa: F401
        except ImportError:
            self.skipTest("Pillow required")
        snap = visual_dream.freeze(self.root, self.score)
        out = self.root / "renders" / "visual-dream" / "synthetic.mp4"
        result = visual_dream.render(self.root, snap, out)
        receipt = json.loads(Path(result["receipt"]).read_text())
        self.assertEqual(receipt["output_frame_count"], 36)
        self.assertEqual(len(receipt["frame_map"]), 36)
        self.assertFalse(any(x["fact_depicted"] for x in receipt["frame_map"]
                             if x["step"] == 1))
        self.assertFalse(receipt["frame_map"][0]["fact_depicted"])
        self.assertTrue(receipt["frame_map"][11]["fact_depicted"])
        self.assertFalse(receipt["distribution_authorized"])
        with self.assertRaisesRegex(ValueError, "overwrite"):
            visual_dream.render(self.root, snap, out)


if __name__ == "__main__":
    unittest.main()
