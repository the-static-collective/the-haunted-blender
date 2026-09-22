"""N4 object isolation tests: synthetic pictures only, never personal archives."""
import hashlib
import json
import math
import shutil
import subprocess
import tempfile
import unittest
from io import BytesIO
from pathlib import Path

from haunted_blender import alchemy, catalog, contour_material, correspondence, living_mesh, project, render

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = ImageDraw = None


@unittest.skipUnless(Image is not None, "N4 uses optional local Pillow")
class ContourMaterialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.root = self.home / "vault"
        photos = self.home / "synthetic"
        photos.mkdir()
        catalog.init(self.root)
        self.source_contour = [[.26, .33], [.44, .33], [.44, .67], [.26, .67]]
        self.target_contour = [[.54, .30], [.77, .32], [.75, .74], [.52, .70]]
        for name, background, polygon, color in (
            ("source", (30, 100, 170), self.source_contour, (240, 45, 20)),
            ("target", (40, 160, 90), self.target_contour, (30, 215, 210)),
            ("clean", (88, 50, 40), None, None),
        ):
            img = Image.new("RGB", (320, 180), background)
            if polygon is not None:
                ImageDraw.Draw(img).polygon([(u * 319, v * 179) for u, v in polygon], fill=color)
            img.save(photos / (name + ".png"))
            img.close()
        self.photos = photos
        self.assertEqual(catalog.scan(self.root, photos)["indexed_or_changed"], 3)
        con = catalog.connect(self.root)
        self.asset = {Path(row["path"]).stem: row["id"]
                      for row in con.execute("SELECT id,path FROM assets")}
        con.close()
        recipe = alchemy.create(self.root, self.asset["source"], self.asset["target"],
                                statement="Artist-proposed contour shape change")
        self.n1 = alchemy.freeze(self.root, recipe["id"])
        points = [
            {"id": "upper_left", "from": [.15, .1], "to": [.15, .1]},
            {"id": "upper_right", "from": [.85, .1], "to": [.85, .1]},
        ]
        parent = correspondence.create(self.root, self.n1, points)
        self.n2 = correspondence.freeze(self.root, parent["id"])
        mesh = living_mesh.create(self.root, self.n2, living_mesh.grid())
        self.n3 = living_mesh.freeze(self.root, mesh["id"])

    def new(self, **opts):
        return contour_material.create(self.root, self.n3,
                                       self.source_contour, self.target_contour, **opts)

    def test_isolated_contour_plan_and_prior_layer_regression(self):
        ancestor_bytes = [p.read_bytes() for p in (self.n1, self.n2, self.n3)]
        recipe = self.new()
        frozen = contour_material.freeze(self.root, recipe["id"])
        self.assertEqual(frozen, contour_material.freeze(self.root, recipe["id"]))
        plan = contour_material.plan(self.root, frozen)
        self.assertEqual(plan["vertex_count"], 4)
        self.assertEqual(len(plan["face_receipts"]), 4)
        self.assertEqual(plan["material_mode"], "source-only")
        self.assertEqual(plan["background_mode"], "diagnostic-matte")
        self.assertEqual(plan["constraints"]["background_hole_filling"], "not_performed")
        self.assertGreater(plan["target_area_px2"], plan["source_area_px2"])
        self.assertTrue(all(face["min_twice_area_px2"] > 12 for face in plan["face_receipts"]))
        self.assertEqual([p.read_bytes() for p in (self.n1, self.n2, self.n3)], ancestor_bytes)
        self.assertEqual(living_mesh.plan(self.root, self.n3)["renderer"],
                         "pillow-triangle-mesh-ffmpeg/v1")
        self.assertEqual(correspondence.plan(self.root, self.n2)["renderer"],
                         "pillow-similarity-ffmpeg/v1")
        self.assertEqual(alchemy.plan(self.root, self.n1)["adapter"], "ffmpeg-alchemy-crossfade/v1")
        film = project.new_film(self.root, "N0 remains intact")
        scene = project.add_scene(self.root, film["id"], "Opening")
        project.add_shot(self.root, film["id"], scene["id"], self.asset["source"], 1000)
        self.assertEqual(render.plan(self.root, project.freeze(self.root, film["id"]))["adapter"],
                         "ffmpeg-static-storyboard/v1")

    def test_contour_validation_rejects_missing_nan_bowtie_and_reverse_winding(self):
        with self.assertRaisesRegex(ValueError, "same ordered vertex"):
            contour_material.create(self.root, self.n3, self.source_contour,
                                    self.target_contour[:-1])
        bad = [p[:] for p in self.source_contour]
        bad[0][0] = math.nan
        with self.assertRaisesRegex(ValueError, "finite normalized"):
            contour_material.create(self.root, self.n3, bad, self.target_contour)
        bad = [self.source_contour[i] for i in (0, 2, 1, 3)]
        recipe = contour_material.create(self.root, self.n3, bad, self.target_contour)
        with self.assertRaisesRegex(ValueError, "collapse or orientation|nonconvex"):
            contour_material.plan(self.root, contour_material.freeze(self.root, recipe["id"]))
        reverse = list(reversed(self.source_contour))
        recipe = contour_material.create(self.root, self.n3, reverse, list(reversed(self.target_contour)))
        with self.assertRaisesRegex(ValueError, "collapse or orientation"):
            contour_material.plan(self.root, contour_material.freeze(self.root, recipe["id"]))

    def test_midpoint_collapse_refused_even_when_endpoints_positive(self):
        before = [[.2, .2], [.4, .2], [.4, .4], [.2, .4]]
        after = [[.4, .4], [.2, .4], [.2, .2], [.4, .2]]
        recipe = contour_material.create(self.root, self.n3, before, after)
        with self.assertRaisesRegex(ValueError, "collapse or orientation"):
            contour_material.plan(self.root, contour_material.freeze(self.root, recipe["id"]))

    def test_clean_plate_requires_explicit_indexed_asset_and_frozen_digest(self):
        with self.assertRaisesRegex(ValueError, "requires an explicitly cataloged"):
            self.new(background_mode="clean-plate")
        with self.assertRaisesRegex(ValueError, "Diagnostic matte cannot claim"):
            self.new(clean_plate_asset_id=self.asset["clean"])
        with self.assertRaisesRegex(ValueError, "Unknown clean-plate asset"):
            self.new(background_mode="clean-plate", clean_plate_asset_id="asset-" + "0" * 24)
        recipe = self.new(background_mode="clean-plate", clean_plate_asset_id=self.asset["clean"])
        snapshot = contour_material.freeze(self.root, recipe["id"])
        plan = contour_material.plan(self.root, snapshot)
        self.assertEqual(plan["clean_plate"]["requested"]["id"], self.asset["clean"])
        self.assertEqual(plan["clean_plate"]["frame"]["sha256"], hashlib.sha256(
            (self.photos/"clean.png").read_bytes()).hexdigest())
        (self.photos / "clean.png").write_bytes(b"mutated clean plate")
        with self.assertRaisesRegex(ValueError, "Frozen clean plate missing or changed"):
            contour_material.plan(self.root, snapshot)

    def test_snapshot_tamper_and_source_mutation_refused(self):
        recipe = self.new()
        snap = contour_material.freeze(self.root, recipe["id"])
        packet = json.loads(snap.read_text(encoding="utf-8"))
        packet["recipe"]["material_mode"] = "crossfade"
        snap.write_text(json.dumps(packet), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "snapshot hash"):
            contour_material.plan(self.root, snap)
        other = self.new()
        fresh = contour_material.freeze(self.root, other["id"])
        (self.photos/"source.png").write_bytes(b"changed after acceptance")
        with self.assertRaisesRegex(ValueError, "Frozen source missing or changed"):
            contour_material.plan(self.root, fresh)

    def test_independent_revision_and_distinct_material_modes(self):
        first = self.new()
        old = contour_material.freeze(self.root, first["id"])
        second = self.new(material_mode="crossfade", revises=first["id"])
        new = contour_material.freeze(self.root, second["id"])
        self.assertEqual(second["revises"], first["id"])
        self.assertNotEqual(old, new)
        self.assertEqual(contour_material.plan(self.root, old)["material_mode"], "source-only")
        self.assertEqual(contour_material.plan(self.root, new)["material_mode"], "crossfade")

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg required for actual N4 preview")
    def test_render_isolated_object_no_background_ghost_and_material_mode(self):
        source = self.new()
        snapshot = contour_material.freeze(self.root, source["id"])
        video = self.home / "object.mp4"
        receipt = contour_material.render(self.root, snapshot, video)
        self.assertTrue(video.is_file())
        self.assertEqual(receipt["status"], "scoped_complete")
        self.assertEqual(receipt["output_sha256"], hashlib.sha256(video.read_bytes()).hexdigest())
        self.assertEqual(receipt["frame_count"], 49)
        self.assertEqual(len(receipt["alpha_coverage_px"]), 49)
        self.assertTrue(min(receipt["alpha_coverage_px"]) > 0)
        self.assertTrue(video.with_suffix(".mp4.receipt.json").exists())
        with self.assertRaises(FileExistsError):
            contour_material.render(self.root, snapshot, video)
        def decoded_at(index):
            cmd = ["ffmpeg", "-nostdin", "-v", "error", "-i", str(video),
                   "-vf", "select=eq(n\\," + str(index) + ")", "-frames:v", "1",
                   "-f", "image2pipe", "-vcodec", "png", "-"]
            data = subprocess.run(cmd, check=True, capture_output=True).stdout
            return Image.open(BytesIO(data)).convert("RGB")
        first = decoded_at(0)
        mid = decoded_at(24)
        last = decoded_at(48)
        # Outside the selected object, the diagnostic background replaces the original
        # source photograph: the object cannot leave a baked-in copy of itself behind.
        for frame in (first, mid, last):
            self.assertLess(max(abs(a-b) for a,b in zip(frame.getpixel((5,5)),
                                                     contour_material.DIAGNOSTIC_COLOR)), 16)
        self.assertGreater(first.getpixel((110, 90))[0], 175)
        self.assertGreater(mid.getpixel((160, 90))[0], 115)
        self.assertGreater(last.getpixel((205, 90))[0], 110)
        self.assertLess(max(last.getpixel((110,90))), 65)
        # Source-only material does not silently become the destination's cyan material.
        self.assertGreater(last.getpixel((205,90))[0], last.getpixel((205,90))[1])
        first.close()
        mid.close()
        last.close()

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg required for actual clean-plate preview")
    def test_explicit_clean_plate_background_and_crossfade_material(self):
        recipe = self.new(material_mode="crossfade", background_mode="clean-plate",
                          clean_plate_asset_id=self.asset["clean"])
        frozen = contour_material.freeze(self.root, recipe["id"])
        video = self.home / "clean.mp4"
        receipt = contour_material.render(self.root, frozen, video)
        self.assertEqual(receipt["background_mode"], "clean-plate")
        self.assertIsNotNone(receipt["clean_plate_sha256"])
        cmd = ["ffmpeg", "-nostdin", "-v", "error", "-i", str(video),
               "-vf", "select=eq(n\\,48)", "-frames:v", "1",
               "-f", "image2pipe", "-vcodec", "png", "-"]
        frame = Image.open(BytesIO(subprocess.run(cmd, check=True, capture_output=True).stdout)).convert("RGB")
        background = frame.getpixel((5,5))
        self.assertLess(max(abs(a-b) for a,b in zip(background, (88,50,40))), 16)
        center = frame.getpixel((205,90))
        self.assertGreater(center[1], center[0])  # Target cyan replaces source orange.
        frame.close()


if __name__ == "__main__":
    unittest.main()
