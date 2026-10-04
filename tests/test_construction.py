"""Synthetic image proof for ART × I × FACT constructor order and output ancestry."""
import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from haunted_blender import alchemy, catalog, construction, scene_artifact, scene_weave
from test_scene_artifact import fictional_story, png


REVERSE = {"constructor": "editorial.reverse/v0", "params": {}}
HOLD = {"constructor": "editorial.hold-first/v0", "params": {"duration_ms": 2600}}


class ConstructionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "library"
        self.photo_dir = Path(self.tmp.name) / "sources"
        self.photo_dir.mkdir()
        catalog.init(self.root)
        for name, rgb in (("cup", (125, 80, 50)), ("water", (25, 60, 140)),
                          ("moon", (210, 205, 155))):
            png(self.photo_dir / (name + ".png"), rgb)
        catalog.scan(self.root, self.photo_dir)
        con = catalog.connect(self.root)
        ids = {Path(row["path"]).stem: row["id"]
               for row in con.execute("SELECT id,path FROM assets")}
        con.close()
        recipe = alchemy.create(self.root, ids["cup"], ids["moon"], bridge=ids["water"],
                                relation="triadic-bridge", statement="Fictional motif")
        self.alchemy_snapshot = alchemy.freeze(self.root, recipe["id"])
        self.source = self.make_source(fictional_story())
        self.steps = [REVERSE, HOLD]

    def make_source(self, story):
        created = scene_weave.from_alchemy(self.root, self.alchemy_snapshot, story)
        world_snapshot = scene_weave.freeze(self.root, created["world_id"])
        choices = [{"beat": i, "role": role, "candidate": "wide"}
                   for i, role in enumerate(("source", "bridge", "target"))]
        return scene_artifact.accept(self.root, world_snapshot, self.alchemy_snapshot,
                                     choices, filmmaker_approval=True)["snapshot"]

    def accept(self, source=None, steps=None, intent="An ordered visual experiment"):
        return construction.accept(self.root, source or self.source, intent,
                                   steps if steps is not None else self.steps,
                                   filmmaker_approval=True)

    def test_recipe_is_distinct_from_outcome_and_requires_approval(self):
        with self.assertRaisesRegex(ValueError, "approval"):
            construction.accept(self.root, self.source, "Art", [REVERSE])
        first = self.accept()
        self.assertEqual(first, self.accept())
        self.assertNotIn("output_sha256", json.loads(Path(first["recipe"]).read_text()))
        recipe, digest = construction.load(self.root, first["recipe"])
        self.assertEqual(first["recipe_sha256"], digest)
        self.assertEqual(recipe["art"]["filmmaker_intention"], "An ordered visual experiment")
        self.assertEqual(recipe["fact"]["claim_boundary"],
                         "fictional assertions are not facts about photographed people")
        self.assertFalse(recipe["distribution_authorized"])

    def test_constructor_order_does_not_commute(self):
        left = construction.plan(self.root, self.accept(steps=[REVERSE, HOLD])["recipe"])
        right = construction.plan(self.root, self.accept(steps=[HOLD, REVERSE])["recipe"])
        self.assertNotEqual(left["recipe_sha256"], right["recipe_sha256"])
        self.assertNotEqual(left["shot_sequence"], right["shot_sequence"])
        self.assertEqual([s["frame_asset_id"] for s in left["shot_sequence"]],
                         [s["frame_asset_id"] for s in right["shot_sequence"]])
        self.assertEqual([s["duration_ms"] for s in left["shot_sequence"]], [2600, 1800, 1800])
        self.assertEqual([s["duration_ms"] for s in right["shot_sequence"]], [1800, 1800, 2600])
        self.assertEqual(left["source_facts_sha256"], right["source_facts_sha256"])
        self.assertEqual(left["fictional_world_sha256"], right["fictional_world_sha256"])
        self.assertEqual(len(left["construction_history"]), 2)
        self.assertEqual(left["status"], "not_rendered")

    def test_same_constructor_different_authored_fact_retains_source_scope(self):
        different = copy.deepcopy(fictional_story())
        different["facts"][0]["value"] = "opened"
        other_source = self.make_source(different)
        a = construction.plan(self.root, self.accept(steps=[REVERSE])["recipe"])
        b = construction.plan(self.root, self.accept(source=other_source, steps=[REVERSE])["recipe"])
        self.assertEqual([x["constructor"] for x in a["construction_history"]],
                         [x["constructor"] for x in b["construction_history"]])
        self.assertNotEqual(a["source_facts_sha256"], b["source_facts_sha256"])
        self.assertNotEqual(a["recipe_sha256"], b["recipe_sha256"])
        self.assertEqual([s["frame_asset_id"] for s in a["shot_sequence"]],
                         [s["frame_asset_id"] for s in b["shot_sequence"]])

    def test_refuses_unsupported_constructor_and_parameter_and_stale_media(self):
        for steps in ([{"constructor": "arbitrary-python/v0", "params": {}}],
                      [{"constructor": "editorial.reverse/v0", "params": {"script": "rm -rf"}}],
                      [{"constructor": "editorial.hold-first/v0", "params": {"duration_ms": True}}]):
            with self.subTest(steps=steps):
                with self.assertRaisesRegex(ValueError, "constructor|parameters|duration"):
                    self.accept(steps=steps)
        accepted = self.accept()
        self.assertEqual(len(construction.plan(self.root, accepted["recipe"])["shot_sequence"]), 3)
        (self.photo_dir / "water.png").write_bytes(b"new media after approval")
        with self.assertRaises(ValueError):
            construction.plan(self.root, accepted["recipe"])

    def test_tamper_and_preexisting_outcome_refuse(self):
        accepted = self.accept()
        path = Path(accepted["recipe"])
        contents = path.read_bytes()
        altered = json.loads(contents)
        altered["i"]["steps"][0]["constructor"] = "editorial.hold-first/v0"
        path.write_text(json.dumps(altered))
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            construction.load(self.root, path)
        path.write_bytes(contents)
        self.assertEqual(construction.load(self.root, path)[1], accepted["recipe_sha256"])
        existing = self.root / "renders" / "existing.mp4"
        existing.write_bytes(b"preexisting data")
        with self.assertRaises(FileExistsError):
            construction.render_recipe(self.root, path, existing)
        self.assertEqual(existing.read_bytes(), b"preexisting data")

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg unavailable: plan checks still execute")
    def test_real_mp4_has_separate_constructor_and_n0_receipts(self):
        accepted = self.accept()
        out = self.root / "renders" / "constructed.mp4"
        result = construction.render_recipe(self.root, accepted["recipe"], out)
        self.assertTrue(out.stat().st_size > 0)
        self.assertEqual(result["output_sha256"], catalog.digest_file(out))
        self.assertTrue(out.with_suffix(".mp4.receipt.json").is_file())
        witness = json.loads(out.with_suffix(".mp4.construction.json").read_text())
        self.assertEqual(witness["status"], "scoped_complete")
        self.assertEqual(witness["recipe_sha256"], accepted["recipe_sha256"])
        self.assertEqual(witness["output_sha256"], catalog.digest_file(out))
        self.assertNotEqual(witness["output_sha256"], accepted["recipe_sha256"])
        self.assertEqual(len(witness["constructor_history"]), 2)
        self.assertFalse(witness["distribution_authorized"])
        with self.assertRaises(FileExistsError):
            construction.render_recipe(self.root, accepted["recipe"], out)


if __name__ == "__main__":
    unittest.main()
