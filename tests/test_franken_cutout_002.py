import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from haunted_blender.cutout_stage import SCHEMA as CUTOUT_SCHEMA, render_cutout
from haunted_blender.flow_pantry import index_flow_folder
from haunted_blender.playdeck_bridge import flow_to_playdeck
from haunted_blender.toaster_bridge import plan_toaster_vspantry


class FrankenCutout002Tests(unittest.TestCase):
    def make_video(self, path: Path, color: str) -> None:
        subprocess.run(
            [
                "ffmpeg", "-v", "error", "-y",
                "-f", "lavfi", "-i", f"color=c={color}:s=64x48:d=0.25:r=8",
                "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path),
            ],
            check=True,
        )

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
    def test_flow_index_is_path_light_and_toaster_addressable(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_video(root / "01-rise.mp4", "red")
            self.make_video(root / "02-light.mp4", "blue")
            manifest = index_flow_folder(root)
            self.assertEqual(manifest["schema"], "haunted-blender/flow-pantry/v1")
            self.assertEqual(manifest["itemCount"], 2)
            self.assertEqual(manifest["uniqueSpecimenCount"], 2)
            self.assertNotIn(str(root), json.dumps(manifest))
            self.assertTrue(all(i["toasterSpecimenId"].startswith("sha256:") for i in manifest["items"]))
            self.assertTrue(all(i["technical"]["width"] == 64 for i in manifest["items"]))

    def test_225_unique_flow_items_become_15_toaster_batches(self):
        items = []
        for index in range(225):
            sha = f"{index:064x}"
            items.append(
                {
                    "assetId": f"flow-video:{sha}:100",
                    "toasterSpecimenId": f"sha256:{sha}:100",
                    "relativePath": f"{index:03d}.mp4",
                    "extension": ".mp4",
                    "sha256": sha,
                    "byteLength": 100,
                    "technical": None,
                }
            )
        manifest = {
            "schema": "haunted-blender/flow-pantry/v1",
            "authority": "index-only",
            "recursive": True,
            "itemCount": 225,
            "uniqueSpecimenCount": 225,
            "filenameSemantics": "none",
            "items": items,
        }
        plan = plan_toaster_vspantry(manifest)
        self.assertEqual(plan["batchCount"], 15)
        self.assertEqual([len(b["ingredients"]) for b in plan["batches"][:-1]], [16] * 14)
        self.assertEqual(len(plan["batches"][-1]["ingredients"]), 1)
        self.assertFalse(plan["grantsRendererAuthority"])

    def test_playdeck_projection_is_sleeping_proposal_not_render_claim(self):
        sha = "a" * 64
        manifest = {
            "schema": "haunted-blender/flow-pantry/v1",
            "authority": "index-only",
            "recursive": True,
            "itemCount": 1,
            "uniqueSpecimenCount": 1,
            "filenameSemantics": "none",
            "items": [{
                "assetId": f"flow-video:{sha}:123",
                "toasterSpecimenId": f"sha256:{sha}:123",
                "relativePath": "clip.mp4",
                "extension": ".mp4",
                "sha256": sha,
                "byteLength": 123,
                "technical": None,
            }],
        }
        proposal = flow_to_playdeck(manifest, deck_id="flow-225")
        card = proposal["deck"]["cards"][0]
        self.assertEqual(proposal["authority"], "proposal-only")
        self.assertEqual(card["temperament"], ["sleeping"])
        self.assertTrue(card["permissions"]["awaken"])
        self.assertFalse(card["metadata"]["renderReady"])
        self.assertFalse(proposal["grantsPlaydeckRenderAuthority"])

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg required")
    def test_cutout_stage_renders_real_motion_and_receipt_without_overwrite(self):
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            self.skipTest("Pillow required")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bg = root / "bg.png"
            body = root / "body.png"
            arm = root / "arm.png"

            Image.new("RGBA", (96, 64), (30, 35, 50, 255)).save(bg)
            Image.new("RGBA", (24, 36), (220, 180, 80, 255)).save(body)
            arm_img = Image.new("RGBA", (18, 8), (0, 0, 0, 0))
            draw = ImageDraw.Draw(arm_img)
            draw.rectangle((0, 1, 17, 6), fill=(240, 210, 120, 255))
            arm_img.save(arm)

            plan = {
                "schema": CUTOUT_SCHEMA,
                "canvas": {"width": 96, "height": 64, "fps": 8, "duration": 0.5},
                "layers": [
                    {"id": "background", "source": str(bg), "z": 0},
                    {
                        "id": "body", "source": str(body), "z": 1, "x": 10, "y": 20,
                        "keyframes": [
                            {"time": 0, "x": 10, "y": 20, "scale": 1, "rotation": 0, "opacity": 1},
                            {"time": 0.5, "x": 45, "y": 12, "scale": 1, "rotation": 0, "opacity": 1},
                        ],
                    },
                    {
                        "id": "arm", "source": str(arm), "z": 2, "x": 25, "y": 28,
                        "keyframes": [
                            {"time": 0, "x": 25, "y": 28, "scale": 1, "rotation": -10, "opacity": 1},
                            {"time": 0.5, "x": 60, "y": 20, "scale": 1, "rotation": 35, "opacity": 1},
                        ],
                    },
                ],
            }
            out = root / "cutout.mp4"
            receipt = render_cutout(plan, out)
            self.assertTrue(out.is_file())
            self.assertGreater(out.stat().st_size, 0)
            self.assertEqual(receipt["status"], "scoped_complete")
            self.assertEqual(receipt["frameCount"], 4)
            self.assertEqual(receipt["audioAuthority"], "none")
            with self.assertRaises(FileExistsError):
                render_cutout(plan, out)


if __name__ == "__main__":
    unittest.main()
