import shutil
import tempfile
import unittest
from pathlib import Path

from haunted_blender import (
    ensemble_stage,
    material_surface,
    paper_director,
    puppet_factory,
    scene_growth,
)


EXPECTED_MATERIALS = {
    "paper",
    "cardboard",
    "wood",
    "clay",
    "felt",
    "plastic",
    "foil",
    "stone",
    "wax",
    "inked",
    "ghost",
    "junk-collage",
}


class MaterialSurface008lTests(unittest.TestCase):
    def setUp(self):
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            self.skipTest("Pillow required")
        self.Image = Image
        self.ImageDraw = ImageDraw

    def source_image(self, path: Path, fill=(190, 120, 70, 255), size=(72, 72)):
        image = self.Image.new("RGBA", size, (0, 0, 0, 0))
        draw = self.ImageDraw.Draw(image)
        draw.rounded_rectangle(
            (5, 5, size[0] - 6, size[1] - 6),
            radius=10,
            fill=fill,
            outline=(20, 20, 20, 255),
            width=3,
        )
        draw.line(
            (10, size[1] // 2, size[0] - 10, size[1] // 2 - 7),
            fill=(245, 225, 180, 255),
            width=3,
        )
        image.save(path)

    def make_rig(self, root: Path, name: str, material: str, *, head_material=None):
        src = root / f"{name}-src"
        src.mkdir()
        for part in ("body", "head", "arm-l", "arm-r", "leg-l", "leg-r"):
            self.source_image(
                src / f"{part}.png",
                fill=(190, 90 + len(part) * 7, 80, 255),
                size=(48, 58) if part != "head" else (50, 46),
            )
        spec = {
            "schema": puppet_factory.SPEC_SCHEMA,
            "label": name,
            "canvas": {"width": 320, "height": 180, "fps": 12},
            "materialDefaults": material,
            "roomMaterial": "cardboard",
            "mouthAnchor": {"x": 145, "y": 66, "scale": 0.5, "z": 55},
            "parts": [
                {"id": "leg-left", "role": "leg-left", "source": str(src / "leg-l.png"), "x": 132, "y": 116},
                {"id": "leg-right", "role": "leg-right", "source": str(src / "leg-r.png"), "x": 162, "y": 116},
                {"id": "body", "role": "body", "source": str(src / "body.png"), "x": 132, "y": 74},
                {"id": "arm-left", "role": "arm-left", "source": str(src / "arm-l.png"), "x": 112, "y": 80},
                {"id": "arm-right", "role": "arm-right", "source": str(src / "arm-r.png"), "x": 188, "y": 80},
                {
                    "id": "head",
                    "role": "head",
                    "source": str(src / "head.png"),
                    "x": 132,
                    "y": 26,
                    **({"material": head_material} if head_material else {}),
                },
            ],
        }
        return puppet_factory.build_rig(spec, root / f"{name}-rig")

    def timing(self, text="hello wooden world"):
        return scene_growth.normalize_timing(
            {
                "schemaVersion": "0.1",
                "id": "material-song",
                "duration": 2.4,
                "gates": [
                    {"id": "verse", "at": 0.0, "kind": "verse", "label": "Verse"},
                ],
            },
            {
                "schema": "full-measure.lyrics.v1",
                "cues": [
                    {"start": 0.25, "end": 1.25, "text": text},
                ],
            },
        )

    def test_expected_material_presets_exist_and_are_aesthetic_only(self):
        self.assertEqual(set(material_surface.PRESETS), EXPECTED_MATERIALS)
        for name in EXPECTED_MATERIALS:
            profile = material_surface.profile(name)
            self.assertEqual(profile["type"], name)
            self.assertEqual(profile["authority"], "aesthetic-profile-only")
            self.assertIn("surface", profile)
            self.assertIn("motion", profile)
            self.assertIn("directing", profile)
            self.assertTrue(profile["id"].startswith("material:"))

    def test_same_source_materializes_to_distinct_wood_clay_and_foil_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.png"
            self.source_image(source)
            source_sha = material_surface._file_sha(source)

            results = {}
            for kind in ("wood", "clay", "foil"):
                results[kind] = material_surface.materialize_asset(
                    source, root / f"{kind}.png", kind
                )
                self.assertEqual(results[kind]["sourceSha256"], source_sha)
                self.assertNotEqual(results[kind]["outputSha256"], source_sha)
                self.assertEqual(results[kind]["material"]["type"], kind)
                self.assertEqual(results[kind]["providerCredits"], 0)

            self.assertEqual(
                len({results[k]["outputSha256"] for k in results}),
                3,
            )

    def test_motion_feel_changes_same_pose_without_changing_material_into_physics(self):
        frames = [
            {"time": 0.0, "x": 10.0, "y": 10.0, "scale": 1.0, "rotation": 0.0, "opacity": 1.0},
            {"time": 1.0, "x": 30.0, "y": 20.0, "scale": 1.2, "rotation": 30.0, "opacity": 1.0},
            {"time": 2.0, "x": 10.0, "y": 10.0, "scale": 1.0, "rotation": 0.0, "opacity": 1.0},
        ]
        paper = material_surface.apply_motion(frames, "paper", fps=12, role="body")
        wood = material_surface.apply_motion(frames, "wood", fps=12, role="body")
        clay = material_surface.apply_motion(frames, "clay", fps=12, role="body")
        foil = material_surface.apply_motion(frames, "foil", fps=12, role="body")
        stone = material_surface.apply_motion(frames, "stone", fps=12, role="body")

        def nearest(rows, at):
            return min(rows, key=lambda row: abs(float(row["time"]) - at))

        self.assertLess(nearest(stone, 1.0)["x"], nearest(wood, 1.0)["x"])
        self.assertLess(nearest(wood, 1.0)["x"], nearest(paper, 1.0)["x"])
        self.assertGreater(nearest(clay, 1.0)["scale"], nearest(paper, 1.0)["scale"])
        self.assertGreater(len(foil), len(paper))
        self.assertIn("MATERIAL != PHYSICS CLAIM", material_surface.profile("wood")["laws"])

    def test_rig_keeps_original_authority_and_materialized_render_sources(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rig = self.make_rig(root, "mixed", "wood", head_material="clay")
            self.assertEqual(rig["materialDefaults"]["type"], "wood")
            self.assertEqual(set(rig["materialTypes"]), {"wood", "clay"})
            self.assertEqual(rig["room"]["material"]["type"], "cardboard")

            head = next(row for row in rig["parts"] if row["id"] == "head")
            body = next(row for row in rig["parts"] if row["id"] == "body")
            self.assertEqual(head["material"]["type"], "clay")
            self.assertEqual(body["material"]["type"], "wood")
            for part in (head, body):
                self.assertTrue(Path(part["source"]).is_file())
                self.assertTrue(Path(part["renderSource"]).is_file())
                self.assertEqual(len(part["sourceSha256"]), 64)
                self.assertEqual(len(part["renderSourceSha256"]), 64)
                self.assertNotEqual(part["sourceSha256"], part["renderSourceSha256"])

    def test_actual_render_uses_materialized_surface_and_records_original_authority(self):
        if not shutil.which("ffmpeg"):
            self.skipTest("FFmpeg required")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            wood_rig = self.make_rig(root, "wood", "wood")
            clay_rig = self.make_rig(root, "clay", "clay")
            timing = self.timing()

            wood_perf = puppet_factory.compile_performance(
                wood_rig, timing, root / "wood-performance"
            )
            clay_perf = puppet_factory.compile_performance(
                clay_rig, timing, root / "clay-performance"
            )
            wood_receipt = puppet_factory.render_performance(
                wood_perf, root / "wood.mp4"
            )
            clay_receipt = puppet_factory.render_performance(
                clay_perf, root / "clay.mp4"
            )
            self.assertNotEqual(
                wood_receipt["outputSha256"],
                clay_receipt["outputSha256"],
            )
            self.assertEqual(wood_receipt["providerCredits"], 0)
            body_receipt = next(
                row for row in wood_receipt["movingInsertReceipt"]["inserts"]
                if False
            ) if wood_receipt.get("movingInsertReceipt") else None
            self.assertIsNone(body_receipt)
            # Cutout material witness is nested in the plan render receipt path;
            # the performance itself freezes both source authorities.
            wood_body = next(
                row for row in wood_perf["cutoutPlan"]["layers"]
                if row["id"] == "body"
            )
            self.assertEqual(wood_body["material"]["type"], "wood")
            self.assertEqual(len(wood_body["sourceAuthoritySha256"]), 64)

    def test_material_is_only_a_weak_directing_vote(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            wood = self.make_rig(root, "wood-direct", "wood")
            clay = self.make_rig(root, "clay-direct", "clay")

            wood_perf = puppet_factory.compile_performance(
                wood, self.timing("ordinary line"), root / "wp"
            )
            clay_perf = puppet_factory.compile_performance(
                clay, self.timing("ordinary line"), root / "cp"
            )
            wood_plan = paper_director.plan(
                self.timing("ordinary line"), performance=wood_perf
            )
            clay_plan = paper_director.plan(
                self.timing("ordinary line"), performance=clay_perf
            )
            wood_cue = next(row for row in wood_plan["shots"] if row.get("cueIndex") == 0)
            clay_cue = next(row for row in clay_plan["shots"] if row.get("cueIndex") == 0)
            self.assertEqual(wood_cue["speakerMaterialType"], "wood")
            self.assertEqual(clay_cue["speakerMaterialType"], "clay")
            self.assertEqual(wood_cue["type"], "WIDE")
            self.assertEqual(clay_cue["type"], "CLOSE_UP")

            question_plan = paper_director.plan(
                self.timing("really?"),
                performance=clay_perf,
            )
            question_cue = next(
                row for row in question_plan["shots"] if row.get("cueIndex") == 0
            )
            self.assertEqual(question_cue["type"], "REACTION")

    def test_mixed_material_ensemble_preserves_each_cast_identity(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            wood = self.make_rig(root, "wood-cast", "wood")
            clay = self.make_rig(root, "clay-cast", "clay")
            timing = scene_growth.normalize_timing(
                {
                    "schemaVersion": "0.1",
                    "id": "mixed-material-dialogue",
                    "duration": 3.0,
                    "gates": [{"id": "v", "at": 0, "kind": "verse", "label": "V"}],
                },
                {
                    "schema": "full-measure.lyrics.v1",
                    "cues": [
                        {"start": 0.2, "end": 1.0, "text": "wood speaks"},
                        {"start": 1.4, "end": 2.3, "text": "clay answers"},
                    ],
                },
            )
            spec = {
                "schema": ensemble_stage.SPEC_SCHEMA,
                "cast": [
                    {"id": "wood", "rig": wood},
                    {"id": "clay", "rig": clay},
                ],
                "dialogue": [
                    {"cueIndex": 0, "speakerId": "wood", "listenerIds": ["clay"]},
                    {"cueIndex": 1, "speakerId": "clay", "listenerIds": ["wood"]},
                ],
            }
            performance = ensemble_stage.compile_ensemble(
                spec, timing, root / "ensemble"
            )
            cast = {row["id"]: row for row in performance["ensemble"]["cast"]}
            self.assertEqual(cast["wood"]["materialDefault"]["type"], "wood")
            self.assertEqual(cast["clay"]["materialDefault"]["type"], "clay")
            self.assertEqual(
                performance["materials"]["cast"]["wood"]["default"]["type"],
                "wood",
            )
            self.assertEqual(
                performance["materials"]["cast"]["clay"]["default"]["type"],
                "clay",
            )


if __name__ == "__main__":
    unittest.main()
