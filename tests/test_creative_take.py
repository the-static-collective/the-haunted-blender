"""A real local MP4 can become a candidate take, without becoming story authority."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from haunted_blender import creative_take
from test_scene_artifact import ArtifactBridgeTests


class CreativeTakeTests(unittest.TestCase):
    def setUp(self):
        ArtifactBridgeTests.setUp(self)
        self.artifact = ArtifactBridgeTests.accept(self)

    def request(self):
        return creative_take.request(self.root, self.artifact["snapshot"], 0,
                                     "The synthetic red field slowly shifts; fixed camera.",
                                     synthetic_source=True, disclose_to_provider=True)

    def test_disclosure_is_separate_from_accepted_local_preview(self):
        with self.assertRaisesRegex(ValueError, "disclosure approval"):
            creative_take.request(self.root, self.artifact["snapshot"], 0, "Move")
        with self.assertRaisesRegex(ValueError, "accepted shot"):
            creative_take.request(self.root, self.artifact["snapshot"], 8, "Move",
                                  synthetic_source=True, disclose_to_provider=True)
        req = self.request()
        self.assertEqual(req["frame_sha256"],
                         json.loads(Path(self.artifact["snapshot"]).read_text())["shots"][0]["frame_sha256"])
        self.assertEqual(self.request(), req)
        (self.photos / "cup.png").write_bytes(b"changed source")
        with self.assertRaisesRegex(ValueError, "Frozen source missing or changed"):
            creative_take.load_request(self.root, req["request"])

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg unavailable")
    def test_local_movie_is_candidate_until_separately_accepted(self):
        req = self.request()
        movie = Path(self.temp.name) / "provider-result.mp4"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i",
                        "color=c=red:s=320x180:r=24", "-t", "0.5", "-c:v", "mpeg4",
                        str(movie)], check=True)
        admitted = creative_take.admit(self.root, req["request"], movie,
                                       provider_job_id="sample-job-0001")
        receipt = json.loads(Path(admitted["receipt"]).read_text())
        self.assertEqual(receipt["status"], "candidate_admitted_not_filmmaker_accepted")
        self.assertFalse(receipt["provider_execution_independently_verified"])
        self.assertFalse(receipt["distribution_authorized"])
        self.assertNotEqual(Path(admitted["video"]), movie)
        with self.assertRaisesRegex(ValueError, "filmmaker acceptance"):
            creative_take.accept(self.root, req["request"], admitted["video"])
        accepted = creative_take.accept(self.root, req["request"], admitted["video"],
                                        filmmaker_approval=True)
        witness = json.loads(Path(accepted["acceptance"]).read_text())
        self.assertEqual(witness["artifact_sha256"], self.artifact["sha256"])
        with self.assertRaisesRegex(ValueError, "overwrite"):
            creative_take.admit(self.root, req["request"], movie,
                                provider_job_id="sample-job-0001")
        Path(admitted["video"]).write_bytes(b"corrupted")
        with self.assertRaisesRegex(ValueError, "lineage changed"):
            creative_take.accept(self.root, req["request"], admitted["video"],
                                 filmmaker_approval=True)

    @unittest.skipUnless(shutil.which("ffprobe"), "ffprobe unavailable")
    def test_arbitrary_mp4_extension_is_not_evidence_of_video(self):
        req = self.request()
        bad = Path(self.temp.name) / "bogus.mp4"
        bad.write_bytes(b"this is not video")
        with self.assertRaises((ValueError, subprocess.CalledProcessError)):
            creative_take.admit(self.root, req["request"], bad,
                                provider_job_id="sample-job-0002")


if __name__ == "__main__":
    unittest.main()
