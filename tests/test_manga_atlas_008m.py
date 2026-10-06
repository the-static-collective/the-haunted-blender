import json
import tempfile
import unittest
from pathlib import Path

from haunted_blender import manga_atlas


class MangaAnimeGrammarAtlas008mTests(unittest.TestCase):
    def setUp(self):
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            self.skipTest("Pillow required")
        self.Image = Image
        self.ImageDraw = ImageDraw

    def make_page(self, path: Path, *, mode="grid"):
        image = self.Image.new("RGB", (420, 620), "white")
        draw = self.ImageDraw.Draw(image)
        if mode == "grid":
            boxes = [
                (20, 20, 200, 290),
                (220, 20, 400, 290),
                (20, 320, 200, 600),
                (220, 320, 400, 600),
            ]
        else:
            boxes = [
                (20, 20, 400, 180),
                (20, 210, 185, 440),
                (215, 210, 400, 440),
                (20, 470, 400, 600),
            ]
        fills = [(232, 220, 205), (210, 225, 235), (235, 210, 220), (218, 235, 216)]
        for index, (box, fill) in enumerate(zip(boxes, fills)):
            draw.rectangle(box, fill=fill, outline=(25, 25, 25), width=4)
            x1, y1, x2, y2 = box
            # Non-semantic internal marks make the regions comic-like without
            # destroying the white gutters used by XY-cut segmentation.
            draw.ellipse(
                (x1 + 30, y1 + 35, min(x2 - 25, x1 + 95), min(y2 - 20, y1 + 105)),
                fill=(75 + index * 20, 70, 85),
            )
            draw.line(
                (x1 + 25, y2 - 40, x2 - 25, y2 - 55),
                fill=(45, 45, 45),
                width=5,
            )
        image.save(path)

    def test_reference_source_allows_grammar_analysis_but_refuses_pixel_harvest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "reference.png"
            self.make_page(source)
            manifest = manga_atlas.source_manifest(
                source,
                source_class="reference",
                pixel_reuse=False,
                derivative_reuse=False,
                publication_reuse=False,
                grammar_families=["anime-action", "reaction"],
                label="Reference anime grammar specimen",
            )
            report = manga_atlas.analyze_page(manifest)
            self.assertEqual(report["sourceClass"], "reference")
            self.assertGreaterEqual(report["panelCount"], 4)
            self.assertEqual(report["sourceSha256"], manifest["sourceSha256"])
            with self.assertRaises(PermissionError):
                manga_atlas.harvest_page(manifest, root / "harvest")

    def test_owned_source_can_be_disassembled_into_traceable_panel_assets(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "owned.png"
            self.make_page(source)
            manifest = manga_atlas.source_manifest(
                source,
                source_class="owned",
                pixel_reuse=True,
                derivative_reuse=True,
                publication_reuse=True,
                grammar_families=["cozy-ensemble", "room-ecology", "panel-rhythm"],
                rights_note="User states this page and its generated pixels are fully theirs to reuse.",
                label="Owned cozy ensemble specimen",
            )
            harvest = manga_atlas.harvest_page(manifest, root / "harvest")
            self.assertGreaterEqual(harvest["panelCount"], 4)
            self.assertGreater(harvest["assetCount"], harvest["panelCount"])
            self.assertEqual(harvest["providerCredits"], 0)
            self.assertEqual(harvest["rights"]["pixelReuse"], True)
            for row in harvest["assets"]:
                self.assertEqual(row["sourceSha256"], manifest["sourceSha256"])
                self.assertTrue(Path(row["path"]).is_file())
                self.assertEqual(len(row["sha256"]), 64)

    def test_panel_map_is_geometry_only_and_emits_varied_panel_shapes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "irregular.png"
            self.make_page(source, mode="irregular")
            manifest = manga_atlas.source_manifest(
                source,
                source_class="owned",
                pixel_reuse=True,
                derivative_reuse=True,
                publication_reuse=True,
                grammar_families=["panel-rhythm"],
                rights_note="Synthetic owned test fixture.",
            )
            report = manga_atlas.analyze_page(manifest)
            geometries = {row["geometry"] for row in report["panels"]}
            self.assertGreaterEqual(report["panelCount"], 4)
            self.assertTrue({"wide", "tall"} & geometries)
            self.assertIn("PANEL MAP IS GEOMETRY, NOT SEMANTIC UNDERSTANDING", report["laws"])

    def test_atlas_keeps_ownership_separate_while_aggregating_grammar(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            owned = root / "owned.png"
            reference = root / "reference.png"
            self.make_page(owned, mode="irregular")
            self.make_page(reference, mode="grid")
            owned_manifest = manga_atlas.source_manifest(
                owned,
                source_class="owned",
                pixel_reuse=True,
                derivative_reuse=True,
                publication_reuse=True,
                grammar_families=["cozy-ensemble", "panel-rhythm"],
                rights_note="Synthetic owned fixture.",
            )
            ref_manifest = manga_atlas.source_manifest(
                reference,
                source_class="reference",
                pixel_reuse=False,
                derivative_reuse=False,
                publication_reuse=False,
                grammar_families=["anime-action", "panel-rhythm"],
            )
            a = manga_atlas.analyze_page(owned_manifest)
            b = manga_atlas.analyze_page(ref_manifest)
            atlas = manga_atlas.build_atlas([a, b])
            self.assertEqual(atlas["schema"], manga_atlas.ATLAS_SCHEMA)
            self.assertIn("cozy-ensemble", atlas["families"])
            self.assertIn("anime-action", atlas["families"])
            self.assertEqual(
                len(atlas["families"]["panel-rhythm"]["sourceReports"]),
                2,
            )
            self.assertIn("OWNERSHIP DOES NOT TRANSFER BETWEEN SOURCES", atlas["laws"])

    def test_panel_geometry_can_propose_director_rhythm_without_becoming_authority(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "page.png"
            self.make_page(source, mode="irregular")
            manifest = manga_atlas.source_manifest(
                source,
                source_class="reference",
                pixel_reuse=False,
                derivative_reuse=False,
                publication_reuse=False,
                grammar_families=["anime-action", "panel-rhythm"],
            )
            report = manga_atlas.analyze_page(manifest)
            prescription = manga_atlas.director_prescription(report)
            self.assertEqual(
                len(prescription["shots"]),
                report["panelCount"],
            )
            self.assertTrue(all(
                row["authority"] == "grammar-proposal-only"
                for row in prescription["shots"]
            ))
            self.assertTrue(all(
                row["suggestedShot"] in {
                    "WIDE", "CLOSE_UP", "SPEAKER", "INSERT", "REACTION", "RETURN"
                }
                for row in prescription["shots"]
            ))

    def test_reference_manifest_cannot_self_grant_reuse_rights(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "page.png"
            self.make_page(source)
            with self.assertRaises(ValueError):
                manga_atlas.source_manifest(
                    source,
                    source_class="reference",
                    pixel_reuse=True,
                    derivative_reuse=True,
                    publication_reuse=False,
                    grammar_families=["anime-action"],
                )


if __name__ == "__main__":
    unittest.main()
