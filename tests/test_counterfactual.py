"""Two privately accepted worlds: same events and images, different audience cuts."""
import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from haunted_blender import alchemy, catalog, counterfactual, scene_artifact, scene_weave
from test_scene_artifact import fictional_story, png


class CounterfactualTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / "vault"
        self.photos = Path(temp.name) / "photos"
        self.photos.mkdir()
        catalog.init(self.root)
        for name, rgb in (("cup", (150, 70, 50)), ("water", (25, 70, 160)),
                          ("moon", (200, 200, 150))):
            png(self.photos / (name + ".png"), rgb)
        catalog.scan(self.root, self.photos)
        con = catalog.connect(self.root)
        ids = {Path(r["path"]).stem: r["id"] for r in con.execute("SELECT path,id FROM assets")}
        con.close()
        recipe = alchemy.create(self.root, ids["cup"], ids["moon"], bridge=ids["water"],
                                relation="triadic-bridge", statement="Fictional motif")
        self.alchemy_snapshot = alchemy.freeze(self.root, recipe["id"])
        story_a = fictional_story()
        story_b = copy.deepcopy(story_a)
        story_b["knowledge"][-1]["since_beat"] = 1  # filmmaker delays the audience's knowledge
        self.world_a = self._world(story_a)
        self.world_b = self._world(story_b)
        self.roles_a = ("source", "bridge", "target")
        self.roles_b = ("bridge", "source", "target")
        self.cut_a = self._cut(self.world_a, self.roles_a)
        self.cut_b = self._cut(self.world_b, self.roles_b)

    def _world(self, story):
        seed = scene_weave.from_alchemy(self.root, self.alchemy_snapshot, story)
        return scene_weave.freeze(self.root, seed["world_id"])

    def _cut(self, world, roles):
        choices = [{"beat": i, "role": role, "candidate": "wide"}
                   for i, role in enumerate(roles)]
        return scene_artifact.accept(self.root, world, self.alchemy_snapshot, choices,
                                     filmmaker_approval=True)["snapshot"]

    def _pair(self):
        return counterfactual.accept(self.root, self.cut_a, self.cut_b,
                                     filmmaker_approval=True)

    def test_pair_requires_approval_and_distinct_authored_audience_cut(self):
        with self.assertRaisesRegex(ValueError, "approval"):
            counterfactual.accept(self.root, self.cut_a, self.cut_b)
        result = self._pair()
        self.assertEqual(self._pair(), result)
        pair, digest = counterfactual.load(self.root, result["snapshot"])
        self.assertEqual(digest, result["sha256"])
        self.assertEqual(pair["knowledge_differences"], [
            {"beat": 0, "beat_id": "arrival", "cut_a_known": ["sealed"], "cut_b_known": []}])
        self.assertFalse(pair["distribution_authorized"])
        self.assertNotEqual(pair["cuts"][0]["shots"][0]["frame_asset_id"],
                            pair["cuts"][1]["shots"][0]["frame_asset_id"])

    def test_refuses_event_changes_same_images_in_same_order_and_different_media(self):
        other_story = fictional_story()
        other_story["facts"][0]["value"] = "open"
        other = self._cut(self._world(other_story), self.roles_b)
        with self.assertRaisesRegex(ValueError, "same authored events"):
            counterfactual.accept(self.root, self.cut_a, other, filmmaker_approval=True)
        identical_order = self._cut(self.world_b, self.roles_a)
        with self.assertRaisesRegex(ValueError, "image orders"):
            counterfactual.accept(self.root, self.cut_a, identical_order, filmmaker_approval=True)
        different_media = self._cut(self.world_b, ("source", "source", "target"))
        with self.assertRaisesRegex(ValueError, "same source image"):
            counterfactual.accept(self.root, self.cut_a, different_media, filmmaker_approval=True)

    def test_no_knowledge_difference_and_tampered_pair_refuse(self):
        same_knowledge = self._cut(self._world(fictional_story()), self.roles_b)
        with self.assertRaisesRegex(ValueError, "different authored audience knowledge"):
            counterfactual.accept(self.root, self.cut_a, same_knowledge,
                                  filmmaker_approval=True)
        pair = self._pair()
        path = Path(pair["snapshot"])
        data = json.loads(path.read_text())
        data["knowledge_differences"] = []
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            counterfactual.load(self.root, path)

    def test_changed_source_refuses_before_pair_render(self):
        pair = self._pair()
        (self.photos / "water.png").write_bytes(b"replaced")
        with self.assertRaises(ValueError):
            counterfactual.render_pair(self.root, pair["snapshot"],
                                       self.root / "renders" / "a.mp4",
                                       self.root / "renders" / "b.mp4")
        self.assertFalse((self.root / "renders" / "a.mp4").exists())

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg unavailable")
    def test_two_real_mp4s_with_independent_receipts_and_pair_receipt(self):
        pair = self._pair()
        a = self.root / "renders" / "cut-a.mp4"
        b = self.root / "renders" / "cut-b.mp4"
        result = counterfactual.render_pair(self.root, pair["snapshot"], a, b)
        self.assertNotEqual(catalog.digest_file(a), catalog.digest_file(b))
        self.assertEqual(len(result["cuts"]), 2)
        receipt = json.loads(Path(result["receipt"]).read_text())
        self.assertEqual(receipt["status"], "scoped_complete")
        self.assertEqual(receipt["pair_sha256"], pair["sha256"])
        for entry, video in zip(receipt["cuts"], (a, b)):
            self.assertEqual(entry["output_sha256"], catalog.digest_file(video))
            self.assertTrue(video.with_suffix(".mp4.receipt.json").is_file())
            self.assertTrue(video.with_suffix(".mp4.scene-artifact.json").is_file())
        with self.assertRaises(FileExistsError):
            counterfactual.render_pair(self.root, pair["snapshot"], a, b)


if __name__ == "__main__":
    unittest.main()
