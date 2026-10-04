"""A real local time-slice render from an accepted synthetic moving take."""
import hashlib
import json
import shutil
import subprocess
import unittest
from pathlib import Path

from haunted_blender import catalog, creative_take, time_slice
from test_scene_artifact import ArtifactBridgeTests


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
class TimeSliceTests(unittest.TestCase):
    def setUp(self):
        ArtifactBridgeTests.setUp(self)
        self.artifact = ArtifactBridgeTests.accept(self, self.choices[:1])
        clip = Path(self.temp.name) / "synthetic-motion.mp4"
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i",
                        "testsrc2=s=320x180:r=24", "-t", "3", "-c:v", "mpeg4", str(clip)],
                       check=True, capture_output=True)
        request = creative_take.request(self.root, self.artifact["snapshot"], 0,
                                        "Synthetic moving door texture.",
                                        synthetic_source=True, disclose_to_provider=True)
        admitted = creative_take.admit(self.root, request["request"], clip,
                                       provider_job_id="synthetic-local-test")
        self.acceptance = creative_take.accept(self.root, request["request"], admitted["video"],
                                                filmmaker_approval=True)
        self.clip = Path(admitted["video"])
        self.source_sha = catalog.digest_file(self.clip)
        self.out = self.root / "renders" / "time-slices" / "synthetic-door.png"

    def test_real_image_receipt_source_survival_and_overwrite_refusal(self):
        result = time_slice.render(self.root, self.artifact["snapshot"],
                                   self.acceptance["acceptance"], self.out)
        image = self.out.read_bytes()
        self.assertTrue(image.startswith(b"\x89PNG\r\n\x1a\n"))
        receipt = json.loads(Path(result["receipt"]).read_text())
        self.assertEqual(receipt["source_video_sha256"], self.source_sha)
        self.assertEqual(receipt["output_sha256"], hashlib.sha256(image).hexdigest())
        self.assertEqual(receipt["sample_count"], 24)
        self.assertEqual(len(receipt["strips"]), 32)
        self.assertEqual([x["x_start"] for x in receipt["strips"]], list(range(0, 320, 10)))
        self.assertEqual(receipt["strips"][-1]["sample_index"], 23)
        self.assertEqual(catalog.digest_file(self.clip), self.source_sha)
        with self.assertRaisesRegex(ValueError, "overwrite"):
            time_slice.render(self.root, self.artifact["snapshot"],
                              self.acceptance["acceptance"], self.out)

    def test_tampered_source_refused_before_output(self):
        self.clip.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "changed"):
            time_slice.render(self.root, self.artifact["snapshot"],
                              self.acceptance["acceptance"], self.out)
        self.assertFalse(self.out.exists())


if __name__ == "__main__":
    unittest.main()
