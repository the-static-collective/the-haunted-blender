"""Execute a moving shot between frozen static beats and check its actual frames."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

from haunted_blender import catalog, creative_take, scene_artifact, take_cut
from test_scene_artifact import ArtifactBridgeTests


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg unavailable")
class TakeCutTests(unittest.TestCase):
    def setUp(self):
        ArtifactBridgeTests.setUp(self)
        self.artifact = ArtifactBridgeTests.accept(self)
        req = creative_take.request(self.root, self.artifact["snapshot"], 1,
                                    "Synthetic moving patterns; no people.",
                                    synthetic_source=True, disclose_to_provider=True)
        self.request = req["request"]
        source = Path(self.temp.name) / "moving.mp4"
        subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-f", "lavfi", "-i",
                        "testsrc2=s=320x180:r=24", "-t", "1", "-c:v", "mpeg4", str(source)],
                       check=True)
        admitted = creative_take.admit(self.root, req["request"], source,
                                       provider_job_id="fixture-video-job-001")
        self.video = Path(admitted["video"])
        self.acceptance = Path(creative_take.accept(self.root, req["request"], self.video,
                                                     filmmaker_approval=True)["acceptance"])

    def _frame(self, movie, at):
        result = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-ss", str(at),
                                 "-i", str(movie), "-frames:v", "1", "-f", "rawvideo",
                                 "-pix_fmt", "rgb24", "-"], check=True, capture_output=True)
        return result.stdout

    def _mean_pixel_delta(self, first, second):
        self.assertEqual(len(first), len(second))
        return sum(abs(a - b) for a, b in zip(first, second)) / len(first)

    def test_render_has_motion_in_selected_beat_and_stillness_elsewhere(self):
        out = self.root / "renders" / "take-cut.mp4"
        result = take_cut.render(self.root, self.artifact["snapshot"], self.acceptance, out)
        receipt = json.loads(Path(result["receipt"]).read_text())
        self.assertEqual([s["kind"] for s in receipt["shots"]],
                         ["static_still", "accepted_video_take", "static_still"])
        self.assertEqual(receipt["output_sha256"], catalog.digest_file(out))
        self.assertFalse(receipt["distribution_authorized"])
        self.assertEqual(receipt["sound"], "omitted for this silent private preview")
        # Re-encoding a still can add sub-pixel codec noise; measure image change.
        self.assertLess(self._mean_pixel_delta(self._frame(out, 0.1), self._frame(out, 0.7)), 0.2)
        self.assertGreater(self._mean_pixel_delta(self._frame(out, 2.0), self._frame(out, 2.5)), 3)
        self.assertLess(self._mean_pixel_delta(self._frame(out, 3.0), self._frame(out, 3.5)), 0.2)
        with self.assertRaisesRegex(ValueError, "overwrite"):
            take_cut.render(self.root, self.artifact["snapshot"], self.acceptance, out)

    def test_stale_take_and_wrong_scene_refuse_before_rendering(self):
        second = scene_artifact.accept(self.root, self.world_snapshot,
                                       self.alchemy_snapshot, self.choices[:2],
                                       filmmaker_approval=True)
        with self.assertRaisesRegex(ValueError, "different Scene Artifact"):
            take_cut.render(self.root, second["snapshot"], self.acceptance,
                            self.root / "renders" / "wrong.mp4")
        self.video.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "take video"):
            take_cut.render(self.root, self.artifact["snapshot"], self.acceptance,
                            self.root / "renders" / "stale.mp4")
        self.assertFalse((self.root / "renders" / "stale.mp4").exists())


if __name__ == "__main__":
    unittest.main()
