import json
import shutil
import tempfile
import unittest
from pathlib import Path

from haunted_blender import narrative_performance, owned_pixel_film


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "specimens" / "008n" / "bus-page-5-a-page-you-can-hear-001.json"
DONOR = ROOT / "specimens" / "008p" / "static-collective-bus-signal-001.donor.json"


class OwnedPixelMangaFilm008pTests(unittest.TestCase):
    def setUp(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("FFmpeg and FFprobe required")
        try:
            from PIL import Image  # noqa: F401
        except ImportError:
            self.skipTest("Pillow required")

    def test_exact_owned_derivative_decodes_and_matches_manifest(self):
        donor = owned_pixel_film.load_donor(DONOR)
        manifest = donor["manifest"]
        self.assertEqual(
            donor["derivativeSha256"],
            "7842a139f34bb5f35ca800d88ee5a7a263758f6f709b063f23f17701e47572cd",
        )
        self.assertEqual(donor["image"].size, (160, 90))
        self.assertEqual(
            manifest["sourceSha256"],
            "c9ee8d9956e8a469082be0b181b0265271465aaba908b9f6c5412302207fc41c",
        )
        self.assertEqual(
            manifest["collectionId"],
            "1n7NfchXgOO9fJMeqTymnV-GW2niBb43v",
        )

    def test_tampered_derivative_sha_refuses_before_render(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = json.loads(DONOR.read_text(encoding="utf-8"))
            source_b64 = (
                ROOT / "specimens" / "008p" / "static-collective-bus-signal-001.jpg.b64"
            )
            local_b64 = root / "donor.jpg.b64"
            local_b64.write_text(source_b64.read_text(encoding="utf-8"), encoding="utf-8")
            manifest["derivative"]["path"] = "specimens/008p/donor.jpg.b64"
            manifest["derivative"]["sha256"] = "0" * 64

            # Recreate the expected <repo>/specimens/008p layout in temp.
            fake_repo = root / "repo"
            target_dir = fake_repo / "specimens" / "008p"
            target_dir.mkdir(parents=True)
            (target_dir / "donor.jpg.b64").write_text(
                source_b64.read_text(encoding="utf-8"), encoding="utf-8"
            )
            manifest_path = target_dir / "donor.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "SHA mismatch"):
                owned_pixel_film.load_donor(manifest_path)

    def test_page_five_renders_real_owned_pixel_audio_video(self):
        with tempfile.TemporaryDirectory() as td:
            result = owned_pixel_film.render_spec(
                SPEC, DONOR, Path(td) / "render",
                width=320, height=180, fps=6,
            )
            movie = Path(result["movie"])
            receipt = result["receipt"]
            self.assertTrue(movie.is_file())
            self.assertGreater(movie.stat().st_size, 1000)
            self.assertEqual(receipt["schema"], owned_pixel_film.RECEIPT_SCHEMA)
            self.assertEqual(receipt["beatCount"], 8)
            self.assertTrue(receipt["hasAudio"])
            self.assertEqual(receipt["ownedPixelFrames"], receipt["frameCount"])
            self.assertGreaterEqual(receipt["durationSeconds"], 6.70)
            self.assertLessEqual(receipt["durationSeconds"], 6.90)
            self.assertEqual(receipt["externalGenerations"], 0)
            self.assertEqual(receipt["providerCredits"], 0)
            self.assertEqual(receipt["usdMicros"], 0)

    def test_every_beat_keeps_narrative_hash_and_pixel_donor_hash(self):
        spec = narrative_performance.read_spec(SPEC)
        bundle = narrative_performance.compile_spec(spec)
        with tempfile.TemporaryDirectory() as td:
            result = owned_pixel_film.render_spec(
                SPEC, DONOR, Path(td) / "render",
                width=320, height=180, fps=6,
            )
        expected = {
            row["id"]: row["sourceParticularHash"]
            for row in bundle["plan"]["beats"]
        }
        for row in result["receipt"]["beats"]:
            self.assertEqual(row["sourceParticularHash"], expected[row["beatId"]])
            self.assertEqual(
                row["pixelDonorDerivativeSha256"],
                result["receipt"]["donorDerivativeSha256"],
            )
            self.assertFalse(row["semanticSegmentationClaim"])

    def test_donor_pixels_do_not_become_narrative_authority(self):
        with tempfile.TemporaryDirectory() as td:
            result = owned_pixel_film.render_spec(
                SPEC, DONOR, Path(td) / "render",
                width=320, height=180, fps=6,
            )
        laws = result["receipt"]["laws"]
        self.assertIn("PIXEL DONOR != NARRATIVE AUTHORITY", laws)
        self.assertIn("STAGING CROP != SEMANTIC SEGMENTATION", laws)
        self.assertIn(
            "EVERY RENDERED FRAME CONTAINS ADMITTED DONOR PIXELS", laws
        )


if __name__ == "__main__":
    unittest.main()
