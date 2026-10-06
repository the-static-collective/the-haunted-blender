import shutil
import tempfile
import unittest
from pathlib import Path

from haunted_blender import ensemble_stage, paper_director, puppet_factory, scene_growth


class EnsembleStage008kTests(unittest.TestCase):
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
            draw.ellipse(
                (1, 1, size[0] - 2, size[1] - 2),
                fill=fill,
                outline=(20, 20, 20, 255),
                width=2,
            )
        else:
            draw.rectangle(
                (1, 1, size[0] - 2, size[1] - 2),
                fill=fill,
                outline=(20, 20, 20, 255),
                width=2,
            )
        image.save(path)

    def make_rig(self, root: Path, name: str, shirt):
        src = root / f"{name}-parts"
        src.mkdir()
        self.part(src / "body.png", (58, 74), shirt)
        self.part(src / "head.png", (54, 50), (236, 216, 177, 255), "ellipse")
        self.part(src / "arm-l.png", (16, 56), shirt)
        self.part(src / "arm-r.png", (16, 56), shirt)
        self.part(src / "leg-l.png", (18, 50), (55, 75, 132, 255))
        self.part(src / "leg-r.png", (18, 50), (55, 75, 132, 255))
        spec = {
            "schema": puppet_factory.SPEC_SCHEMA,
            "label": name,
            "canvas": {"width": 320, "height": 180, "fps": 12},
            "roomLabel": "ENSEMBLE ROOM",
            "mouthAnchor": {"x": 145, "y": 66, "scale": 0.52, "z": 55},
            "parts": [
                {"id": "leg-left", "role": "leg-left", "source": str(src / "leg-l.png"), "x": 132, "y": 116},
                {"id": "leg-right", "role": "leg-right", "source": str(src / "leg-r.png"), "x": 162, "y": 116},
                {"id": "body", "role": "body", "source": str(src / "body.png"), "x": 130, "y": 74},
                {"id": "arm-left", "role": "arm-left", "source": str(src / "arm-l.png"), "x": 112, "y": 80},
                {"id": "arm-right", "role": "arm-right", "source": str(src / "arm-r.png"), "x": 188, "y": 80},
                {"id": "head", "role": "head", "source": str(src / "head.png"), "x": 132, "y": 26},
            ],
        }
        return puppet_factory.build_rig(spec, root / f"{name}-rig")

    def timing(self):
        track = {
            "schemaVersion": "0.1",
            "id": "ensemble-song",
            "duration": 6.0,
            "gates": [
                {"id": "verse", "at": 0.0, "kind": "verse", "label": "Verse"},
                {"id": "chorus", "at": 3.0, "kind": "chorus", "label": "Chorus"},
            ],
        }
        lyrics = {
            "schema": "full-measure.lyrics.v1",
            "cues": [
                {"start": 0.3, "end": 1.1, "text": "I found the door"},
                {"start": 1.4, "end": 2.2, "text": "you saw it too?"},
                {"start": 3.1, "end": 3.9, "text": "we walk through words"},
                {"start": 4.2, "end": 5.1, "text": "UP AND UP AGAIN"},
            ],
        }
        return scene_growth.normalize_timing(track, lyrics)

    def spec(self, rig_a, rig_b):
        return {
            "schema": ensemble_stage.SPEC_SCHEMA,
            "cast": [
                {
                    "id": "a",
                    "label": "A",
                    "rig": rig_a,
                    "enterAt": 0.0,
                    "exitAt": 6.0,
                },
                {
                    "id": "b",
                    "label": "B",
                    "rig": rig_b,
                    "enterAt": 0.8,
                    "exitAt": 5.5,
                },
            ],
            "dialogue": [
                {"cueIndex": 0, "speakerId": "a", "listenerIds": ["b"]},
                {"cueIndex": 1, "speakerId": "b", "listenerIds": ["a"]},
                {"cueIndex": 2, "speakerId": "a", "listenerIds": ["b"]},
                {"cueIndex": 3, "speakerId": "b", "listenerIds": ["a"]},
            ],
        }

    def build(self, root: Path):
        a = self.make_rig(root, "A", (203, 69, 65, 255))
        b = self.make_rig(root, "B", (67, 119, 190, 255))
        performance = ensemble_stage.compile_ensemble(
            self.spec(a, b),
            self.timing(),
            root / "ensemble",
        )
        return a, b, performance

    def test_dialogue_assigns_mouths_only_to_current_speaker_and_reactions_to_listener(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _a, _b, performance = self.build(root)
            ensemble = performance["ensemble"]
            self.assertEqual(ensemble["castCount"], 2)
            self.assertEqual(ensemble["dialogueTurnCount"], 4)
            speakers = [row["speakerId"] for row in ensemble["dialogueTurns"]]
            self.assertEqual(speakers, ["a", "b", "a", "b"])

            by_cue = {}
            for row in performance["mouthEvents"]:
                by_cue.setdefault(row["cueIndex"], set()).add(row["speakerId"])
            self.assertEqual(by_cue[0], {"a"})
            self.assertEqual(by_cue[1], {"b"})
            self.assertEqual(by_cue[2], {"a"})
            self.assertEqual(by_cue[3], {"b"})

            reactions = ensemble["reactionEvents"]
            self.assertTrue(any(
                row["cueIndex"] == 0 and row["characterId"] == "b"
                for row in reactions
            ))
            self.assertTrue(any(
                row["cueIndex"] == 1 and row["characterId"] == "a"
                for row in reactions
            ))

    def test_eyelines_and_entrance_exit_are_stage_grammar_not_new_rigs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            a, b, performance = self.build(root)
            poses = performance["poseEvents"]
            self.assertTrue(any(
                row["characterId"] == "b"
                and row["cueIndex"] == 0
                and row["role"] == "listener-eyeline"
                for row in poses
            ))
            self.assertTrue(any(
                row["characterId"] == "a"
                and row["cueIndex"] == 1
                and row["role"] == "listener-eyeline"
                for row in poses
            ))

            cast = {row["id"]: row for row in performance["ensemble"]["cast"]}
            self.assertEqual(cast["a"]["rigId"], a["id"])
            self.assertEqual(cast["b"]["rigId"], b["id"])
            self.assertEqual(cast["b"]["enterAt"], 0.8)
            self.assertEqual(cast["b"]["exitAt"], 5.5)

            b_body = next(
                row for row in performance["cutoutPlan"]["layers"]
                if row["id"] == "b--body"
            )
            early = next(row for row in b_body["keyframes"] if row["time"] == 0.0)
            self.assertEqual(early["opacity"], 0.0)
            self.assertTrue(any(
                abs(float(row["time"]) - 0.8) < 1e-6 and row["opacity"] == 1.0
                for row in b_body["keyframes"]
            ))
            self.assertTrue(any(
                abs(float(row["time"]) - 5.5) < 1e-6 and row["opacity"] == 0.0
                for row in b_body["keyframes"]
            ))

    def test_two_character_performance_renders_full_duration_for_zero_provider_cost(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _a, _b, performance = self.build(root)
            receipt = puppet_factory.render_performance(
                performance, root / "ensemble.mp4"
            )
            self.assertTrue(Path(receipt["output"]).is_file())
            self.assertAlmostEqual(receipt["durationSeconds"], 6.0, places=5)
            self.assertEqual(receipt["providerCredits"], 0)
            self.assertEqual(receipt["usdMicros"], 0)
            self.assertGreater(len(performance["mouthEvents"]), 8)
            self.assertGreater(len(performance["ensemble"]["reactionEvents"]), 0)

    def test_paper_director_targets_actual_speaker_listener_and_two_shot_boxes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _a, _b, performance = self.build(root)
            plan = paper_director.plan(
                self.timing(),
                performance=performance,
                max_shot_seconds=2.0,
            )
            cue_shots = {
                row["cueIndex"]: row
                for row in plan["shots"]
                if row.get("cueIndex") is not None
            }
            self.assertEqual(cue_shots[0]["speakerId"], "a")
            self.assertEqual(cue_shots[0]["listenerId"], "b")
            self.assertEqual(cue_shots[1]["speakerId"], "b")
            self.assertEqual(cue_shots[1]["listenerId"], "a")
            self.assertEqual(cue_shots[1]["type"], "REACTION")
            self.assertEqual(cue_shots[3]["type"], "TWO_SHOT")

            speaker_crop = paper_director._crop_for_shot(
                cue_shots[0],
                width=320,
                height=180,
                performance=performance,
                index=0,
            )
            reaction_crop = paper_director._crop_for_shot(
                cue_shots[1],
                width=320,
                height=180,
                performance=performance,
                index=1,
            )
            two_crop = paper_director._crop_for_shot(
                cue_shots[3],
                width=320,
                height=180,
                performance=performance,
                index=3,
            )
            box_a = next(x["box"] for x in performance["ensemble"]["cast"] if x["id"] == "a")
            box_b = next(x["box"] for x in performance["ensemble"]["cast"] if x["id"] == "b")
            center_a = box_a["x"] + box_a["width"] / 2
            center_b = box_b["x"] + box_b["width"] / 2
            speaker_center = speaker_crop["x"] + speaker_crop["w"] / 2
            reaction_center = reaction_crop["x"] + reaction_crop["w"] / 2
            self.assertLess(abs(speaker_center - center_a), abs(speaker_center - center_b))
            self.assertLess(abs(reaction_center - center_a), abs(reaction_center - center_b))
            self.assertLessEqual(two_crop["x"], min(box_a["x"], box_b["x"]))
            self.assertGreaterEqual(
                two_crop["x"] + two_crop["w"],
                max(box_a["x"] + box_a["width"], box_b["x"] + box_b["width"]),
            )

    def test_directed_ensemble_changes_view_without_changing_performance_authority(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _a, _b, performance = self.build(root)
            base = root / "ensemble.mp4"
            base_receipt = puppet_factory.render_performance(performance, base)
            plan = paper_director.plan(
                self.timing(),
                performance=performance,
                max_shot_seconds=1.8,
            )
            directed = root / "ensemble-directed.mp4"
            receipt = paper_director.render(
                base,
                plan,
                directed,
                performance=performance,
            )
            self.assertTrue(directed.is_file())
            self.assertNotEqual(base_receipt["outputSha256"], receipt["outputSha256"])
            self.assertGreaterEqual(receipt["coverageRatio"], 0.99)
            self.assertEqual(receipt["providerCredits"], 0)
            self.assertTrue(any(row["speakerId"] for row in receipt["shots"]))
            self.assertTrue(any(row["listenerId"] for row in receipt["shots"]))
            self.assertTrue(any(row["type"] == "TWO_SHOT" for row in receipt["shots"]))


if __name__ == "__main__":
    unittest.main()
