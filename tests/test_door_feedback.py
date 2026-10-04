"""Motion feedback is recursive, and an accepted synthetic take stays intact."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

from haunted_blender import catalog, creative_take, door_feedback
from test_scene_artifact import ArtifactBridgeTests


class RecursionTests(unittest.TestCase):
    def test_shifted_trace_survives_after_motion_ends(self):
        frame_bytes = door_feedback.WIDTH * door_feedback.HEIGHT * 3
        first = bytearray(frame_bytes)
        second = bytearray(frame_bytes)
        x, y = 30, 30
        second[(y * door_feedback.WIDTH + x) * 3] = 200
        output = door_feedback._echo_frames(bytes(first + second + first))
        self.assertEqual(output[:frame_bytes], first)
        shifted = (((y + door_feedback.SHIFT_Y) * door_feedback.WIDTH +
                    x + door_feedback.SHIFT_X) * 3)
        self.assertGreater(output[2 * frame_bytes + shifted + 2], 0)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
class AcceptedDoorFeedbackTests(unittest.TestCase):
    def setUp(self):
        ArtifactBridgeTests.setUp(self)
        self.artifact = ArtifactBridgeTests.accept(self, self.choices[:1])
        source = Path(self.temp.name) / "synthetic-motion.mp4"
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i",
                        "testsrc2=s=320x180:r=24", "-t", "0.5", "-c:v", "mpeg4", str(source)],
                       check=True, capture_output=True)
        request = creative_take.request(self.root, self.artifact["snapshot"], 0,
                                        "Synthetic moving door texture.",
                                        synthetic_source=True, disclose_to_provider=True)
        admitted = creative_take.admit(self.root, request["request"], source,
                                       provider_job_id="synthetic-echo-test")
        self.acceptance = creative_take.accept(self.root, request["request"], admitted["video"],
                                                filmmaker_approval=True)
        self.source = Path(admitted["video"])
        self.source_sha = catalog.digest_file(self.source)
        self.out = self.root / "renders" / "door-feedback" / "synthetic-echo.mp4"

    def test_real_video_receipt_and_source_survival(self):
        result = door_feedback.render(self.root, self.artifact["snapshot"],
                                      self.acceptance["acceptance"], self.out)
        receipt = json.loads(Path(result["receipt"]).read_text())
        self.assertEqual(receipt["source_video_sha256"], self.source_sha)
        self.assertEqual(receipt["output_sha256"], catalog.digest_file(self.out))
        self.assertEqual(receipt["sample_count"], 6)
        self.assertFalse(receipt["hydra_engine_executed"])
        self.assertEqual(catalog.digest_file(self.source), self.source_sha)
        with self.assertRaisesRegex(ValueError, "overwrite"):
            door_feedback.render(self.root, self.artifact["snapshot"],
                                 self.acceptance["acceptance"], self.out)

    def test_changed_parent_refused_before_output(self):
        self.source.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "changed"):
            door_feedback.render(self.root, self.artifact["snapshot"],
                                 self.acceptance["acceptance"], self.out)
        self.assertFalse(self.out.exists())


if __name__ == "__main__":
    unittest.main()
