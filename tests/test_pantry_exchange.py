"""Nuklear Pantry Exchange: local, synthetic stills only."""
import hashlib
import json
import shutil
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from haunted_blender import alchemy, catalog
from haunted_blender.pantry_exchange import SCHEMA, export_alchemy


def png(path: Path, rgb: tuple[int, int, int]) -> None:
    width, height = 48, 32
    pixels = (b"\x00" + bytes(rgb) * width) * height

    def chunk(kind, data):
        return (struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff))

    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">2I5B", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(pixels))
        + chunk(b"IEND", b"")
    )


@unittest.skipUnless(shutil.which("ffmpeg"), "Real alchemical MP4 proof requires local FFmpeg")
class ExchangeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.root = catalog.init(self.home / "library")
        self.photos = self.home / "photos"
        self.photos.mkdir()
        png(self.photos / "cup.png", (190, 80, 30))
        png(self.photos / "moon.png", (30, 80, 190))
        catalog.scan(self.root, self.photos)
        con = catalog.connect(self.root)
        ids = {Path(row["path"]).stem: row["id"] for row in con.execute("SELECT id,path FROM assets")}
        con.close()
        recipe = alchemy.create(self.root, ids["cup"], ids["moon"], relation="shape-echo",
                                statement="Similar circles are a creative proposal")
        self.snapshot = alchemy.freeze(self.root, recipe["id"])
        self.video = self.home / "preview.mp4"
        alchemy.render(self.root, self.snapshot, self.video)
        self.receipt = self.video.with_suffix(".mp4.receipt.json")
        self.manifest = self.home / "exchange.json"

    def test_real_render_exports_path_free_replayable_claim(self):
        result = export_alchemy(self.root, self.snapshot, self.video, self.manifest)
        raw = self.manifest.read_bytes()
        manifest = json.loads(raw)
        self.assertEqual(result["schema"], SCHEMA)
        self.assertEqual(result["manifestSha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(manifest["media"]["sha256"], hashlib.sha256(self.video.read_bytes()).hexdigest())
        self.assertEqual(manifest["media"]["byteLength"], self.video.stat().st_size)
        self.assertEqual(manifest["producer"]["receiptSha256"], hashlib.sha256(self.receipt.read_bytes()).hexdigest())
        self.assertEqual(manifest["producer"]["relation"], "shape-echo")
        self.assertEqual(manifest["producer"]["evidenceClass"], "artist_proposed")
        self.assertEqual(len(manifest["producer"]["orderedSources"]), 2)
        self.assertEqual(manifest["authority"]["renderAuthority"], "none")
        self.assertNotIn(str(self.home), raw.decode("utf-8"))
        self.assertNotIn("output_path", manifest)
        self.assertEqual(export_alchemy(self.root, self.snapshot, self.video, self.manifest), result)
        occupied = self.home / "occupied.json"
        occupied.write_text("different")
        with self.assertRaisesRegex(FileExistsError, "refusing overwrite"):
            export_alchemy(self.root, self.snapshot, self.video, occupied)

    def test_mutated_video_refuses_without_export(self):
        self.video.write_bytes(self.video.read_bytes() + b"tamper")
        with self.assertRaisesRegex(ValueError, "Video bytes differ"):
            export_alchemy(self.root, self.snapshot, self.video, self.manifest)
        self.assertFalse(self.manifest.exists())

    def test_forged_receipt_or_mutated_source_refuses(self):
        receipt = json.loads(self.receipt.read_text())
        receipt["segments"][0]["asset_id"] = "asset-" + "f" * 24
        self.receipt.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(ValueError, "segment lineage"):
            export_alchemy(self.root, self.snapshot, self.video, self.manifest)
        self.assertFalse(self.manifest.exists())

    def test_source_mutation_refuses_even_after_completed_video(self):
        (self.photos / "cup.png").write_bytes(b"changed-original")
        with self.assertRaisesRegex(ValueError, "Frozen source missing or changed"):
            export_alchemy(self.root, self.snapshot, self.video, self.manifest)
        self.assertFalse(self.manifest.exists())
