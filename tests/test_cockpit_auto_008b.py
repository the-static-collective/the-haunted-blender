import json
import shutil
import tempfile
import unittest
from pathlib import Path

from haunted_blender import cockpit, cockpit_engine, cockpit_media
from haunted_blender.dream_cutout_compiler import KIT_SCHEMA
from haunted_blender.motion_organ import OFFERS_SCHEMA


class CockpitAutoCrossings008bTests(unittest.TestCase):
    def setUp(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("FFmpeg required")
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow required")
        self.Image = Image

    def make_project(self, root: Path):
        cockpit.create_project(root, project_id="auto-008b", title="Auto Film", local_only=True)
        cockpit.add_section(root, section_id="chorus", kind="chorus", start=0, end=2.0, label="Chorus")

        self.Image.new("RGBA", (96, 54), (30, 35, 50, 255)).save(root / "bg.png")
        self.Image.new("RGBA", (20, 30), (220, 180, 80, 255)).save(root / "actor.png")
        kit = {
            "schema": KIT_SCHEMA,
            "canvas": {"width": 96, "height": 54},
            "layers": [
                {"id": "background", "role": "background", "source": "bg.png", "z": 0, "x": 0, "y": 0},
                {"id": "actor", "role": "actor", "source": "actor.png", "z": 1, "x": 20, "y": 20},
            ],
        }
        (root / "kit.json").write_text(json.dumps(kit), encoding="utf-8")

        offers = {
            "schema": OFFERS_SCHEMA,
            "observedAt": "2026-10-06T02:00:00Z",
            "offers": [
                {
                    "offerId": "free-i2v",
                    "providerId": "provider-test",
                    "model": "test-i2v",
                    "available": True,
                    "spendClass": "free",
                    "creditCost": 1,
                    "creditBalance": 100,
                    "inputModes": ["image-to-video"],
                    "aspectRatios": ["16:9"],
                    "minSeconds": 0.5,
                    "maxSeconds": 8,
                }
            ],
        }
        (root / "offers.json").write_text(json.dumps(offers), encoding="utf-8")

        cockpit_engine.configure_project(
            root,
            source_receipt_ids=["receipt-real-a"],
            kit_path="kit.json",
            motion_offers_path="offers.json",
            fps=8,
            preview_seconds=0.5,
            occurrence_budget_usd_micros=100000,
            per_job_budget_usd_micros=50000,
        )

    def test_grow_keep_play_is_real_and_needs_no_internal_ids(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_project(root)

            grown = cockpit_engine.grow(root, "chorus")
            self.assertEqual(len(grown["proposals"]), 6)
            self.assertTrue(Path(grown["sixupVideo"]).is_file())
            self.assertEqual(cockpit.cockpit_view(root)["sections"][0]["temperature"], "dreaming")

            kept = cockpit_engine.keep(root, "chorus", slot=1)
            self.assertEqual(kept["keptSlot"], 1)
            self.assertTrue(Path(kept["sceneVideo"]).is_file())
            self.assertEqual(cockpit.cockpit_view(root)["sections"][0]["temperature"], "moving")

            media = cockpit_media.media_view(root, "chorus")
            self.assertIsNotNone(media["sixup"])
            self.assertIsNotNone(media["scene"])

            preview = cockpit_engine.play(root)
            self.assertTrue(Path(preview["preview"]).is_file())
            self.assertGreater(Path(preview["preview"]).stat().st_size, 0)
            self.assertEqual(preview["authority"], "derived-preview-only")

    def test_awaken_prepares_006_007_but_does_not_submit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_project(root)
            cockpit_engine.grow(root, "chorus")
            cockpit_engine.keep(root, "chorus", slot=2)
            cockpit.set_local_only(root, False)

            result = cockpit_engine.awaken(root, "chorus")
            self.assertFalse(result["submitted"])
            self.assertEqual(result["next"]["action"], "CAPABILITIES")
            self.assertTrue(result["requestSha256"])
            self.assertTrue(result["routeSha256"])
            self.assertTrue(result["planSha256"])
            self.assertEqual(cockpit.cockpit_view(root)["sections"][0]["temperature"], "awakening")

            view = cockpit_engine.engine_view(root, "chorus")
            self.assertEqual(view["nextMotionAction"]["action"], "CAPABILITIES")
            self.assertEqual(len(view["awakeningWindows"]), 1)

    def test_local_only_still_blocks_automatic_awaken(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_project(root)
            cockpit_engine.grow(root, "chorus")
            cockpit_engine.keep(root, "chorus", slot=3)
            with self.assertRaises(ValueError):
                cockpit_engine.awaken(root, "chorus")
            self.assertEqual(cockpit.cockpit_view(root)["sections"][0]["temperature"], "moving")

    def test_grow_is_resumable_without_duplicate_ecology(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_project(root)
            first = cockpit_engine.grow(root, "chorus")
            second = cockpit_engine.grow(root, "chorus")
            self.assertEqual(first["ecologyId"], second["ecologyId"])
            self.assertEqual(cockpit.resume_summary(root)["resume"]["unbornSixups"], 1)


if __name__ == "__main__":
    unittest.main()
