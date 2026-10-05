import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from haunted_blender.dream_cutout_compiler import KIT_SCHEMA
from haunted_blender.dreambreeder import create_ecology, keep_proposal
from haunted_blender.scene_growth import (
    AWAKENED_RECEIPT_SCHEMA,
    SCENE_SCHEMA,
    awaken_kept_scene,
    grow_kept_scene,
    normalize_timing,
)


class SceneGrowth005Tests(unittest.TestCase):
    def setUp(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("FFmpeg required")
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow required")
        self.Image = Image

    def make_kit(self, root: Path) -> dict:
        bg = root / "bg.png"
        actor = root / "actor.png"
        self.Image.new("RGBA", (96, 64), (30, 35, 50, 255)).save(bg)
        self.Image.new("RGBA", (20, 30), (220, 180, 80, 255)).save(actor)
        return {
            "schema": KIT_SCHEMA,
            "canvas": {"width": 96, "height": 64},
            "layers": [
                {"id": "background", "role": "background", "source": str(bg), "z": 0, "x": 0, "y": 0},
                {"id": "actor", "role": "actor", "source": str(actor), "z": 1, "x": 20, "y": 25},
            ],
        }

    def kept(self):
        ecology = create_ecology(
            relation_id="r5", common_checkpoint_id="c5",
            source_receipt_ids=["ra", "rb"],
        )
        return keep_proposal(ecology, ecology["proposals"][0]["id"])

    def timing(self):
        track = {
            "schemaVersion": "0.1",
            "id": "song-005",
            "duration": 3.0,
            "gates": [
                {"id": "i", "at": 0, "kind": "intro", "label": "arrival"},
                {"id": "v", "at": 0.6, "kind": "verse", "label": "verse"},
                {"id": "c", "at": 1.4, "kind": "chorus", "label": "chorus"},
                {"id": "o", "at": 2.4, "kind": "outro", "label": "out"},
            ],
        }
        lyrics = {
            "schema": "full-measure.lyrics.v1",
            "cues": [
                {"start": 0.7, "end": 1.1, "text": "walking"},
                {"start": 1.5, "end": 1.9, "text": "up then up again"},
            ],
        }
        return normalize_timing(track, lyrics)

    def test_timing_binds_playdeck_gates_and_full_measure_cues(self):
        timing = self.timing()
        self.assertEqual(timing["schema"], "haunted-blender/track-timing/v1")
        self.assertEqual(len(timing["sections"]), 4)
        self.assertEqual(timing["sections"][1]["lyricCueIndices"], [0])
        self.assertEqual(len(timing["awakeningWindows"]), 1)
        self.assertEqual(timing["awakeningWindows"][0]["kind"], "chorus")
        self.assertEqual(timing["awakeningWindows"][0]["authorityClass"], "proposal-only")

    def test_keep_grows_real_longer_scene_without_resolving_performance(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            result = grow_kept_scene(self.kept(), self.timing(), self.make_kit(root), root / "scene", fps=8)
            self.assertEqual(result["scene"]["schema"], SCENE_SCHEMA)
            self.assertEqual(result["scene"]["status"], "deterministic-kept-scene")
            self.assertEqual(len(result["scene"]["segments"]), 4)
            self.assertTrue(Path(result["videoPath"]).is_file())
            self.assertFalse(result["scene"]["distributionAuthorized"])
            self.assertEqual(result["receipt"]["status"], "scoped_complete")

    def test_awakening_replaces_only_verified_bounded_window(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            grown = grow_kept_scene(self.kept(), self.timing(), self.make_kit(root), root / "scene", fps=8)
            accepted = root / "accepted.mp4"
            subprocess.run(
                [
                    "ffmpeg", "-v", "error", "-y",
                    "-f", "lavfi", "-i", "color=c=white:s=96x64:d=2:r=8",
                    "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(accepted),
                ],
                check=True,
            )
            descriptor = {
                "sha256": "a" * 64,
                "acceptanceSha256": "b" * 64,
                "requestSha256": "c" * 64,
                "durationSeconds": 2.0,
            }
            out = root / "awakened.mp4"
            window = grown["scene"]["awakeningWindows"][0]
            with patch(
                "haunted_blender.scene_growth.video_resolver.resolve_accepted_video_for_serve",
                return_value=(descriptor, accepted),
            ):
                result = awaken_kept_scene(
                    root, grown, window["id"], "sha256:" + "a" * 64, out
                )
            self.assertTrue(out.is_file())
            receipt = json.loads(Path(result["receipt"]).read_text())
            self.assertEqual(receipt["schema"], AWAKENED_RECEIPT_SCHEMA)
            self.assertEqual(receipt["awakeningWindowId"], window["id"])
            self.assertFalse(receipt["distributionAuthorized"])


if __name__ == "__main__":
    unittest.main()
