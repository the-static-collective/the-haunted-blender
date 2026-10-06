import json
import shutil
import tempfile
import unittest
from pathlib import Path

from haunted_blender import cutaway_machine, puppet_factory, scene_growth, weakest_window_doctor


class CutoutPuppetFactory008gTests(unittest.TestCase):
    def setUp(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("FFmpeg required")
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            self.skipTest("Pillow required")
        self.Image = Image
        self.ImageDraw = ImageDraw

    def part(self, path: Path, size, fill, shape="rect"):
        image = self.Image.new("RGBA", size, (0, 0, 0, 0))
        draw = self.ImageDraw.Draw(image)
        if shape == "ellipse":
            draw.ellipse((1, 1, size[0] - 2, size[1] - 2), fill=fill, outline=(20, 20, 20, 255), width=2)
        else:
            draw.rectangle((1, 1, size[0] - 2, size[1] - 2), fill=fill, outline=(20, 20, 20, 255), width=2)
        image.save(path)

    def make_spec(self, root: Path):
        self.part(root / "body.png", (64, 80), (217, 68, 62, 255))
        self.part(root / "head.png", (62, 55), (236, 216, 177, 255), "ellipse")
        self.part(root / "arm-l.png", (18, 62), (217, 68, 62, 255))
        self.part(root / "arm-r.png", (18, 62), (217, 68, 62, 255))
        self.part(root / "leg-l.png", (20, 55), (55, 75, 132, 255))
        self.part(root / "leg-r.png", (20, 55), (55, 75, 132, 255))
        return {
            "schema": puppet_factory.SPEC_SCHEMA,
            "label": "Paper Person",
            "canvas": {"width": 320, "height": 180, "fps": 12},
            "roomLabel": "THE ROOM",
            "mouthAnchor": {"x": 145, "y": 66, "scale": 0.55, "z": 55},
            "parts": [
                {"id": "leg-left", "role": "leg-left", "source": str(root / "leg-l.png"), "x": 132, "y": 118},
                {"id": "leg-right", "role": "leg-right", "source": str(root / "leg-r.png"), "x": 164, "y": 118},
                {"id": "body", "role": "body", "source": str(root / "body.png"), "x": 128, "y": 74},
                {"id": "arm-left", "role": "arm-left", "source": str(root / "arm-l.png"), "x": 112, "y": 80},
                {"id": "arm-right", "role": "arm-right", "source": str(root / "arm-r.png"), "x": 192, "y": 80},
                {"id": "head", "role": "head", "source": str(root / "head.png"), "x": 130, "y": 26},
            ],
        }

    def timing(self, duration=6.0):
        track = {
            "schemaVersion": "0.1",
            "id": "puppet-song",
            "duration": duration,
            "gates": [
                {"id": "verse", "at": 0, "kind": "verse", "label": "Verse"},
                {"id": "chorus", "at": duration / 2, "kind": "chorus", "label": "Chorus"},
            ],
        }
        lyrics = {
            "schema": "full-measure.lyrics.v1",
            "cues": [
                {"start": 0.2, "end": 1.25, "text": "I was down in the dust"},
                {"start": 1.45, "end": 2.65, "text": "then mercy hit hard!"},
                {"start": 3.1, "end": 4.25, "text": "up and up again"},
                {"start": 4.45, "end": 5.65, "text": "are you hearing this?"},
            ],
        }
        return scene_growth.normalize_timing(track, lyrics)

    def doctor_report(self):
        windows = [
            {
                "id": "window-0001",
                "start": 0.0,
                "end": 2.0,
                "weaknessScore": 0.82,
                "dominantWeakness": "stasis",
            },
            {
                "id": "window-0002",
                "start": 2.0,
                "end": 4.0,
                "weaknessScore": 0.71,
                "dominantWeakness": "recentRepetition",
            },
            {
                "id": "window-0003",
                "start": 4.0,
                "end": 6.0,
                "weaknessScore": 0.63,
                "dominantWeakness": "transitionJolt",
            },
        ]
        return {
            "schema": weakest_window_doctor.REPORT_SCHEMA,
            "id": "weak-report:test",
            "windows": windows,
            "ranking": [row["id"] for row in windows],
            "coverageRatio": 1.0,
            "meanWeakness": 0.72,
        }

    def test_build_rig_creates_room_mouth_atlas_and_pose_grammar(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            spec = self.make_spec(root)
            rig = puppet_factory.build_rig(spec, root / "rig")
            self.assertEqual(rig["schema"], puppet_factory.RIG_SCHEMA)
            self.assertTrue(Path(rig["room"]["path"]).is_file())
            self.assertEqual(set(rig["mouth"]["atlas"]), set(puppet_factory.MOUTH_SHAPES))
            self.assertIn("yell", rig["poseGrammar"])
            self.assertIn("walk", rig["poseGrammar"])
            self.assertIn("side-eye", rig["poseGrammar"])
            self.assertEqual(len(rig["parts"]), 6)

    def test_lyrics_become_mouth_events_pose_events_and_physical_geography(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rig = puppet_factory.build_rig(self.make_spec(root), root / "rig")
            timing = self.timing()
            performance = puppet_factory.compile_performance(rig, timing, root / "perf")
            self.assertGreater(len(performance["mouthEvents"]), 10)
            self.assertEqual(len(performance["poseEvents"]), 4)
            self.assertEqual(len(performance["lyricGeography"]), 4)
            self.assertTrue(all(Path(row["path"]).is_file() for row in performance["lyricGeography"]))
            self.assertTrue(any(row["shape"] == "round" for row in performance["mouthEvents"]))
            self.assertTrue(any(row["pose"] == "yell" for row in performance["poseEvents"]))
            self.assertTrue(any(row["pose"] == "shrug" for row in performance["poseEvents"]))
            self.assertEqual(performance["cost"]["providerCredits"], 0)

    def test_one_puppet_and_one_room_render_full_timed_movie_for_zero_provider_cost(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rig = puppet_factory.build_rig(self.make_spec(root), root / "rig")
            timing = self.timing()
            performance = puppet_factory.compile_performance(rig, timing, root / "perf")
            receipt = puppet_factory.render_performance(performance, root / "puppet.mp4")
            self.assertTrue(Path(receipt["output"]).is_file())
            self.assertAlmostEqual(receipt["durationSeconds"], 6.0, places=5)
            self.assertEqual(receipt["frameCount"], 72)
            self.assertGreater(receipt["mouthEventCount"], 10)
            self.assertEqual(receipt["lyricGeographyCount"], 4)
            self.assertEqual(receipt["externalGenerations"], 0)
            self.assertEqual(receipt["providerCredits"], 0)
            self.assertEqual(receipt["usdMicros"], 0)

    def test_cutaway_machine_uses_doctor_weakness_and_changes_rendered_movie(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rig = puppet_factory.build_rig(self.make_spec(root), root / "rig")
            timing = self.timing()
            report = self.doctor_report()
            cutaways = cutaway_machine.plan_from_doctor(
                report, timing, max_cutaways=3, duration_seconds=0.8
            )
            self.assertEqual([e["kind"] for e in cutaways["entries"]], ["reaction", "prop-gag", "establishing"])
            self.assertTrue(all(e["providerCredits"] == 0 for e in cutaways["entries"]))

            base = puppet_factory.compile_performance(rig, timing, root / "base-perf")
            base_receipt = puppet_factory.render_performance(base, root / "base.mp4")
            altered = puppet_factory.compile_performance(
                rig, timing, root / "cut-perf", cutaway_plan=cutaways
            )
            altered_receipt = puppet_factory.render_performance(altered, root / "cut.mp4")
            self.assertEqual(altered_receipt["cutawayCount"], 3)
            self.assertNotEqual(base_receipt["outputSha256"], altered_receipt["outputSha256"])
            self.assertAlmostEqual(base_receipt["durationSeconds"], altered_receipt["durationSeconds"], places=5)

    def test_same_rig_compiles_longer_performance_without_new_provider_work(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rig = puppet_factory.build_rig(self.make_spec(root), root / "rig")
            timing = self.timing(duration=18.0)
            # Extend cue positions by leaving the same first cues and a long held tail.
            performance = puppet_factory.compile_performance(rig, timing, root / "long")
            self.assertEqual(performance["duration"], 18.0)
            self.assertEqual(performance["rigId"], rig["id"])
            self.assertEqual(performance["cost"]["externalGenerations"], 0)
            self.assertEqual(performance["cost"]["providerCredits"], 0)
            self.assertEqual(performance["cost"]["usdMicros"], 0)


if __name__ == "__main__":
    unittest.main()
