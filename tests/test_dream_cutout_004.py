import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from haunted_blender.dream_cutout_compiler import (
    COMPILED_SCHEMA,
    KIT_SCHEMA,
    SIXUP_SCHEMA,
    compile_proposal,
    render_sixup,
)
from haunted_blender.dreambreeder import create_ecology


class DreamCutout004Tests(unittest.TestCase):
    def setUp(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("FFmpeg and FFprobe required")
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            self.skipTest("Pillow required")
        self.Image = Image
        self.ImageDraw = ImageDraw

    def make_kit(self, root: Path) -> dict:
        bg = root / "bg.png"
        actor = root / "actor.png"
        arm = root / "arm.png"
        light = root / "light.png"
        self.Image.new("RGBA", (96, 64), (30, 35, 50, 255)).save(bg)
        self.Image.new("RGBA", (20, 32), (220, 180, 80, 255)).save(actor)
        arm_img = self.Image.new("RGBA", (16, 8), (0, 0, 0, 0))
        self.ImageDraw.Draw(arm_img).rectangle((0, 1, 15, 6), fill=(240, 210, 120, 255))
        arm_img.save(arm)
        self.Image.new("RGBA", (26, 26), (255, 230, 150, 100)).save(light)
        return {
            "schema": KIT_SCHEMA,
            "canvas": {"width": 96, "height": 64},
            "donorScale": 0.2,
            "layers": [
                {"id": "background", "role": "background", "source": str(bg), "z": 0, "x": 0, "y": 0},
                {"id": "light", "role": "light", "source": str(light), "z": 1, "x": 66, "y": 2, "opacity": 0.35},
                {"id": "actor", "role": "actor", "source": str(actor), "z": 2, "x": 18, "y": 24},
                {"id": "arm", "role": "arm-right", "source": str(arm), "z": 3, "x": 32, "y": 34},
            ],
        }

    def make_donor(self, path: Path) -> None:
        subprocess.run(
            [
                "ffmpeg", "-v", "error", "-y",
                "-f", "lavfi", "-i", "testsrc2=s=64x48:d=0.5:r=8",
                "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path),
            ],
            check=True,
        )

    def ecology(self, donor_ids=None):
        return create_ecology(
            relation_id="relation-004",
            common_checkpoint_id="checkpoint-004",
            source_receipt_ids=["receipt-a", "receipt-b"],
            donor_ids=donor_ids or [],
        )

    def test_compile_proposal_is_preview_not_keep(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            kit = self.make_kit(root)
            ecology = self.ecology()
            proposal = ecology["proposals"][0]
            compiled = compile_proposal(ecology, proposal["id"], kit, duration=0.5, fps=8)
            self.assertEqual(compiled["schema"], COMPILED_SCHEMA)
            self.assertEqual(compiled["authorityClass"], "proposal-preview")
            self.assertEqual(compiled["cutoutPlan"]["schema"], "haunted-blender/cutout-stage/v1")
            self.assertEqual(compiled["cutoutPlan"]["canvas"]["duration"], 0.5)
            self.assertIsNone(ecology["disposition"])
            self.assertIn("PREVIEW != KEEP", compiled["laws"])

    def test_motion_grammar_changes_real_keyframes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            kit = self.make_kit(root)
            ecology = self.ecology()
            fingerprints = []
            for proposal in ecology["proposals"]:
                compiled = compile_proposal(ecology, proposal["id"], kit, duration=0.5, fps=8)
                actor = next(layer for layer in compiled["cutoutPlan"]["layers"] if layer["id"] == "actor")
                fingerprints.append(json.dumps(actor["keyframes"], sort_keys=True))
            self.assertGreaterEqual(len(set(fingerprints)), 3)

    def test_six_unborn_movies_render_and_contact_sheet_is_not_history(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            kit = self.make_kit(root)
            donor_id = "flow-video:test-donor"
            donor = root / "donor.mp4"
            self.make_donor(donor)
            ecology = self.ecology([donor_id])

            out = root / "sixup"
            result = render_sixup(
                ecology,
                kit,
                out,
                duration=0.5,
                fps=8,
                donor_video_by_id={donor_id: str(donor)},
            )
            self.assertEqual(result["schema"], SIXUP_SCHEMA)
            self.assertEqual(result["authorityClass"], "proposal-preview")
            self.assertEqual(len(result["previews"]), 6)
            self.assertTrue(Path(result["contactSheetVideo"]).is_file())
            self.assertGreater(Path(result["contactSheetVideo"]).stat().st_size, 0)
            self.assertTrue(all(Path(p["videoPath"]).is_file() for p in result["previews"]))
            self.assertTrue(any(p["donorWitness"] is not None for p in result["previews"]))
            self.assertIsNone(ecology["disposition"])
            self.assertIn("WATCHING != KEEP", result["laws"])


if __name__ == "__main__":
    unittest.main()
