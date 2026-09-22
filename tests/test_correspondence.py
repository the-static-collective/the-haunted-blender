"""N2 correspondence tests use synthetic artwork only; no personal photo data."""
import hashlib
import json
import math
import shutil
import subprocess
import tempfile
import unittest
from io import BytesIO
from pathlib import Path

from haunted_blender import alchemy, catalog, correspondence, project, render

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = ImageDraw = None


@unittest.skipUnless(Image is not None, "optional Pillow is required for correspondence cartridge")
class CorrespondenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "library"
        self.photos = Path(self.tmp.name) / "photos"
        self.photos.mkdir()
        catalog.init(self.root)
        for name, positions, rgb in (
            ("cup", [(0.25, 0.3), (0.75, 0.3)], (230, 35, 35)),
            ("water", [(0.3, 0.25), (0.8, 0.25)], (25, 210, 60)),
            ("moon", [(0.28, 0.26), (0.72, 0.26)], (20, 90, 230)),
        ):
            im = Image.new("RGB", (96, 54), (15, 15, 15))
            dr = ImageDraw.Draw(im)
            for x, y in positions:
                px, py = x * 95, y * 53
                dr.ellipse((px - 4, py - 4, px + 4, py + 4), fill=rgb)
            im.save(self.photos / (name + ".png"))
        self.assertEqual(catalog.scan(self.root, self.photos)["indexed_or_changed"], 3)
        con = catalog.connect(self.root)
        self.assets = {Path(r["path"]).stem: r["id"] for r in
                       con.execute("SELECT path,id FROM assets")}
        con.close()
        recipe = alchemy.create(self.root, self.assets["cup"], self.assets["moon"],
                                bridge=self.assets["water"], relation="triadic-bridge",
                                statement="Cup, water, moon: artist-proposed three-part reflection")
        self.parent = alchemy.freeze(self.root, recipe["id"])

    def points(self):
        return [
            {"id": "rim-left", "from": [0.25, 0.30], "to": [0.30, 0.25]},
            {"id": "rim-right", "from": [0.75, 0.30], "to": [0.80, 0.25]},
        ]

    def make(self, **kwargs):
        return correspondence.create(self.root, self.parent, self.points(), **kwargs)

    def test_frozen_three_part_relation_remains_unmodified(self):
        original_bytes = self.parent.read_bytes()
        recipe = self.make()
        snap = correspondence.freeze(self.root, recipe["id"])
        spec = correspondence.plan(self.root, snap)
        self.assertEqual(spec["from_role"], "source")
        self.assertEqual(spec["to_role"], "bridge")
        self.assertEqual(spec["point_count"], 2)
        self.assertLess(spec["max_geometric_reprojection_error_px"], 0.000001)
        self.assertEqual(spec["constraints"]["actual_pixel_tracking"], "not_assessed")
        self.assertEqual(self.parent.read_bytes(), original_bytes)
        self.assertEqual(alchemy.plan(self.root, self.parent)["adapter"], "ffmpeg-alchemy-crossfade/v1")
        film = project.new_film(self.root, "Untouched N0")
        scene = project.add_scene(self.root, film["id"], "One")
        project.add_shot(self.root, film["id"], scene["id"], self.assets["cup"], 750)
        self.assertEqual(render.plan(self.root, project.freeze(self.root, film["id"]))["adapter"],
                         "ffmpeg-static-storyboard/v1")

    def test_reject_nonadjacent_roles_and_invalid_points(self):
        with self.assertRaisesRegex(ValueError, "consecutive roles"):
            self.make(from_role="source", to_role="target")
        with self.assertRaisesRegex(ValueError, "2–16"):
            correspondence.create(self.root, self.parent, self.points()[:1])
        invalid = self.points()
        invalid[0]["to"] = [math.nan, 0.2]
        with self.assertRaisesRegex(ValueError, "finite normalized"):
            correspondence.create(self.root, self.parent, invalid)
        invalid = self.points()
        invalid[1]["from"] = invalid[0]["from"]
        with self.assertRaisesRegex(ValueError, "well-separated"):
            correspondence.create(self.root, self.parent, invalid)
        invalid = self.points()
        invalid[1]["id"] = invalid[0]["id"]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            correspondence.create(self.root, self.parent, invalid)

    def test_inconsistent_third_point_refuses_constraint(self):
        points = self.points() + [{"id": "third", "from": [0.5, 0.75], "to": [0.5, 0.05]}]
        recipe = correspondence.create(self.root, self.parent, points, max_error_px=2.0)
        snap = correspondence.freeze(self.root, recipe["id"])
        with self.assertRaisesRegex(ValueError, "reprojection exceeds tolerance"):
            correspondence.plan(self.root, snap)

    def test_revisions_are_new_recipes_and_old_snapshot_is_stable(self):
        original = self.make()
        original_snap = correspondence.freeze(self.root, original["id"])
        updated = self.points()
        updated[0]["to"] = [0.32, 0.27]
        updated[1]["to"] = [0.82, 0.27]
        revision = correspondence.create(self.root, self.parent, updated, revises=original["id"])
        revision_snap = correspondence.freeze(self.root, revision["id"])
        self.assertEqual(revision["revises"], original["id"])
        self.assertNotEqual(original_snap, revision_snap)
        self.assertEqual(correspondence.plan(self.root, original_snap)["points"], self.points())
        self.assertEqual(correspondence.plan(self.root, revision_snap)["points"], updated)

    def test_parent_or_source_tampering_cannot_pass(self):
        recipe = self.make()
        snap = correspondence.freeze(self.root, recipe["id"])
        bundle = json.loads(snap.read_text(encoding="utf-8"))
        bundle["recipe"]["max_error_px"] = 30.0
        snap.write_text(json.dumps(bundle), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "snapshot hash"):
            correspondence.plan(self.root, snap)
        snap = correspondence.freeze(self.root, recipe["id"]) if False else None
        fresh = self.make()
        fresh_snap = correspondence.freeze(self.root, fresh["id"])
        (self.photos / "moon.png").write_bytes(b"altered image")
        with self.assertRaisesRegex(ValueError, "Frozen source missing or changed"):
            correspondence.plan(self.root, fresh_snap)

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg required for output proof")
    def test_real_geometric_morph_video_and_receipt(self):
        recipe = self.make()
        snap = correspondence.freeze(self.root, recipe["id"])
        outfile = Path(self.tmp.name) / "geometry.mp4"
        receipt = correspondence.render(self.root, snap, outfile)
        self.assertEqual(receipt["status"], "scoped_complete")
        self.assertEqual(receipt["frames"], correspondence.FRAMES)
        self.assertEqual(receipt["point_count"], 2)
        self.assertEqual(receipt["output_sha256"], hashlib.sha256(outfile.read_bytes()).hexdigest())
        self.assertIn("not semantic metamorphosis", receipt["claim"])
        self.assertTrue(outfile.with_suffix(".mp4.receipt.json").is_file())
        with self.assertRaises(FileExistsError):
            correspondence.render(self.root, snap, outfile)
        # Decode the middle frame and check that transformed synthetic feature color exists
        # around the predicted anchor; this is a pixel-level test, not semantic recognition.
        command = ["ffmpeg", "-nostdin", "-v", "error", "-i", str(outfile),
                   "-vf", "select=eq(n\\,24)", "-frames:v", "1",
                   "-f", "image2pipe", "-vcodec", "png", "-"]
        mid = subprocess.run(command, check=True, capture_output=True).stdout
        frame = Image.open(BytesIO(mid)).convert("RGB")
        self.assertEqual(frame.size, (correspondence.WIDTH, correspondence.HEIGHT))
        # First point travels from x=.25 to x=.30, y=.30 to .25 in a full-canvas 16:9 fixture.
        px, py = round(0.275 * (correspondence.WIDTH - 1)), round(0.275 * (correspondence.HEIGHT - 1))
        neighborhood = [frame.getpixel((x, y))
                        for x in range(px - 4, px + 5)
                        for y in range(py - 4, py + 5)]
        self.assertTrue(any(max(color) > 50 for color in neighborhood))


if __name__ == "__main__":
    unittest.main()
