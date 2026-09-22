"""N3 Living Mesh pressure tests; only small generated synthetic images enter the pantry."""
import hashlib
import json
import math
import shutil
import subprocess
import tempfile
import unittest
from io import BytesIO
from pathlib import Path

from haunted_blender import alchemy, catalog, correspondence, living_mesh, project, render

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = ImageDraw = None


@unittest.skipUnless(Image is not None, "N3 requires optional Pillow")
class LivingMeshTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "vault"
        self.photos = Path(self.tmp.name) / "synthetic"
        self.photos.mkdir()
        catalog.init(self.root)
        for name, center, color in (
            ("cup", (.5, .5), (240, 40, 40)),
            ("water", (.58, .53), (30, 220, 80)),
            ("moon", (.6, .5), (60, 70, 235)),
        ):
            image = Image.new("RGB", (320, 180), (10, 10, 10))
            draw = ImageDraw.Draw(image)
            x, y = (center[0] * 319, center[1] * 179)
            draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=color)
            # Stable common first-layer landmarks remain in the top mesh row.
            for u in (.15, .85):
                px, py = u * 319, .1 * 179
                draw.ellipse((px - 4, py - 4, px + 4, py + 4), fill=(230, 230, 230))
            image.save(self.photos / (name + ".png"))
            image.close()
        self.assertEqual(catalog.scan(self.root, self.photos)["indexed_or_changed"], 3)
        con = catalog.connect(self.root)
        self.assets = {Path(row["path"]).stem: row["id"]
                       for row in con.execute("SELECT path,id FROM assets")}
        con.close()
        n1 = alchemy.create(self.root, self.assets["cup"], self.assets["moon"],
                            relation="triadic-bridge", bridge=self.assets["water"],
                            statement="Artist-proposed cup/water/moon transformation")
        self.n1_snapshot = alchemy.freeze(self.root, n1["id"])
        landmarks = [
            {"id": "rim-left", "from": [.15, .1], "to": [.15, .1]},
            {"id": "rim-right", "from": [.85, .1], "to": [.85, .1]},
        ]
        n2 = correspondence.create(self.root, self.n1_snapshot, landmarks,
                                   from_role="source", to_role="bridge")
        self.n2_snapshot = correspondence.freeze(self.root, n2["id"])

    def deformed(self):
        target = living_mesh.grid()
        target[12] = [.58, .53]  # Center can move while the 16 boundary nodes remain fixed.
        return target

    def make(self, **kwargs):
        return living_mesh.create(self.root, self.n2_snapshot, self.deformed(), **kwargs)

    def test_dogram_analytic_orientation_catches_hidden_midpoint_fold(self):
        # Both endpoint triangles have positive orientation, but a 180-degree
        # vertex rotation through straight trajectories collapses at t=1/2.
        source = [(0., 0.), (100., 0.), (0., 100.)]
        target = [(0., 0.), (-100., 0.), (0., -100.)]
        witness = living_mesh.orientation_envelope(source, target, (0, 1, 2))
        self.assertGreater(witness["source_twice_area_px2"], 0)
        self.assertGreater(witness["target_twice_area_px2"], 0)
        self.assertEqual(witness["min_twice_area_px2"], 0)
        self.assertEqual(witness["min_at_t"], .5)

    def test_distinct_local_deformation_preserves_legacy_layers(self):
        parent_before = self.n2_snapshot.read_bytes()
        n1_before = self.n1_snapshot.read_bytes()
        recipe = self.make()
        frozen = living_mesh.freeze(self.root, recipe["id"])
        self.assertEqual(frozen, living_mesh.freeze(self.root, recipe["id"]))
        result = living_mesh.plan(self.root, frozen)
        self.assertEqual(result["face_count"], 32)
        self.assertEqual(result["grid"], 5)
        self.assertEqual(result["frames"], 49)
        self.assertEqual(result["constraints"]["triangle_orientation_all_continuous_t"],
                         "validated_analytically")
        self.assertEqual(len(result["face_receipts"]), 32)
        self.assertEqual(len(result["landmark_receipts"]), 2)
        self.assertLess(result["max_inherited_landmark_error_px"], 1e-6)
        self.assertEqual(self.n2_snapshot.read_bytes(), parent_before)
        self.assertEqual(self.n1_snapshot.read_bytes(), n1_before)
        self.assertEqual(alchemy.plan(self.root, self.n1_snapshot)["adapter"],
                         "ffmpeg-alchemy-crossfade/v1")
        self.assertEqual(correspondence.plan(self.root, self.n2_snapshot)["renderer"],
                         "pillow-similarity-ffmpeg/v1")
        film = project.new_film(self.root, "Original N0")
        scene = project.add_scene(self.root, film["id"], "Shot")
        project.add_shot(self.root, film["id"], scene["id"], self.assets["cup"], 800)
        self.assertEqual(render.plan(self.root, project.freeze(self.root, film["id"]))["adapter"],
                         "ffmpeg-static-storyboard/v1")

    def test_invalid_grid_and_boundary_motion_are_refused(self):
        vertices = self.deformed()
        with self.assertRaisesRegex(ValueError, "exactly 25"):
            living_mesh.create(self.root, self.n2_snapshot, vertices[:-1])
        invalid = self.deformed()
        invalid[0] = [.02, 0.]
        with self.assertRaisesRegex(ValueError, "Boundary vertices"):
            living_mesh.create(self.root, self.n2_snapshot, invalid)
        invalid = self.deformed()
        invalid[12] = [math.nan, .5]
        with self.assertRaisesRegex(ValueError, "finite normalized"):
            living_mesh.create(self.root, self.n2_snapshot, invalid)
        invalid = self.deformed()
        invalid[12] = [True, .5]
        with self.assertRaisesRegex(ValueError, "finite normalized"):
            living_mesh.create(self.root, self.n2_snapshot, invalid)

    def test_inverted_mesh_is_refused_even_with_valid_endpoint_file(self):
        invalid = self.deformed()
        invalid[12] = [.99, .99]
        recipe = living_mesh.create(self.root, self.n2_snapshot, invalid)
        frozen = living_mesh.freeze(self.root, recipe["id"])
        with self.assertRaisesRegex(ValueError, "Triangle collapse or orientation flip"):
            living_mesh.plan(self.root, frozen)

    def test_landmark_conflicts_are_not_silently_ignored(self):
        vertices = living_mesh.grid()
        # Move an interior control near the inherited upper-left landmark.
        vertices[6] = [.32, .26]
        recipe = living_mesh.create(self.root, self.n2_snapshot, vertices,
                                     max_landmark_error_px=.25)
        frozen = living_mesh.freeze(self.root, recipe["id"])
        with self.assertRaisesRegex(ValueError, "landmark error exceeds|crosses mesh faces"):
            living_mesh.plan(self.root, frozen)

    def test_distinct_revision_preserves_prior_recipe_and_snapshot(self):
        original = self.make()
        earlier = living_mesh.freeze(self.root, original["id"])
        changed = self.deformed()
        changed[12] = [.55, .52]
        revised = living_mesh.create(self.root, self.n2_snapshot, changed, revises=original["id"])
        newer = living_mesh.freeze(self.root, revised["id"])
        self.assertNotEqual(earlier, newer)
        self.assertEqual(revised["revises"], original["id"])
        self.assertEqual(living_mesh.plan(self.root, earlier)["vertices"]["target"][12], [.58, .53])
        self.assertEqual(living_mesh.plan(self.root, newer)["vertices"]["target"][12], [.55, .52])

    def test_snapshot_tamper_and_real_source_mutation_refused(self):
        recipe = self.make()
        frozen = living_mesh.freeze(self.root, recipe["id"])
        snapshot = json.loads(frozen.read_text(encoding="utf-8"))
        snapshot["recipe"]["target_vertices"][12] = [.52, .55]
        frozen.write_text(json.dumps(snapshot), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "snapshot hash"):
            living_mesh.plan(self.root, frozen)
        second = self.make()
        second_frozen = living_mesh.freeze(self.root, second["id"])
        (self.photos / "cup.png").write_bytes(b"mutated private source")
        with self.assertRaisesRegex(ValueError, "Frozen source missing or changed"):
            living_mesh.plan(self.root, second_frozen)

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg needed for executable video check")
    def test_rendered_nonrigid_frame_and_output_receipt(self):
        recipe = self.make()
        frozen = living_mesh.freeze(self.root, recipe["id"])
        out = Path(self.tmp.name) / "living-mesh.mp4"
        result = living_mesh.render(self.root, frozen, out)
        self.assertTrue(out.stat().st_size > 0)
        self.assertEqual(result["status"], "scoped_complete")
        self.assertEqual(result["output_sha256"], hashlib.sha256(out.read_bytes()).hexdigest())
        self.assertEqual(len(result["face_receipts"]), 32)
        self.assertEqual(result["constraints"]["visible_pixel_identity"], "not_assessed")
        self.assertTrue(out.with_suffix(".mp4.receipt.json").exists())
        with self.assertRaises(FileExistsError):
            living_mesh.render(self.root, frozen, out)
        decode = ["ffmpeg", "-nostdin", "-v", "error", "-i", str(out),
                  "-vf", "select=eq(n\\,24)", "-frames:v", "1",
                  "-f", "image2pipe", "-vcodec", "png", "-"]
        frame_bytes = subprocess.run(decode, check=True, capture_output=True).stdout
        frame = Image.open(BytesIO(frame_bytes)).convert("RGB")
        self.assertEqual(frame.size, (living_mesh.WIDTH, living_mesh.HEIGHT))
        predicted_x = round(.54 * 319)
        predicted_y = round(.515 * 179)
        neighborhood = [frame.getpixel((x, y))
                        for x in range(predicted_x - 4, predicted_x + 5)
                        for y in range(predicted_y - 4, predicted_y + 5)]
        self.assertTrue(any(max(rgb) > 55 for rgb in neighborhood),
                        "Decoded midpoint must contain the transported synthetic center feature")


if __name__ == "__main__":
    unittest.main()
