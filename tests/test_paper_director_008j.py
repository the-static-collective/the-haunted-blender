import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from haunted_blender import paper_director, scene_growth


class PaperDirector008jTests(unittest.TestCase):
    def setUp(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("FFmpeg required")

    def timing(self):
        track = {
            "schemaVersion": "0.1",
            "id": "director-song",
            "duration": 8.0,
            "gates": [
                {"id": "intro", "at": 0.0, "kind": "intro", "label": "Intro"},
                {"id": "verse", "at": 0.8, "kind": "verse", "label": "Verse"},
                {"id": "chorus", "at": 3.0, "kind": "chorus", "label": "Chorus"},
                {"id": "bridge", "at": 6.0, "kind": "bridge", "label": "Bridge"},
            ],
        }
        lyrics = {
            "schema": "full-measure.lyrics.v1",
            "cues": [
                {"start": 0.25, "end": 0.70, "text": "hello room"},
                {"start": 0.95, "end": 1.75, "text": "I was down in the dust"},
                {"start": 2.05, "end": 2.65, "text": "you see this?"},
                {"start": 3.10, "end": 4.10, "text": "UP AND UP AGAIN!"},
                {"start": 4.45, "end": 5.20, "text": "the television knows"},
                {"start": 6.10, "end": 6.95, "text": "walk through the words"},
                {"start": 7.15, "end": 7.75, "text": "and return"},
            ],
        }
        return scene_growth.normalize_timing(track, lyrics)

    def performance(self):
        return {
            "schema": "haunted-blender/puppet-performance/v1",
            "id": "puppet-performance:director-test",
            "movingInsertPlan": {
                "schema": "haunted-blender/moving-insert-plan/v1",
                "id": "moving-insert-plan:director-test",
                "canvas": {
                    "width": 320,
                    "height": 180,
                    "fps": 12,
                    "durationSeconds": 8.0,
                },
                "inserts": [
                    {
                        "id": "moving-insert-001",
                        "role": "television",
                        "start": 0.0,
                        "end": 8.0,
                        "box": {
                            "x": 26,
                            "y": 24,
                            "width": 80,
                            "height": 49,
                            "border": 6,
                        },
                    }
                ],
            },
        }

    def doctor(self):
        return {
            "schema": "haunted-blender/weakest-window-report/v1",
            "id": "weak-report:director-test",
            "windows": [
                {
                    "id": "window-0001",
                    "start": 0.0,
                    "end": 3.0,
                    "weaknessScore": 0.30,
                    "dominantWeakness": "noveltyDeficit",
                },
                {
                    "id": "window-0002",
                    "start": 3.0,
                    "end": 5.5,
                    "weaknessScore": 0.91,
                    "dominantWeakness": "stasis",
                },
                {
                    "id": "window-0003",
                    "start": 5.5,
                    "end": 8.0,
                    "weaknessScore": 0.44,
                    "dominantWeakness": "transitionJolt",
                },
            ],
            "ranking": ["window-0002", "window-0003", "window-0001"],
            "coverageRatio": 1.0,
            "meanWeakness": 0.55,
        }

    def make_video(self, path: Path, *, duration=8.0, audio=True):
        args = [
            "ffmpeg", "-v", "error", "-y",
            "-f", "lavfi", "-i", f"testsrc2=s=320x180:r=12:d={duration}",
        ]
        if audio:
            args += [
                "-f", "lavfi", "-i",
                f"sine=frequency=330:sample_rate=44100:duration={duration}",
                "-shortest",
            ]
        args += [
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
        ]
        if audio:
            args += ["-c:a", "aac"]
        else:
            args += ["-an"]
        args += [str(path)]
        subprocess.run(args, check=True)

    def has_audio(self, path: Path) -> bool:
        proc = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "a:0",
                "-show_entries", "stream=index",
                "-of", "csv=p=0",
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return bool(proc.stdout.strip())

    def test_plan_covers_whole_song_with_diverse_nonrepeating_shot_grammar(self):
        timing = self.timing()
        plan = paper_director.plan(
            timing,
            performance=self.performance(),
            doctor_report=self.doctor(),
            max_shot_seconds=2.0,
        )
        self.assertEqual(plan["coverageRatio"], 1.0)
        self.assertAlmostEqual(plan["coverageSeconds"], 8.0, places=5)
        self.assertGreater(plan["shotCount"], 6)
        self.assertGreaterEqual(len(plan["shotTypeCounts"]), 4)
        self.assertLessEqual(
            max(float(row["durationSeconds"]) for row in plan["shots"]),
            2.000001,
        )
        for left, right in zip(plan["shots"], plan["shots"][1:]):
            self.assertNotEqual(left["type"], right["type"])
            self.assertAlmostEqual(float(left["end"]), float(right["start"]), places=5)
        self.assertAlmostEqual(float(plan["shots"][0]["start"]), 0.0, places=5)
        self.assertAlmostEqual(float(plan["shots"][-1]["end"]), 8.0, places=5)

    def test_doctor_can_turn_weak_window_into_existing_insert_closeup(self):
        plan = paper_director.plan(
            self.timing(),
            performance=self.performance(),
            doctor_report=self.doctor(),
            max_shot_seconds=2.5,
        )
        insert_shots = [row for row in plan["shots"] if row["type"] == "INSERT"]
        self.assertGreater(len(insert_shots), 0)
        target = next(
            row for row in insert_shots
            if row.get("weakWindowId") == "window-0002"
        )
        self.assertEqual(target["insertId"], "moving-insert-001")
        crop = paper_director._crop_for_shot(
            target,
            width=320,
            height=180,
            performance=self.performance(),
            index=0,
        )
        # Crop must contain the frozen television box plus bezel padding.
        self.assertLessEqual(crop["x"], 26)
        self.assertLessEqual(crop["y"], 24)
        self.assertGreaterEqual(crop["w"], 80)
        self.assertGreaterEqual(crop["h"], 49)

    def test_section_and_punctuation_grammar_create_expected_view_changes(self):
        plan = paper_director.plan(
            self.timing(),
            performance=self.performance(),
            max_shot_seconds=3.0,
        )
        cue_types = {
            row.get("cueIndex"): row["type"]
            for row in plan["shots"]
            if row.get("cueIndex") is not None
        }
        self.assertEqual(cue_types[2], "REACTION")
        self.assertEqual(cue_types[3], "CLOSE_UP")
        # Bridge cue is intentionally directed into lyric-world/reaction/close grammar.
        self.assertIn(cue_types[5], {"LYRIC_WORLD", "REACTION", "CLOSE_UP"})

    def test_render_changes_view_preserves_duration_and_base_audio(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            base = root / "base.mp4"
            self.make_video(base, duration=8.0, audio=True)
            plan = paper_director.plan(
                self.timing(),
                performance=self.performance(),
                doctor_report=self.doctor(),
                max_shot_seconds=2.0,
            )
            out = root / "directed.mp4"
            receipt = paper_director.render(
                base,
                plan,
                out,
                performance=self.performance(),
            )
            self.assertTrue(out.is_file())
            self.assertNotEqual(receipt["baseSha256"], receipt["outputSha256"])
            self.assertGreaterEqual(receipt["coverageRatio"], 0.99)
            self.assertGreaterEqual(receipt["durationSeconds"], 7.94)
            self.assertTrue(self.has_audio(out))
            self.assertEqual(receipt["audioAuthority"], "base-performance-only")
            self.assertEqual(receipt["shotCount"], plan["shotCount"])
            self.assertEqual(receipt["providerCredits"], 0)
            self.assertEqual(receipt["usdMicros"], 0)
            self.assertTrue(any(
                row["crop"]["w"] < 320 or row["crop"]["h"] < 180
                for row in receipt["shots"]
            ))

    def test_no_audio_base_remains_valid_directed_movie(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            base = root / "silent.mp4"
            self.make_video(base, duration=8.0, audio=False)
            plan = paper_director.plan(
                self.timing(),
                performance=self.performance(),
                max_shot_seconds=2.2,
            )
            receipt = paper_director.render(
                base,
                plan,
                root / "directed-silent.mp4",
                performance=self.performance(),
            )
            self.assertGreaterEqual(receipt["coverageRatio"], 0.99)
            self.assertFalse(self.has_audio(Path(root / "directed-silent.mp4")))
            self.assertEqual(receipt["externalGenerations"], 0)


if __name__ == "__main__":
    unittest.main()
