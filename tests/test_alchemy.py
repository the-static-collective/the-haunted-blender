"""N1 alchemy contract tests. No personal photographs or remote models."""
import hashlib
import json
import shutil
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from haunted_blender import alchemy, catalog, project, render


def png(path: Path, rgb: tuple[int, int, int]) -> None:
    """Write a real 48x32 solid-color PNG using the standard library."""
    width, height = 48, 32
    pixels = (b"\x00" + bytes(rgb) * width) * height

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff))

    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">2I5B", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(pixels))
        + chunk(b"IEND", b"")
    )


class AlchemyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "library"
        self.photos = Path(self.tmp.name) / "photos"
        self.photos.mkdir()
        catalog.init(self.root)
        for name, rgb in (("cup", (180, 50, 60)), ("water", (30, 80, 190)),
                          ("moon", (230, 210, 155))):
            png(self.photos / (name + ".png"), rgb)
        self.assertEqual(catalog.scan(self.root, self.photos)["indexed_or_changed"], 3)
        con = catalog.connect(self.root)
        self.assets = {Path(row["path"]).stem: row["id"]
                       for row in con.execute("SELECT id,path FROM assets")}
        con.close()

    def triad(self, **kwargs):
        return alchemy.create(self.root, self.assets["cup"], self.assets["moon"],
                              bridge=self.assets["water"], relation="triadic-bridge",
                              statement="Cup contains water that reflects a moon; artist proposal",
                              **kwargs)

    def test_triadic_requirement_and_catalog_boundary(self):
        with self.assertRaisesRegex(ValueError, "declared participants"):
            alchemy.create(self.root, self.assets["cup"], self.assets["moon"],
                           relation="triadic-bridge")
        with self.assertRaisesRegex(ValueError, "declared participants"):
            alchemy.create(self.root, self.assets["cup"], self.assets["moon"],
                           bridge=self.assets["water"], relation="shape-echo")
        with self.assertRaisesRegex(ValueError, "distinct"):
            alchemy.create(self.root, self.assets["cup"], self.assets["moon"],
                           bridge=self.assets["cup"], relation="triadic-bridge")
        with self.assertRaisesRegex(ValueError, "Uncataloged"):
            alchemy.create(self.root, "asset-" + "0" * 24, self.assets["moon"])
        self.assertFalse((self.root / "projects" / "alchemy").exists())

    def test_frozen_triad_has_three_participants_and_truthful_checks(self):
        recipe = self.triad()
        snapshot = alchemy.freeze(self.root, recipe["id"])
        self.assertEqual(snapshot, alchemy.freeze(self.root, recipe["id"]))
        spec = alchemy.plan(self.root, snapshot)
        self.assertEqual([s["role"] for s in spec["segments"]], ["source", "bridge", "target"])
        self.assertEqual(spec["duration_ms"], 4500)
        self.assertEqual(spec["checks"]["visual_relation"], "not_assessed")
        self.assertEqual(spec["evidence_class"], "artist_proposed")
        self.assertEqual(spec["adapter"], "ffmpeg-alchemy-crossfade/v1")
        self.assertEqual(len(spec["segments"]), 3)
        self.assertEqual(spec["audio"], "none")

    def test_reordering_is_not_collapsed(self):
        first = self.triad()
        second = self.triad(order=["bridge", "source", "target"])
        plan_a = alchemy.plan(self.root, alchemy.freeze(self.root, first["id"]))
        plan_b = alchemy.plan(self.root, alchemy.freeze(self.root, second["id"]))
        self.assertNotEqual([s["role"] for s in plan_a["segments"]],
                            [s["role"] for s in plan_b["segments"]])
        self.assertNotEqual(plan_a["snapshot_sha256"], plan_b["snapshot_sha256"])

    def test_tamper_and_mutated_source_refused(self):
        recipe = self.triad()
        snapshot = alchemy.freeze(self.root, recipe["id"])
        (self.photos / "water.png").write_bytes(b"mutated after freezing")
        with self.assertRaisesRegex(ValueError, "Frozen source missing or changed"):
            alchemy.plan(self.root, snapshot)
        bundle = json.loads(snapshot.read_text(encoding="utf-8"))
        bundle["recipe"]["statement"] = "forged"
        snapshot.write_text(json.dumps(bundle), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "snapshot hash"):
            alchemy.plan(self.root, snapshot)

    def test_raw_derivative_is_frozen_against_reassociation(self):
        raw = self.photos / "original.CR2"
        raw.write_bytes(b"not a real RAW - digest fixture only")
        raw_id, _ = None, None
        con = catalog.connect(self.root)
        try:
            raw_id, _ = catalog.index_file(con, raw)
            con.commit()
        finally:
            con.close()
        catalog.derivative(self.root, raw_id, self.photos / "cup.png")
        recipe = alchemy.create(self.root, raw_id, self.assets["moon"])
        snapshot = alchemy.freeze(self.root, recipe["id"])
        before = alchemy.plan(self.root, snapshot)
        catalog.derivative(self.root, raw_id, self.photos / "water.png")
        after = alchemy.plan(self.root, snapshot)
        self.assertEqual(before["segments"][0]["frame_asset_id"], self.assets["cup"])
        self.assertEqual(before["segments"][0]["frame_asset_id"], after["segments"][0]["frame_asset_id"])
        self.assertEqual(before["snapshot_sha256"], after["snapshot_sha256"])

    def test_n0_filmmaking_contract_untouched(self):
        film = project.new_film(self.root, "Original layer")
        scene = project.add_scene(self.root, film["id"], "Opening")
        project.add_shot(self.root, film["id"], scene["id"], self.assets["cup"], 800)
        frozen = project.freeze(self.root, film["id"])
        self.triad()
        self.assertEqual(render.plan(self.root, frozen)["adapter"], "ffmpeg-static-storyboard/v1")
        self.assertEqual(project.load(self.root, film["id"])["schema"], "haunted-blender/film/v1")

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg unavailable; deterministic plan tests still run")
    def test_actual_ffmpeg_transition_and_receipt(self):
        recipe = self.triad()
        snapshot = alchemy.freeze(self.root, recipe["id"])
        out = Path(self.tmp.name) / "result.mp4"
        receipt = alchemy.render(self.root, snapshot, out)
        self.assertTrue(out.stat().st_size > 0)
        self.assertEqual(receipt["output_sha256"], hashlib.sha256(out.read_bytes()).hexdigest())
        self.assertEqual(receipt["status"], "scoped_complete")
        self.assertIn("not a verified semantic metamorphosis", receipt["claim"])
        self.assertTrue(out.with_suffix(".mp4.receipt.json").exists())
        with self.assertRaises(FileExistsError):
            alchemy.render(self.root, snapshot, out)


if __name__ == "__main__":
    unittest.main()
