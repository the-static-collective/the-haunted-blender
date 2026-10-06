import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from haunted_blender import (
    flow_pantry,
    parts_harvester,
    puppet_factory,
    scene_growth,
    stage_compost,
)


class PartsHarvester008hTests(unittest.TestCase):
    def setUp(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("FFmpeg required")
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            self.skipTest("Pillow required")
        self.Image = Image
        self.ImageDraw = ImageDraw

    def make_video(self, path: Path, *, mode: str = "testsrc2", duration: float = 2.4):
        if mode == "testsrc2":
            source = f"testsrc2=s=192x108:r=12:d={duration}"
        elif mode == "bars":
            source = f"smptebars=s=192x108:r=12:d={duration}"
        else:
            source = f"color=c={mode}:s=192x108:r=12:d={duration}"
        subprocess.run(
            [
                "ffmpeg", "-v", "error", "-y",
                "-f", "lavfi", "-i", source,
                "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path),
            ],
            check=True,
        )

    def make_part(self, path: Path, size=(48, 48), fill=(220, 190, 150, 255)):
        image = self.Image.new("RGBA", size, (0, 0, 0, 0))
        draw = self.ImageDraw.Draw(image)
        draw.rectangle((2, 2, size[0] - 3, size[1] - 3), fill=fill, outline=(20, 20, 20, 255), width=2)
        image.save(path)

    def puppet_spec(self, root: Path):
        for name in ("body", "head", "arm-l", "arm-r", "leg-l", "leg-r"):
            self.make_part(root / f"{name}.png")
        return {
            "schema": puppet_factory.SPEC_SCHEMA,
            "label": "Compost Puppet",
            "canvas": {"width": 320, "height": 180, "fps": 12},
            "parts": [
                {"id": "leg-left", "role": "leg-left", "source": str(root / "leg-l.png"), "x": 132, "y": 118},
                {"id": "leg-right", "role": "leg-right", "source": str(root / "leg-r.png"), "x": 164, "y": 118},
                {"id": "body", "role": "body", "source": str(root / "body.png"), "x": 136, "y": 78},
                {"id": "arm-left", "role": "arm-left", "source": str(root / "arm-l.png"), "x": 112, "y": 80},
                {"id": "arm-right", "role": "arm-right", "source": str(root / "arm-r.png"), "x": 190, "y": 80},
                {"id": "head", "role": "head", "source": str(root / "head.png"), "x": 138, "y": 30},
            ],
        }

    def timing(self):
        track = {
            "schemaVersion": "0.1",
            "id": "compost-song",
            "duration": 4.0,
            "gates": [
                {"id": "a", "at": 0, "kind": "verse", "label": "A"},
                {"id": "b", "at": 2, "kind": "chorus", "label": "B"},
            ],
        }
        lyrics = {
            "schema": "full-measure.lyrics.v1",
            "cues": [
                {"start": 0.2, "end": 1.2, "text": "paper world"},
                {"start": 2.1, "end": 3.4, "text": "move these bits!"},
            ],
        }
        return scene_growth.normalize_timing(track, lyrics)

    def test_one_clip_explodes_into_many_traceable_parts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.mp4"
            self.make_video(source, duration=2.4)
            harvest = parts_harvester.harvest(
                source,
                root / "harvest",
                still_count=4,
                loop_seconds=0.8,
                fragment_seconds=0.5,
                sample_fps=4,
            )
            self.assertEqual(harvest["schema"], parts_harvester.SCHEMA)
            self.assertEqual(harvest["counts"]["stills"], 4)
            self.assertEqual(harvest["counts"]["crops"], 15)
            self.assertEqual(harvest["counts"]["textures"], 9)
            self.assertEqual(harvest["counts"]["masks"], 9)
            self.assertEqual(harvest["counts"]["loops"], 3)
            self.assertEqual(harvest["counts"]["fragments"], 3)
            self.assertGreater(harvest["derivativeYieldCount"], 35)
            self.assertEqual(harvest["cost"]["providerCredits"], 0)
            source_sha = harvest["source"]["sha256"]
            for artifact in harvest["artifacts"]:
                self.assertEqual(artifact["sourceSha256"], source_sha)
                self.assertTrue(Path(artifact["path"]).is_file())
                self.assertEqual(len(artifact["sha256"]), 64)

    def test_motion_behavior_can_move_unrelated_appearance_without_identity_collapse(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "motion.mp4"
            self.make_video(source, duration=2.0)
            harvest = parts_harvester.harvest(source, root / "harvest", still_count=3)
            behavior_row = next(x for x in harvest["artifacts"] if x["kind"] == "motion-behavior")
            behavior = json.loads(Path(behavior_row["path"]).read_text(encoding="utf-8"))
            self.assertGreater(behavior["meanEnergy"], 0)
            target_sha = "a" * 64
            transplant = parts_harvester.behavior_transplant(
                behavior,
                target_source_sha256=target_sha,
                duration_seconds=5.0,
                base_state={"x": 10, "y": 20, "scale": 0.5, "rotation": 0},
            )
            self.assertEqual(transplant["targetSourceSha256"], target_sha)
            self.assertEqual(transplant["durationSeconds"], 5.0)
            self.assertGreater(len(transplant["keyframes"]), 2)
            self.assertEqual(transplant["keyframes"][0]["time"], 0.0)
            self.assertEqual(transplant["keyframes"][-1]["time"], 5.0)

    def test_flow_batch_turns_multiple_sources_into_one_junk_drawer(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "flow"
            source.mkdir()
            self.make_video(source / "a.mp4", mode="testsrc2")
            self.make_video(source / "b.mp4", mode="bars")
            manifest = flow_pantry.index_flow_folder(source, probe=True)
            summary = parts_harvester.harvest_flow_manifest(
                manifest,
                source,
                root / "batch",
                still_count=3,
                loop_seconds=0.7,
                fragment_seconds=0.4,
            )
            drawer = json.loads((root / "batch" / "parts-drawer.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["sourceCount"], 2)
            self.assertEqual(drawer["sourceCount"], 2)
            self.assertGreater(drawer["artifactCount"], 60)
            self.assertGreaterEqual(drawer["byKind"]["loop"], 6)
            self.assertEqual(summary["providerCredits"], 0)
            sources = {row["sourceSha256"] for row in drawer["artifacts"]}
            self.assertEqual(len(sources), 2)

    def test_stage_dresser_keeps_appearance_and_behavior_provenance_separate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "flow"
            source.mkdir()
            self.make_video(source / "a.mp4", mode="testsrc2")
            self.make_video(source / "b.mp4", mode="bars")
            manifest = flow_pantry.index_flow_folder(source, probe=True)
            parts_harvester.harvest_flow_manifest(
                manifest, source, root / "batch", still_count=3
            )
            drawer = json.loads((root / "batch" / "parts-drawer.json").read_text(encoding="utf-8"))
            dressing = stage_compost.plan(
                drawer, width=320, height=180, duration_seconds=4.0
            )
            witness = next(w for w in dressing["witnesses"] if w["role"] == "behavior-prop")
            self.assertNotEqual(
                witness["appearanceSourceSha256"],
                witness["behaviorSourceSha256"],
            )
            prop = next(layer for layer in dressing["layers"] if layer["id"] == "harvest-behavior-prop")
            self.assertGreater(len(prop["keyframes"]), 2)
            self.assertGreater(len(dressing["movingInserts"]), 0)
            self.assertEqual(dressing["cost"]["providerCredits"], 0)

    def test_puppet_world_can_be_dressed_from_drawer_without_new_generation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "flow"
            source.mkdir()
            self.make_video(source / "a.mp4", mode="testsrc2")
            self.make_video(source / "b.mp4", mode="bars")
            manifest = flow_pantry.index_flow_folder(source, probe=True)
            parts_harvester.harvest_flow_manifest(
                manifest, source, root / "batch", still_count=3
            )
            drawer = json.loads((root / "batch" / "parts-drawer.json").read_text(encoding="utf-8"))

            rig = puppet_factory.build_rig(self.puppet_spec(root), root / "rig")
            timing = self.timing()
            base = puppet_factory.compile_performance(rig, timing, root / "base-perf")
            base_receipt = puppet_factory.render_performance(base, root / "base.mp4")

            dressing = stage_compost.plan(
                drawer,
                width=rig["canvas"]["width"],
                height=rig["canvas"]["height"],
                duration_seconds=base["duration"],
            )
            dressed = stage_compost.apply_to_performance(base, dressing)
            dressed_receipt = puppet_factory.render_performance(dressed, root / "dressed.mp4")
            self.assertNotEqual(base_receipt["outputSha256"], dressed_receipt["outputSha256"])
            self.assertAlmostEqual(base_receipt["durationSeconds"], dressed_receipt["durationSeconds"], places=5)
            self.assertGreater(dressed_receipt["harvestedStageLayerCount"], 0)
            self.assertGreater(dressed_receipt["movingInsertProposalCount"], 0)
            self.assertEqual(dressed_receipt["providerCredits"], 0)
            self.assertEqual(dressed_receipt["usdMicros"], 0)


if __name__ == "__main__":
    unittest.main()
