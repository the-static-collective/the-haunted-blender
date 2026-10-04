"""Memory residue uses pixels actually seen by one camera/I-eye."""
import copy
import json
import shutil
import subprocess
import unittest
from pathlib import Path

from haunted_blender import (
    catalog, creative_take, memory_feedback, observer_local,
)
from test_scene_artifact import ArtifactBridgeTests


WORLD = {
    "id": "world-memory-feedback-test",
    "beats": [{"id": "beat-0", "index": 0}],
    "facts": [
        {"id": "fact-room", "since_beat": 0},
        {"id": "fact-figure", "since_beat": 0},
    ],
}
EYE = {
    "id": "eye-threshold",
    "position": "threshold",
    "access_fact_ids": ["fact-room"],
    "focus_fact_ids": ["fact-figure"],
    "threshold_rules": [
        {"threshold_id": "door-main", "fact_id": "fact-figure", "min_open": 0.4}
    ],
}
REGIONS = {"fact-figure": [0.20, 0.20, 0.50, 0.70]}


def projections():
    visible = observer_local.project(
        WORLD, 0, EYE, {"door-main": 0.70})
    residue = observer_local.project(
        WORLD, 0, EYE, {"door-main": 0.10}, visible["memory_receipt"])
    return visible, residue


class MemoryFrameTests(unittest.TestCase):
    def test_seen_pixels_persist_then_decay_after_occlusion(self):
        visible, residue = projections()
        frame_bytes = memory_feedback.WIDTH * memory_feedback.HEIGHT * 3
        first = bytearray(frame_bytes)
        x0, y0, x1, y1 = memory_feedback._normalize_regions(REGIONS)["fact-figure"]["pixels"]
        for y in range(y0, y1):
            for x in range(x0, x1):
                p = (y * memory_feedback.WIDTH + x) * 3
                first[p:p + 3] = bytes((180, 160, 220))
        black = bytearray(frame_bytes)
        source = bytes(first + black + black + black)
        timeline = [
            {"start_frame": 0, "end_frame_exclusive": 1, "projection": visible},
            {"start_frame": 1, "end_frame_exclusive": 4, "projection": residue},
        ]
        compiled = memory_feedback._compile_timeline(4, timeline, REGIONS)
        output, stats = memory_feedback._memory_frames(source, compiled)
        self.assertEqual(output[:frame_bytes], bytes(first))
        totals = [
            sum(output[i * frame_bytes:(i + 1) * frame_bytes])
            for i in range(4)
        ]
        self.assertGreater(totals[1], totals[3])
        self.assertGreater(totals[3], 0)
        self.assertEqual(stats["fact-figure"]["captured_frames"], 1)
        self.assertEqual(stats["fact-figure"]["residue_frames"], 3)
        self.assertEqual(stats["fact-figure"]["max_residue_age"], 3)

    def test_receipt_does_not_magic_pixels_into_memory(self):
        visible, residue = projections()
        timeline = [
            {"start_frame": 0, "end_frame_exclusive": 2, "projection": residue}
        ]
        compiled = memory_feedback._compile_timeline(2, timeline, REGIONS)
        frame_bytes = memory_feedback.WIDTH * memory_feedback.HEIGHT * 3
        with self.assertRaisesRegex(ValueError, "no on-timeline visual capture"):
            memory_feedback._memory_frames(bytes(frame_bytes * 2), compiled)

    def test_tampered_projection_is_refused(self):
        visible, _ = projections()
        forged = copy.deepcopy(visible)
        forged["visible_fact_ids"] = []
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            memory_feedback._compile_timeline(
                1,
                [{"start_frame": 0, "end_frame_exclusive": 1,
                  "projection": forged}],
                REGIONS,
            )


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
class AcceptedMemoryFeedbackTests(unittest.TestCase):
    def setUp(self):
        ArtifactBridgeTests.setUp(self)
        self.artifact = ArtifactBridgeTests.accept(self, self.choices[:1])
        source = Path(self.temp.name) / "synthetic-memory.mp4"
        subprocess.run(
            ["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i",
             "testsrc2=s=320x180:r=24", "-t", "1.0", "-c:v", "mpeg4", str(source)],
            check=True, capture_output=True,
        )
        request = creative_take.request(
            self.root, self.artifact["snapshot"], 0,
            "Synthetic observer-local doorway memory texture.",
            synthetic_source=True, disclose_to_provider=True)
        admitted = creative_take.admit(
            self.root, request["request"], source,
            provider_job_id="synthetic-memory-feedback-test")
        self.acceptance = creative_take.accept(
            self.root, request["request"], admitted["video"],
            filmmaker_approval=True)
        self.source = Path(admitted["video"])
        self.source_sha = catalog.digest_file(self.source)
        self.out = self.root / "renders" / "memory-feedback" / "synthetic-memory.mp4"

    def test_real_video_memory_receipt_and_source_survival(self):
        visible, residue = projections()
        timeline = [
            {"start_frame": 0, "end_frame_exclusive": 5, "projection": visible},
            {"start_frame": 5, "end_frame_exclusive": 12, "projection": residue},
        ]
        result = memory_feedback.render(
            self.root, self.artifact["snapshot"], self.acceptance["acceptance"],
            timeline, REGIONS, self.out)
        receipt = json.loads(Path(result["receipt"]).read_text())
        self.assertEqual(receipt["source_video_sha256"], self.source_sha)
        self.assertEqual(receipt["output_sha256"], catalog.digest_file(self.out))
        self.assertEqual(receipt["sample_count"], 12)
        self.assertEqual(receipt["observer_id"], "eye-threshold")
        self.assertEqual(receipt["residue_fact_ids"], ["fact-figure"])
        stats = receipt["memory_statistics"]["fact-figure"]
        self.assertEqual(stats["captured_frames"], 5)
        self.assertEqual(stats["residue_frames"], 7)
        self.assertEqual(catalog.digest_file(self.source), self.source_sha)
        with self.assertRaisesRegex(ValueError, "overwrite"):
            memory_feedback.render(
                self.root, self.artifact["snapshot"], self.acceptance["acceptance"],
                timeline, REGIONS, self.out)


if __name__ == "__main__":
    unittest.main()
