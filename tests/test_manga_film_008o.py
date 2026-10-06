import json
import shutil
import tempfile
import unittest
from pathlib import Path

from haunted_blender import manga_film, narrative_performance


FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "specimens"
    / "008n"
    / "bus-page-5-a-page-you-can-hear-001.json"
)


class PageFiveMangaFilm008oTests(unittest.TestCase):
    def setUp(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("FFmpeg and FFprobe required")
        try:
            from PIL import Image  # noqa: F401
        except ImportError:
            self.skipTest("Pillow required")

    def spec(self):
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_audio_plan_is_deterministic_and_hash_bound(self):
        bundle=narrative_performance.compile_spec(self.spec())
        a=manga_film.audio_plan(bundle["plan"])
        b=manga_film.audio_plan(bundle["plan"])
        self.assertEqual(a,b)
        self.assertEqual(len(a["events"]),8)
        by_beat={row["id"]:row for row in bundle["plan"]["beats"]}
        for event in a["events"]:
            self.assertEqual(
                event["sourceParticularHash"],
                by_beat[event["beatId"]]["sourceParticularHash"],
            )

    def test_page_five_renders_an_actual_audio_video_descendant(self):
        with tempfile.TemporaryDirectory() as td:
            result=manga_film.render_spec(
                self.spec(),Path(td)/"render",width=480,height=270,fps=10
            )
            movie=Path(result["movie"])
            receipt=result["receipt"]
            self.assertTrue(movie.is_file())
            self.assertGreater(movie.stat().st_size,1000)
            self.assertEqual(receipt["schema"],manga_film.RECEIPT_SCHEMA)
            self.assertEqual(receipt["beatCount"],8)
            self.assertEqual(receipt["externalGenerations"],0)
            self.assertEqual(receipt["providerCredits"],0)
            self.assertEqual(receipt["usdMicros"],0)
            self.assertTrue(receipt["hasAudio"])
            self.assertGreaterEqual(receipt["durationSeconds"],6.70)
            self.assertLessEqual(receipt["durationSeconds"],6.90)
            self.assertEqual(len(receipt["outputSha256"]),64)

    def test_every_visible_beat_keeps_the_008n_source_hash(self):
        with tempfile.TemporaryDirectory() as td:
            spec=self.spec()
            bundle=narrative_performance.compile_spec(spec)
            result=manga_film.render_spec(
                spec,Path(td)/"render",width=400,height=240,fps=8
            )
            expected={
                row["id"]:row["sourceParticularHash"]
                for row in bundle["plan"]["beats"]
            }
            observed={
                row["beatId"]:row["sourceParticularHash"]
                for row in result["receipt"]["beats"]
            }
            self.assertEqual(observed,expected)
            self.assertTrue(all(row["firstFrame"]<=row["lastFrame"] for row in result["receipt"]["beats"]))

    def test_partial_admission_yields_only_admitted_visible_beats(self):
        with tempfile.TemporaryDirectory() as td:
            spec=self.spec()
            spec["admittedBeatIds"]=["beat-01","beat-07","beat-08"]
            result=manga_film.render_spec(
                spec,Path(td)/"render",width=400,height=240,fps=8
            )
            self.assertEqual(
                [row["beatId"] for row in result["receipt"]["beats"]],
                ["beat-01","beat-07","beat-08"],
            )
            self.assertEqual(result["receipt"]["beatCount"],3)

    def test_audio_is_declared_derived_not_source_recording(self):
        bundle=narrative_performance.compile_spec(self.spec())
        audio=manga_film.audio_plan(bundle["plan"])
        self.assertEqual(audio["authority"],"derived-performance-sound-only")
        self.assertIn("SYNTHESIZED SOUND != SOURCE RECORDING",audio["laws"])


if __name__=="__main__":
    unittest.main()
