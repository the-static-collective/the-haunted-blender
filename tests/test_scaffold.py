import json
import tempfile
import unittest
from pathlib import Path

from haunted_blender import catalog, project, render


class NuclearScaffoldTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "blender"
        self.photos = Path(self.temp.name) / "photos"
        self.photos.mkdir()
        catalog.init(self.root)

    def test_resumable_scan_and_raw_derivative(self):
        raw = self.photos / "moment.CR2"
        raw.write_bytes(b"synthetic RAW fixture - not a real photograph")
        (self.photos / "moment.xmp").write_text("<xmp>test</xmp>")
        image = self.photos / "moment-edited.jpg"
        image.write_bytes(b"synthetic JPEG fixture - not a real photograph")
        first = catalog.scan(self.root, self.photos)
        self.assertEqual(first["indexed_or_changed"], 2)
        second = catalog.scan(self.root, self.photos)
        self.assertEqual(second["unchanged"], 2)
        con = catalog.connect(self.root)
        raw_row = con.execute("SELECT * FROM assets WHERE extension='.cr2'").fetchone()
        self.assertEqual(raw_row["sidecar_path"], str(self.photos / "moment.xmp"))
        con.close()
        derivative_id = catalog.derivative(self.root, raw_row["id"], image)
        con = catalog.connect(self.root)
        self.assertEqual(catalog.source_for_render(con, raw_row["id"])["id"], derivative_id)
        con.close()

    def test_freeze_and_render_plan_requires_editable_derivative(self):
        raw = self.photos / "source.CR2"
        raw.write_bytes(b"synthetic RAW fixture")
        catalog.scan(self.root, self.photos)
        con = catalog.connect(self.root)
        raw_id = con.execute("SELECT id FROM assets").fetchone()["id"]
        con.close()
        film = project.new_film(self.root, "A film")
        scene = project.add_scene(self.root, film["id"], "Opening")
        project.add_shot(self.root, film["id"], scene["id"], raw_id, 1500)
        snapshot = project.freeze(self.root, film["id"])
        with self.assertRaisesRegex(ValueError, "no renderable derivative"):
            render.plan(self.root, snapshot)
        export = self.photos / "export.jpg"
        export.write_bytes(b"synthetic image fixture")
        catalog.derivative(self.root, raw_id, export)
        spec = render.plan(self.root, snapshot)
        self.assertEqual(spec["shots"][0]["requested_asset_id"], raw_id)
        self.assertEqual(spec["shots"][0]["duration_ms"], 1500)
        self.assertEqual(spec["audio"], "none")
        self.assertEqual(spec["adapter"], "ffmpeg-static-storyboard/v1")
        # Actual footage render requires an actual JPEG and ffmpeg; not claimed by this test.

    def test_tamper_detected_and_no_snapshot_overwrite(self):
        image = self.photos / "frame.png"
        image.write_bytes(b"synthetic image fixture")
        catalog.scan(self.root, self.photos)
        con = catalog.connect(self.root)
        asset_id = con.execute("SELECT id FROM assets").fetchone()["id"]
        con.close()
        film = project.new_film(self.root, "A film")
        scene = project.add_scene(self.root, film["id"], "Opening")
        project.add_shot(self.root, film["id"], scene["id"], asset_id, 1000)
        snapshot = project.freeze(self.root, film["id"])
        self.assertEqual(snapshot, project.freeze(self.root, film["id"]))
        image.write_bytes(b"changed source")
        with self.assertRaisesRegex(ValueError, "Source changed"):
            render.plan(self.root, snapshot)
        original = json.loads(snapshot.read_text())
        original["title"] = "Tampered"
        snapshot.write_text(json.dumps(original))
        with self.assertRaisesRegex(ValueError, "Snapshot hash"):
            project.load_snapshot(self.root, snapshot)

    def test_invalid_shot_and_existing_project_protected(self):
        film = project.new_film(self.root, "Another film")
        scene = project.add_scene(self.root, film["id"], "Interior")
        with self.assertRaisesRegex(ValueError, "Shot duration"):
            project.add_shot(self.root, film["id"], scene["id"], "asset-abc", 0)
        unchanged = project.load(self.root, film["id"])
        self.assertEqual(unchanged["scenes"][0]["shots"], [])


if __name__ == "__main__":
    unittest.main()
