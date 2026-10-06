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

    def test_dark_border_layout_falls_back_when_white_gutters_are_absent(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "bordered.png"
            image = self.Image.new("RGB", (420, 620), (222, 218, 210))
            draw = self.ImageDraw.Draw(image)
            # Four touching panel fields: no white gutter, only continuous dark borders.
            draw.rectangle((0, 0, 209, 309), fill=(232, 220, 205), outline=(15, 15, 15), width=6)
            draw.rectangle((210, 0, 419, 309), fill=(210, 225, 235), outline=(15, 15, 15), width=6)
            draw.rectangle((0, 310, 209, 619), fill=(235, 210, 220), outline=(15, 15, 15), width=6)
            draw.rectangle((210, 310, 419, 619), fill=(218, 235, 216), outline=(15, 15, 15), width=6)
            image.save(source)

            manifest = manga_atlas.source_manifest(
                source,
                source_class="reference",
                pixel_reuse=False,
                derivative_reuse=False,
                publication_reuse=False,
                grammar_families=["panel-rhythm"],
            )
            report = manga_atlas.analyze_page(manifest)
            self.assertGreaterEqual(report["panelCount"], 4)
            self.assertIn(
                "WHITE GUTTER AND DARK BORDER DETECTION ARE BOTH HEURISTICS",
                report["laws"],
            )

    def test_owned_page_harvest_can_drop_into_existing_008h_parts_drawer(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "owned.png"
            self.make_page(source, mode="irregular")
            manifest = manga_atlas.source_manifest(
                source,
                source_class="owned",
                pixel_reuse=True,
                derivative_reuse=True,
                publication_reuse=True,
                grammar_families=["cozy-ensemble", "room-ecology"],
                rights_note="Synthetic owned fixture.",
            )
            harvest = manga_atlas.harvest_page(manifest, root / "harvest")
            drawer = manga_atlas.page_harvest_to_parts_drawer(
                harvest, root / "parts-drawer.json"
            )
            self.assertEqual(drawer["schema"], "haunted-blender/parts-drawer/v1")
            self.assertEqual(drawer["sourceCount"], 1)
            self.assertGreater(drawer["artifactCount"], 0)
            self.assertIn("still", drawer["byKind"])
            self.assertIn("crop", drawer["byKind"])
            self.assertIn("mask", drawer["byKind"])
            self.assertTrue(all(
                row["sourceSha256"] == manifest["sourceSha256"]
                for row in drawer["artifacts"]
            ))
            self.assertTrue(all(
                row["harvestId"] == harvest["id"]
                for row in drawer["artifacts"]
            ))

    def test_multi_page_sequence_grammar_preserves_roles_continuity_and_recurring_motifs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pages = []
            configs = [
                ("a.png", "establish", ["door", "room"], 0),
                ("b.png", "dialogue", ["door", "chair"], 1),
                ("c.png", "threshold", ["door", "light"], 2),
                ("d.png", "return", ["door", "room"], 3),
            ]
            for name, role, motifs, index in configs:
                path = root / name
                self.make_page(path, mode="irregular" if index % 2 else "grid")
                manifest = manga_atlas.source_manifest(
                    path,
                    source_class="reference",
                    pixel_reuse=False,
                    derivative_reuse=False,
                    publication_reuse=False,
                    grammar_families=["panel-rhythm", "sequence-rhythm"],
                    page_role=role,
                    continuity_group="room-001",
                    motifs=motifs,
                    sequence_index=index,
                )
                pages.append(manga_atlas.analyze_page(manifest))

            sequence = manga_atlas.build_sequence_grammar(pages)
            self.assertEqual(
                [row["pageRole"] for row in sequence["pages"]],
                ["establish", "dialogue", "threshold", "return"],
            )
            self.assertEqual(len(sequence["transitions"]), 3)
            self.assertTrue(all(
                row["sameContinuityGroup"] for row in sequence["transitions"]
            ))
            self.assertIn("door", sequence["recurringMotifs"])
            self.assertEqual(len(sequence["recurringMotifs"]["door"]), 4)

    def test_sequence_director_maps_page_roles_to_reusable_shot_patterns(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            reports = []
            for index, role in enumerate(("establish", "dialogue", "vertical-transition", "return")):
                path = root / f"{index}.png"
                self.make_page(path, mode="irregular")
                manifest = manga_atlas.source_manifest(
                    path,
                    source_class="reference",
                    pixel_reuse=False,
                    derivative_reuse=False,
                    publication_reuse=False,
                    grammar_families=["sequence-rhythm"],
                    page_role=role,
                    continuity_group="world-a",
                    motifs=["window"] if index in (0, 3) else [],
                    sequence_index=index,
                )
                reports.append(manga_atlas.analyze_page(manifest))

            sequence = manga_atlas.build_sequence_grammar(reports)
            prescription = manga_atlas.sequence_director_prescription(sequence)
            self.assertEqual(
                [row["pageRole"] for row in prescription["beats"]],
                ["establish", "dialogue", "vertical-transition", "return"],
            )
            self.assertEqual(
                prescription["beats"][0]["suggestedShotPattern"],
                ["ESTABLISH", "WIDE"],
            )
            self.assertIn("TWO_SHOT", prescription["beats"][1]["suggestedShotPattern"])
            self.assertIn("LYRIC_WORLD", prescription["beats"][2]["suggestedShotPattern"])
            self.assertIn("window", prescription["callbackMotifs"])
            self.assertTrue(all(
                row["authority"] == "sequence-grammar-proposal-only"
                for row in prescription["beats"]
            ))

    def test_registered_owned_drive_collection_and_exact_snapshot_cover_fifteen_pages(self):
        root = Path(__file__).resolve().parents[1]
        collection = json.loads(
            (
                root
                / "specimens"
                / "008m"
                / "static-collective-owned-page-collection-001.json"
            ).read_text(encoding="utf-8")
        )
        batch = json.loads(
            (
                root
                / "specimens"
                / "008m"
                / "static-collective-owned-page-batch-snapshot-001.json"
            ).read_text(encoding="utf-8")
        )

        self.assertEqual(
            collection["schema"],
            "haunted-blender/page-source-collection/v1",
        )
        self.assertEqual(collection["sourceClass"], "owned")
        self.assertTrue(collection["futureMembersInherit"])
        self.assertEqual(collection["memberCount"], 15)
        self.assertEqual(len(collection["memberSnapshot"]), 15)
        self.assertTrue(collection["rights"]["pixelReuse"])
        self.assertTrue(collection["rights"]["derivativeReuse"])
        self.assertTrue(collection["rights"]["publicationReuse"])

        self.assertEqual(batch["schema"], "haunted-blender/page-source-batch/v1")
        self.assertEqual(batch["sourceClass"], "owned")
        self.assertEqual(batch["pageCount"], 15)
        self.assertEqual(len(batch["entries"]), 15)
        self.assertEqual(
            len({row["sha256"] for row in batch["entries"]}),
            15,
        )
        self.assertTrue(
            all(len(row["sha256"]) == 64 for row in batch["entries"])
        )
        self.assertIn("INGEST ORDER != STORY ORDER", batch["laws"])

    def test_owned_batch_runs_exact_bytes_through_reports_harvest_and_combined_drawer(self):
        import hashlib

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source_dir = root / "source"
            source_dir.mkdir()
            entries = []
            for index, mode in enumerate(("grid", "irregular", "grid")):
                path = source_dir / f"page-{index:02d}.png"
                self.make_page(path, mode=mode)
                if index == 2:
                    image = self.Image.open(path).convert("RGB")
                    image.putpixel((10, 10), (123, 45, 67))
                    image.save(path)
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                with self.Image.open(path) as image:
                    width, height = image.size
                entries.append({
                    "filename": path.name,
                    "sha256": digest,
                    "width": width,
                    "height": height,
                    "byteLength": path.stat().st_size,
                    "sequenceIndex": index,
                    "pageRole": None,
                    "motifs": [],
                    "grammarFamilies": [
                        "cozy-ensemble",
                        "panel-rhythm",
                        "sequence-rhythm",
                    ],
                    "label": f"Owned Page {index + 1}",
                })

            batch = manga_atlas.owned_batch_manifest(
                entries,
                label="Synthetic Owned Batch",
                rights_note="Synthetic fixture is fully owned for test reuse.",
                continuity_group="fixture-room",
                grammar_families=[
                    "cozy-ensemble",
                    "panel-rhythm",
                    "sequence-rhythm",
                ],
            )
            result = manga_atlas.run_owned_batch(
                batch,
                source_dir,
                root / "run",
            )
            self.assertEqual(result["pageCount"], 3)
            self.assertEqual(result["providerCredits"], 0)
            self.assertEqual(result["usdMicros"], 0)
            self.assertGreater(result["artifactCount"], 3)
            self.assertTrue((root / "run" / "parts-drawer.combined.json").is_file())
            self.assertTrue((root / "run" / "manga-anime-atlas.json").is_file())
            self.assertTrue((root / "run" / "page-sequence-grammar.json").is_file())

            combined = json.loads(
                (root / "run" / "parts-drawer.combined.json").read_text()
            )
            self.assertEqual(combined["sourceCount"], 3)
            self.assertEqual(combined["ownedBatchId"], batch["id"])
            self.assertTrue(all(
                row["ownedBatchId"] == batch["id"]
                for row in combined["artifacts"]
            ))
            self.assertTrue(all(
                len(row["sourceSha256"]) == 64
                for row in combined["artifacts"]
            ))

    def test_owned_batch_refuses_bytes_that_no_longer_match_frozen_hash(self):
        import hashlib

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source_dir = root / "source"
            source_dir.mkdir()
            path = source_dir / "page.png"
            self.make_page(path)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            with self.Image.open(path) as image:
                width, height = image.size

            batch = manga_atlas.owned_batch_manifest(
                [{
                    "filename": path.name,
                    "sha256": digest,
                    "width": width,
                    "height": height,
                    "sequenceIndex": 0,
                }],
                label="Frozen Bytes",
                rights_note="Synthetic fixture.",
                grammar_families=["panel-rhythm"],
            )

            image = self.Image.open(path).convert("RGB")
            image.putpixel((0, 0), (1, 2, 3))
            image.save(path)

            with self.assertRaisesRegex(ValueError, "SHA mismatch"):
                manga_atlas.run_owned_batch(
                    batch,
                    source_dir,
                    root / "run",
                )

    def test_owned_collection_inherits_full_reuse_to_current_member_after_sha_ingest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "member.png"
            self.make_page(source)
            collection = manga_atlas.collection_manifest(
                label="Owned manga collection",
                collection_id="owned-001",
                collection_url="",
                source_class="owned",
                pixel_reuse=True,
                derivative_reuse=True,
                publication_reuse=True,
                rights_note="User-declared owned collection.",
                member_snapshot=[{"externalId": "member.png", "title": "member.png"}],
                future_members_inherit=True,
            )
            manifest = manga_atlas.source_from_collection(
                source,
                collection,
                external_id="member.png",
                grammar_families=["cozy-ensemble"],
                page_role="dialogue",
            )
            self.assertEqual(manifest["sourceClass"], "owned")
            self.assertTrue(manifest["rights"]["pixelReuse"])
            self.assertTrue(manifest["rights"]["derivativeReuse"])
            self.assertTrue(manifest["rights"]["publicationReuse"])
            self.assertTrue(manifest["rightsInheritedFromCollection"])
            self.assertEqual(manifest["externalMemberId"], "member.png")
            self.assertEqual(len(manifest["sourceSha256"]), 64)

    def test_future_member_inherits_collection_rights_but_still_gets_its_own_sha(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            old = root / "old.png"
            new = root / "new.png"
            self.make_page(old, mode="grid")
            self.make_page(new, mode="irregular")
            collection = manga_atlas.collection_manifest(
                label="Growing owned manga collection",
                collection_id="owned-growing",
                collection_url="",
                source_class="owned",
                pixel_reuse=True,
                derivative_reuse=True,
                publication_reuse=True,
                rights_note="User declares current and future deliberate folder members owned.",
                member_snapshot=[{"externalId": "old.png", "title": "old.png"}],
                future_members_inherit=True,
            )
            manifest = manga_atlas.source_from_collection(
                new,
                collection,
                external_id="new.png",
                grammar_families=["sequence-rhythm"],
                observed_membership=True,
            )
            self.assertTrue(manifest["rightsInheritedFromCollection"])
            self.assertEqual(manifest["externalMemberId"], "new.png")
            self.assertEqual(len(manifest["sourceSha256"]), 64)
            self.assertNotEqual(manifest["sourceSha256"], manga_atlas._file_sha(old))

    def test_future_member_requires_membership_witness_even_when_collection_inherits(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "new.png"
            self.make_page(source)
            collection = manga_atlas.collection_manifest(
                label="Growing owned collection",
                collection_id="growing-guard",
                collection_url="",
                source_class="owned",
                pixel_reuse=True,
                derivative_reuse=True,
                publication_reuse=True,
                rights_note="Future deliberate folder members are owned.",
                member_snapshot=[],
                future_members_inherit=True,
            )
            with self.assertRaisesRegex(PermissionError, "membership witness"):
                manga_atlas.source_from_collection(
                    source,
                    collection,
                    external_id="new.png",
                )

    def test_future_member_is_refused_when_collection_policy_does_not_inherit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "new.png"
            self.make_page(source)
            collection = manga_atlas.collection_manifest(
                label="Frozen collection",
                collection_id="frozen-001",
                collection_url="",
                source_class="owned",
                pixel_reuse=True,
                derivative_reuse=True,
                publication_reuse=True,
                rights_note="Only snapshotted members are authorized.",
                member_snapshot=[{"externalId": "old.png", "title": "old.png"}],
                future_members_inherit=False,
            )
            with self.assertRaises(PermissionError):
                manga_atlas.source_from_collection(
                    source,
                    collection,
                    external_id="new.png",
                )

    def test_undersegmented_owned_page_gets_nonsemantic_quarry_tiles_and_drawer_crops(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "single-field.png"
            image = self.Image.new("RGB", (420, 620), (222, 218, 210))
            draw = self.ImageDraw.Draw(image)
            # One continuous illustration field with no panel gutters/borders.
            draw.ellipse((80, 90, 330, 360), fill=(80, 70, 95))
            draw.rectangle((40, 420, 380, 560), fill=(180, 155, 120))
            image.save(source)

            manifest = manga_atlas.source_manifest(
                source,
                source_class="owned",
                pixel_reuse=True,
                derivative_reuse=True,
                publication_reuse=True,
                grammar_families=["panel-rhythm"],
                rights_note="Synthetic owned fixture.",
            )
            report = manga_atlas.analyze_page(manifest)
            self.assertLessEqual(report["panelCount"], 2)
            self.assertEqual(report["panelMapStatus"], "undersegmented")
            self.assertTrue(report["quarryRecommended"])

            harvest = manga_atlas.harvest_page(
                manifest,
                root / "harvest",
            )
            self.assertEqual(harvest["panelMapStatus"], "undersegmented")
            self.assertEqual(harvest["quarryCandidateCount"], 18)
            quarry = [
                row for row in harvest["assets"]
                if row["kind"] == "quarry-candidate"
            ]
            self.assertEqual(len(quarry), 18)
            self.assertTrue(all(
                row["recipe"]["semantic"] is False
                for row in quarry
            ))

            drawer = manga_atlas.page_harvest_to_parts_drawer(
                harvest,
                root / "parts-drawer.json",
            )
            quarry_crops = [
                row for row in drawer["artifacts"]
                if row["pageAssetKind"] == "quarry-candidate"
            ]
            self.assertEqual(len(quarry_crops), 18)
            self.assertTrue(all(row["kind"] == "crop" for row in quarry_crops))

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
