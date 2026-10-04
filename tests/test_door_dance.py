"""A real frame-reordered video and an inspectable door-performance score."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

from haunted_blender import catalog, creative_take, door_dance
from test_scene_artifact import ArtifactBridgeTests


class ScoreTests(unittest.TestCase):
    def test_open_retreat_open_again_is_continuous(self):
        edit = door_dance.score(72)
        frames = edit["source_frame_indices"]
        self.assertEqual((edit["hinge_frame"], edit["retreat_frame"]), (36, 26))
        self.assertEqual(len(frames), 98)
        self.assertEqual(frames[36:43], [36, 36, 36, 36, 36, 35, 34])
        self.assertEqual(frames[49:55], [27, 26, 26, 26, 27, 28])
        self.assertEqual(frames[-1], 71)
        self.assertEqual([p["action"] for p in edit["phases"]],
                         ["open_partway", "pause_partway", "close_a_little",
                          "pause_reclosed", "open_again"])
        self.assertTrue(all(abs(a - b) <= 1 for a, b in zip(frames, frames[1:])))


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
class AcceptedDoorDanceTests(unittest.TestCase):
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
                                       provider_job_id="synthetic-hinge-test")
        self.acceptance = creative_take.accept(self.root, request["request"], admitted["video"],
                                                filmmaker_approval=True)
        self.source = Path(admitted["video"])
        self.source_sha = catalog.digest_file(self.source)
        self.out = self.root / "renders" / "door-dances" / "synthetic-hinge.mp4"

    def test_real_dance_frame_count_receipt_and_source_survival(self):
        result = door_dance.render(self.root, self.artifact["snapshot"],
                                   self.acceptance["acceptance"], self.out)
        receipt = json.loads(Path(result["receipt"]).read_text())
        self.assertEqual(receipt["source_video_sha256"], self.source_sha)
        self.assertEqual(receipt["output_sha256"], catalog.digest_file(self.out))
        self.assertEqual(receipt["source_sample_count"], 12)
        self.assertEqual(receipt["output_frame_count"], len(receipt["edit"]["source_frame_indices"]))
        probe = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
                                "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0",
                                str(self.out)], capture_output=True, text=True, check=True)
        self.assertEqual(int(probe.stdout.strip()), receipt["output_frame_count"])
        self.assertEqual(catalog.digest_file(self.source), self.source_sha)
        with self.assertRaisesRegex(ValueError, "overwrite"):
            door_dance.render(self.root, self.artifact["snapshot"],
                              self.acceptance["acceptance"], self.out)

    def test_changed_source_refused_before_output(self):
        self.source.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "changed"):
            door_dance.render(self.root, self.artifact["snapshot"],
                              self.acceptance["acceptance"], self.out)
        self.assertFalse(self.out.exists())


if __name__ == "__main__":
    unittest.main()
