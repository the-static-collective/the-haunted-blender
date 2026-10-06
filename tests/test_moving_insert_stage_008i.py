import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from haunted_blender import (
    flow_pantry,
    moving_insert_stage,
    parts_harvester,
    puppet_factory,
    scene_growth,
    stage_compost,
)


class MovingInsertStage008iTests(unittest.TestCase):
    def setUp(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("FFmpeg required")
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            self.skipTest("Pillow required")
        self.Image = Image
        self.ImageDraw = ImageDraw

    def make_video(self, path: Path, *, pattern="testsrc2", duration=1.2, audio=False):
        args = ["ffmpeg", "-v", "error", "-y"]
        if pattern == "testsrc2":
            args += ["-f", "lavfi", "-i", f"testsrc2=s=192x108:r=12:d={duration}"]
        elif pattern == "bars":
            args += ["-f", "lavfi", "-i", f"smptebars=s=192x108:r=12:d={duration}"]
        else:
            args += ["-f", "lavfi", "-i", f"color=c={pattern}:s=192x108:r=12:d={duration}"]
        if audio:
            args += ["-f", "lavfi", "-i", f"sine=frequency=440:sample_rate=44100:duration={duration}"]
            args += ["-shortest", "-c:a", "aac"]
        else:
            args += ["-an"]
        args += ["-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)]
        subprocess.run(args, check=True)

    def has_audio(self, path: Path) -> bool:
        proc = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "a",
                "-show_entries", "stream=index",
                "-of", "csv=p=0",
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return bool(proc.stdout.strip())

    def part(self, path: Path, fill):
        image = self.Image.new("RGBA", (44, 44), (0, 0, 0, 0))
        draw = self.ImageDraw.Draw(image)
        draw.rectangle((2, 2, 41, 41), fill=fill, outline=(20, 20, 20, 255), width=2)
        image.save(path)

    def puppet_spec(self, root: Path):
        for name, fill in (
            ("body", (210, 70, 60, 255)),
            ("head", (230, 208, 170, 255)),
            ("arm-l", (210, 70, 60, 255)),
            ("arm-r", (210, 70, 60, 255)),
            ("leg-l", (50, 70, 130, 255)),
            ("leg-r", (50, 70, 130, 255)),
        ):
            self.part(root / f"{name}.png", fill)
        return {
            "schema": puppet_factory.SPEC_SCHEMA,
            "label": "TV Puppet",
            "canvas": {"width": 320, "height": 180, "fps": 12},
            "parts": [
                {"id": "leg-left", "role": "leg-left", "source": str(root / "leg-l.png"), "x": 132, "y": 118},
                {"id": "leg-right", "role": "leg-right", "source": str(root / "leg-r.png"), "x": 164, "y": 118},
                {"id": "body", "role": "body", "source": str(root / "body.png"), "x": 138, "y": 78},
                {"id": "arm-left", "role": "arm-left", "source": str(root / "arm-l.png"), "x": 112, "y": 82},
                {"id": "arm-right", "role": "arm-right", "source": str(root / "arm-r.png"), "x": 190, "y": 82},
                {"id": "head", "role": "head", "source": str(root / "head.png"), "x": 138, "y": 30},
            ],
        }

    def timing(self):
        return scene_growth.normalize_timing(
            {
                "schemaVersion": "0.1",
                "id": "moving-room-song",
                "duration": 4.0,
                "gates": [
                    {"id": "a", "at": 0.0, "kind": "verse", "label": "A"},
                    {"id": "b", "at": 2.0, "kind": "chorus", "label": "B"},
                ],
            },
            {
                "schema": "full-measure.lyrics.v1",
                "cues": [
                    {"start": 0.2, "end": 1.5, "text": "the television wakes"},
                    {"start": 2.1, "end": 3.6, "text": "the window remembers"},
                ],
            },
        )

    def make_dressing(self, root: Path):
        source = root / "source"
        source.mkdir()
        self.make_video(source / "a.mp4", pattern="testsrc2", duration=1.0)
        self.make_video(source / "b.mp4", pattern="bars", duration=1.1)
        manifest = flow_pantry.index_flow_folder(source, probe=True)
        parts_harvester.harvest_flow_manifest(
            manifest,
            source,
            root / "parts",
            still_count=3,
            loop_seconds=0.6,
            fragment_seconds=0.4,
        )
        drawer = json.loads((root / "parts" / "parts-drawer.json").read_text(encoding="utf-8"))
        dressing = stage_compost.plan(
            drawer, width=320, height=180, duration_seconds=4.0
        )
        return drawer, dressing

    def test_plan_converts_harvested_moving_bits_into_bounded_surfaces(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _drawer, dressing = self.make_dressing(root)
            plan = moving_insert_stage.plan_from_dressing(
                dressing,
                width=320,
                height=180,
                fps=12,
                duration_seconds=4.0,
                max_inserts=4,
            )
            self.assertEqual(plan["schema"], moving_insert_stage.SCHEMA)
            self.assertGreaterEqual(len(plan["inserts"]), 1)
            self.assertLessEqual(len(plan["inserts"]), 4)
            self.assertEqual(plan["inserts"][0]["role"], "television")
            self.assertEqual(plan["inserts"][0]["start"], 0.0)
            self.assertEqual(plan["inserts"][0]["end"], 4.0)
            self.assertTrue(all(row["mute"] for row in plan["inserts"]))
            self.assertEqual(plan["cost"]["providerCredits"], 0)

    def test_render_preserves_base_audio_and_duration_while_changing_pixels(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            base = root / "base.mp4"
            moving = root / "moving.mp4"
            self.make_video(base, pattern="navy", duration=3.0, audio=True)
            self.make_video(moving, pattern="testsrc2", duration=0.7, audio=True)
            sha = parts_harvester._file_sha(moving)
            dressing = {
                "schema": stage_compost.SCHEMA,
                "id": "dressing:test",
                "movingInserts": [{
                    "kind": "loop",
                    "path": str(moving),
                    "sha256": sha,
                    "sourceSha256": "b" * 64,
                    "harvestId": "harvest:test",
                }],
            }
            plan = moving_insert_stage.plan_from_dressing(
                dressing,
                width=192,
                height=108,
                fps=12,
                duration_seconds=3.0,
                max_inserts=1,
            )
            out = root / "out.mp4"
            receipt = moving_insert_stage.render(base, plan, out)
            self.assertTrue(out.is_file())
            self.assertNotEqual(receipt["baseSha256"], receipt["outputSha256"])
            self.assertGreaterEqual(receipt["durationSeconds"], 2.94)
            self.assertEqual(receipt["insertCount"], 1)
            self.assertEqual(receipt["audioAuthority"], "base-performance-only")
            self.assertTrue(self.has_audio(out))
            self.assertEqual(receipt["providerCredits"], 0)

    def test_source_byte_mutation_after_planning_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            base = root / "base.mp4"
            moving = root / "moving.mp4"
            self.make_video(base, pattern="black", duration=2.0)
            self.make_video(moving, pattern="testsrc2", duration=0.8)
            sha = parts_harvester._file_sha(moving)
            dressing = {
                "schema": stage_compost.SCHEMA,
                "id": "dressing:test",
                "movingInserts": [{
                    "kind": "loop",
                    "path": str(moving),
                    "sha256": sha,
                    "sourceSha256": "c" * 64,
                    "harvestId": "harvest:test",
                }],
            }
            plan = moving_insert_stage.plan_from_dressing(
                dressing, width=192, height=108, fps=12, duration_seconds=2.0
            )
            self.make_video(moving, pattern="red", duration=0.8)
            # Replanning catches the changed harvested bytes.
            with self.assertRaises(ValueError):
                moving_insert_stage.plan_from_dressing(
                    dressing, width=192, height=108, fps=12, duration_seconds=2.0
                )

    def test_parts_drawer_automatically_becomes_real_moving_puppet_surfaces(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            drawer, dressing = self.make_dressing(root)
            rig = puppet_factory.build_rig(self.puppet_spec(root), root / "rig")
            performance = puppet_factory.compile_performance(
                rig, self.timing(), root / "performance"
            )
            dressed = stage_compost.apply_to_performance(performance, dressing)
            self.assertIn("movingInsertPlan", dressed)
            self.assertGreater(len(dressed["movingInsertPlan"]["inserts"]), 0)

            receipt = puppet_factory.render_performance(
                dressed, root / "moving-puppet.mp4"
            )
            self.assertTrue(Path(receipt["output"]).is_file())
            self.assertGreater(receipt["movingInsertRenderedCount"], 0)
            self.assertGreater(receipt["movingInsertProposalCount"], 0)
            self.assertAlmostEqual(receipt["durationSeconds"], 4.0, delta=0.06)
            self.assertEqual(receipt["providerCredits"], 0)
            self.assertEqual(receipt["usdMicros"], 0)
            for row in receipt["movingInsertReceipt"]["inserts"]:
                self.assertEqual(len(row["sourceSha256"]), 64)
                self.assertEqual(len(row["sourceProvenanceSha256"]), 64)

    def test_no_inserts_is_identity_copy_not_fake_generation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            base = root / "base.mp4"
            self.make_video(base, pattern="green", duration=1.5)
            plan = {
                "schema": moving_insert_stage.SCHEMA,
                "id": "moving-insert-plan:none",
                "canvas": {"width": 192, "height": 108, "fps": 12, "durationSeconds": 1.5},
                "inserts": [],
            }
            out = root / "copy.mp4"
            receipt = moving_insert_stage.render(base, plan, out)
            self.assertEqual(receipt["status"], "no-inserts-copy")
            self.assertEqual(receipt["insertCount"], 0)
            self.assertEqual(receipt["baseSha256"], receipt["outputSha256"])
            self.assertEqual(receipt["providerCredits"], 0)


if __name__ == "__main__":
    unittest.main()
