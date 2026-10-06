import copy
import json
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from haunted_blender import mangalize as m, manga_atlas as atlas, manga_quarantine as q, parts_harvester as parts

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "specimens/mangalize-001/lemonpress"
ANCESTOR = ROOT / "specimens/mangalize-001/executed"
PAGE = "works/manga-press-specimen/manga/001/pages/page-05.json"
HANDOFF = "works/manga-press-specimen/manga/001/blender-compatibility-handoff.json"


class QuarantineRelease002Tests(unittest.TestCase):
    def setUp(self):
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            self.skipTest("Pillow required; full experiment CI installs it")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "synthetic-source"
        self.source.mkdir()
        # Independent synthetic pixels and publication identities. No grant in
        # this suite promotes the real pinned 001 founding page or its assets.
        image = Image.new("RGB", (64, 96), "white")
        draw = ImageDraw.Draw(image)
        draw.rectangle((5, 6, 57, 87), fill=(160, 210, 230), outline="black", width=2)
        draw.line((7, 15, 53, 79), fill=(190, 20, 80), width=3)
        image.save(self.source / "synthetic-page.png")
        declaration = {"fictionalTestOnly": True, "id": "unit-test-only:independent-source"}
        m.persist(self.source / "synthetic-source.json", declaration)
        source_binding = m.binding(self.source, self.source / "synthetic-source.json")
        closed = {k: False for k in m.GRANTS}
        page = m.read(SOURCE / PAGE)
        page.update(editionId="synthetic-unit-test:edition", issueId="synthetic-unit-test:issue", pageId="synthetic-page",
                    sourceImage=m.binding(self.source, self.source / "synthetic-page.png"), rightsSource=source_binding,
                    sourceLineage=[source_binding], narrativeReferences=[], dialogueCaptionReferences=[], grants=closed)
        page["pageHash"] = atlas._hash({k: v for k, v in page.items() if k != "pageHash"})
        handoff = m.read(SOURCE / HANDOFF)
        locator = {"workId": "synthetic-unit-test:work", "editionId": page["editionId"],
                   "editionHash": atlas._hash({"fictionalEdition": page["pageHash"]}), "issueId": page["issueId"],
                   "pageId": page["pageId"], "pageHash": page["pageHash"], "sourceImageSha256": page["sourceImage"]["sha256"]}
        handoff.update({k: locator[k] for k in ("workId", "editionId", "editionHash", "issueId")})
        handoff.update(grants=closed, source=source_binding, admission=source_binding, editionAdmission=source_binding,
                       orderingContext={"readingDirection": "ltr", "placements": [], "spreads": []},
                       allowedAdaptationScope=["fictional unit-test geometry only"], pages=[
                           {"identity": locator, "sourceImage": page["sourceImage"], "rightsSource": source_binding, "grants": closed}])
        handoff["handoffHash"] = atlas._hash({k: v for k, v in handoff.items() if k != "handoffHash"})
        m.persist(self.source / "page.json", page)
        m.persist(self.source / "handoff.json", handoff)
        grant = m.source_grant(locator, handoff["handoffHash"], authority_ref="fictional-test:harvest-source-grant",
                               source_repository="synthetic-unit-test/no-real-repository", source_commit="a" * 40)
        m.persist(self.source / "harvest-only.json", grant)
        request = m.make_request(self.source, self.source / "handoff.json", self.source / "page.json", page_id=page["pageId"],
            operations=["harvest"], authority_ref="fictional-test:harvest-request", source_repository="synthetic-unit-test/no-real-repository",
            source_commit="a" * 40, grant_paths=[self.source / "harvest-only.json"])
        admission = m.admit(request, allow=["harvest"], authority_ref="fictional-test:harvest-admission")
        self.ancestor = self.root / "synthetic-harvest"
        m.execute(self.source, request, admission, self.ancestor)
        self.record = q.quarantine_set(self.source, self.ancestor)
        self.ids = [next(r["assetId"] for r in self.record["members"] if r["kind"] == kind)
                    for kind in ("panel", "region-candidate", "edge-mask")]
        self.selection = q.select(self.record, asset_ids=self.ids, authority_ref="fictional-test:selector", reason="three nonsemantic asset kinds")

    def grant(self, ids=None, **permissions):
        rights = {k: k in ("pixelReuse", "derivativeReuse") for k in m.GRANTS}
        rights.update(permissions)
        return q.asset_grant(self.record, self.selection, asset_ids=self.ids if ids is None else ids,
                             permissions=rights, authority_ref="fictional-test:independent-later-grant")

    def executed(self, grant=None):
        grant = self.grant() if grant is None else grant
        out = self.root / "released"
        promotion = q.execute(self.source, self.ancestor, self.record, self.selection, grant, out)
        return grant, promotion, m.read(out / "parts-drawer.json"), out

    def test_quarantine_replay_is_immutable_and_all_dimensions_closed(self):
        other = q.quarantine_set(self.source, self.ancestor)
        self.assertEqual(atlas._stable(self.record), atlas._stable(other))
        self.assertTrue(all(not any(r["effectivePermissions"].values()) for r in self.record["members"]))
        path = self.root / "quarantine.json"
        m.persist(path, self.record)
        m.persist(path, other)
        with self.assertRaisesRegex(ValueError, "create-only"):
            m.persist(path, {"state": "reusable"})

    def test_exact_founding_quarantine_has_25_members_and_known_return(self):
        record = q.quarantine_set(SOURCE, ANCESTOR)
        self.assertEqual(record["memberCount"], 25)
        self.assertEqual(record["ancestorEvent"]["returnHash"], "22c3368039b1e81c196f0acd9e32bfb9fb410ad364ee5c170b7fe8243f5be444")
        self.assertEqual({r["assetId"] for r in record["members"]},
                         {r["id"] for r in m.read(ANCESTOR / "harvest/page-harvest.json")["assets"]})
        self.assertTrue(all(not any(r["effectivePermissions"].values()) for r in record["members"]))

    def test_prepared_founding_selection_is_exact_and_still_grants_nothing(self):
        prepared = ROOT / "specimens/mangalize-002/prepared"
        record, selection = m.read(prepared / "quarantine-set.json"), m.read(prepared / "selection.json")
        q.verify_quarantine(SOURCE, ANCESTOR, record)
        q.verify_selection(record, selection)
        self.assertEqual({r["assetId"] for r in selection["selected"]}, {
            "page-asset:4730b32b3e6a6a201762cb0c", "page-asset:3303923667b99a06c7417376", "page-asset:a622c44b71a723710826149f"})
        self.assertFalse(any(selection["effectivePermissions"].values()))
        self.assertIn("GRANT REQUIRED", (prepared / "TRACE.md").read_text())

    def test_approved_founding_three_promote_and_22_siblings_remain_closed(self):
        root = ROOT / "specimens/mangalize-002"
        record = m.read(root / "prepared/quarantine-set.json")
        selection = m.read(root / "prepared/selection.json")
        grant = m.read(root / "grants/selected-assets.grant.json")
        promotion = m.read(root / "released/promotion.json")
        drawer = m.read(root / "released/parts-drawer.json")
        self.assertEqual(q.verify(SOURCE, ANCESTOR, record, selection, grant, root / "released"), promotion["promotionHash"])
        self.assertEqual(grant["permissions"], {k: k in ("pixelReuse", "derivativeReuse") for k in m.GRANTS})
        expected = {r["assetId"]: r["sha256"] for r in selection["selected"]}
        self.assertEqual({r["id"]: r["sha256"] for r in drawer["artifacts"]}, expected)
        self.assertEqual(drawer["byKind"], {"still": 1, "crop": 1, "mask": 1})
        self.assertEqual(len(promotion["stillQuarantined"]), 22)
        all_ids = {r["assetId"] for r in record["members"]}
        self.assertEqual({r["assetId"] for r in promotion["stillQuarantined"]}, all_ids - set(expected))
        self.assertTrue(all(r["state"] == "quarantined-inspection-only" for r in promotion["stillQuarantined"]))
        for row in drawer["artifacts"]:
            self.assertEqual(row["foreignAncestry"], record["foreignAncestry"])
            for key, value in record["ancestorEvent"].items():
                self.assertEqual(row["provenance"]["eventLineage"][0][key], value)
            self.assertEqual(row["rights"], grant["permissions"])
            self.assertFalse(any(row["authority"].values()))
            self.assertEqual(atlas._file_sha(parts.resolve_drawer_artifact(drawer, row, artifact_root=ANCESTOR)), expected[row["id"]])
        self.assertTrue(all(not any(r["effectivePermissions"].values()) for r in record["members"]))
        self.assertFalse(any(selection["effectivePermissions"].values()))

    def test_actual_material_proposal_witness_retains_every_approved_envelope(self):
        root = ROOT / "specimens/mangalize-002"
        drawer = m.read(root / "released/parts-drawer.json")
        witness = m.read(root / "witnesses/material-proposal-boundary.json")
        self.assertEqual(witness, parts.select_for_stage(drawer, max_per_role=2))
        self.assertEqual(witness["authority"], "proposal-only")
        originals = {row["id"]: row for row in drawer["artifacts"]}
        proposed = [row for rows in witness["selection"].values() for row in rows]
        self.assertEqual({row["assetId"] for row in proposed}, set(originals))
        for row in proposed:
            self.assertEqual(row["provenance"], originals[row["assetId"]]["provenance"])
            self.assertFalse(row["provenance"]["authority"]["staging"])

    def test_all_pinned_001_evidence_is_byte_identical(self):
        pin = m.read(ROOT / "specimens/mangalize-002/ANCESTOR_PIN.json")
        self.assertEqual(pin["commit"], "268d31f4a5283ce96209e3f7957edcfa2df30a7b")
        for row in pin["files"]:
            self.assertEqual(hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest(), row["sha256"], row["path"])

    def test_selection_is_deterministic_order_independent_and_not_authority(self):
        other = q.select(self.record, asset_ids=reversed(self.ids), authority_ref="fictional-test:selector", reason="three nonsemantic asset kinds")
        self.assertEqual(atlas._stable(other), atlas._stable(self.selection))
        self.assertEqual(other["authority"], "selection-only")
        self.assertFalse(any(other["effectivePermissions"].values()))

    def test_selection_requires_explicit_unique_in_set_ids(self):
        for ids in ([], [self.ids[0], self.ids[0]], ["not-a-descendant"]):
            with self.assertRaises(ValueError):
                q.select(self.record, asset_ids=ids, authority_ref="fictional-test:selector", reason="test")

    def test_selection_cannot_self_authorize(self):
        with self.assertRaisesRegex(ValueError, "cannot authorize itself"):
            q.asset_grant(self.record, self.selection, asset_ids=self.ids, permissions=self.grant()["permissions"],
                          authority_ref=self.selection["selectingAuthority"])

    def test_later_grant_is_deterministic_and_binds_exact_page_events_set_selection_sha(self):
        grant = self.grant()
        self.assertEqual(atlas._stable(grant), atlas._stable(self.grant()))
        self.assertEqual(grant["assets"], self.selection["selected"])
        self.assertEqual(grant["foreignAncestry"], self.record["foreignAncestry"])
        self.assertEqual(grant["ancestorEvent"], self.record["ancestorEvent"])
        self.assertEqual(grant["quarantineSetHash"], self.record["quarantineSetHash"])
        self.assertEqual(grant["selectionHash"], self.selection["selectionHash"])

    def test_grant_cannot_expand_to_unselected_sibling_or_regrant_harvest(self):
        other = next(r["assetId"] for r in self.record["members"] if r["assetId"] not in self.ids)
        with self.assertRaisesRegex(ValueError, "exceeds exact selection"):
            self.grant([other])
        with self.assertRaisesRegex(ValueError, "cannot re-grant harvest"):
            self.grant(pixelHarvest=True)

    def test_reuse_only_cannot_derive_or_enter_creative_drawer(self):
        grant = self.grant(derivativeReuse=False)
        q.require_operation(grant, "reuse")
        with self.assertRaisesRegex(ValueError, "derive is not granted"):
            q.promote(self.record, self.selection, grant)
        self.assertFalse((self.root / "released").exists())

    def test_derivative_only_cannot_reuse_or_enter_drawer(self):
        with self.assertRaisesRegex(ValueError, "reuse is not granted"):
            q.promote(self.record, self.selection, self.grant(pixelReuse=False))

    def test_derivative_does_not_grant_publication_motion_or_sound(self):
        grant, promotion, drawer, _ = self.executed()
        for operation in ("publish", "animate", "sound", "harvest", "stage", "render"):
            with self.assertRaisesRegex(ValueError, "not granted"):
                q.require_operation(grant, operation)
        self.assertFalse(any(promotion["authority"].values()))
        self.assertIsNone(promotion["publicationStateChange"])
        for row in drawer["artifacts"]:
            self.assertEqual(row["rights"], {k: k in ("pixelReuse", "derivativeReuse") for k in m.GRANTS})
            self.assertFalse(any(row["authority"].values()))

    def test_exact_asset_bytes_ids_and_recipes_survive_promotion_without_copy(self):
        _, promotion, drawer, out = self.executed()
        originals = {r["assetId"]: r for r in self.record["members"]}
        self.assertEqual(drawer["schema"], parts.DRAWER_SCHEMA)
        self.assertEqual(drawer["byKind"], {"still": 1, "crop": 1, "mask": 1})
        self.assertEqual(promotion["artifactChanges"], [])
        self.assertFalse(list(out.rglob("*.png")))
        for row in drawer["artifacts"]:
            original = originals[row["id"]]
            self.assertEqual(row["sha256"], original["sha256"])
            self.assertEqual(row["recipe"], original["transformRecipe"])
            self.assertEqual(atlas._file_sha(parts.resolve_drawer_artifact(drawer, row, artifact_root=self.ancestor)), row["sha256"])
            self.assertNotEqual(row["id"], row["admittedUseId"])

    def test_complete_foreign_and_local_ancestry_reaches_every_drawer_row(self):
        grant, promotion, drawer, _ = self.executed()
        for row in drawer["artifacts"]:
            envelope = row["provenance"]
            self.assertEqual(envelope["foreignAncestry"], self.record["foreignAncestry"])
            first, later = envelope["eventLineage"]
            for key, value in self.record["ancestorEvent"].items():
                self.assertEqual(first[key], value)
            for key, value in (("quarantineSetHash", self.record["quarantineSetHash"]), ("selectionHash", self.selection["selectionHash"]),
                               ("grantHash", grant["grantHash"]), ("promotionHash", promotion["promotionHash"])):
                self.assertEqual(later[key], value)
            self.assertEqual(envelope["artifact"]["id"], row["id"])
            self.assertEqual(envelope["artifact"]["sha256"], row["sha256"])

    def test_unselected_sibling_and_selected_ungranted_remain_quarantined(self):
        _, promotion, drawer, _ = self.executed(self.grant([self.ids[0]]))
        self.assertEqual(drawer["artifactCount"], 1)
        remaining = {r["assetId"]: r for r in promotion["stillQuarantined"]}
        self.assertEqual(len(remaining), self.record["memberCount"] - 1)
        for asset_id in self.ids[1:]:
            self.assertEqual(remaining[asset_id]["reason"], "selected but not granted")
        crop_sibling = next(r for r in self.record["members"] if r["assetId"] not in self.ids and r["kind"] == "region-candidate")
        self.assertIn("unselected sibling", remaining[crop_sibling["assetId"]]["reason"])
        self.assertFalse(any(crop_sibling["effectivePermissions"].values()))

    def test_only_one_crop_granted_other_crop_same_event_stays_closed(self):
        crops = [r["assetId"] for r in self.record["members"] if r["kind"] == "region-candidate"][:2]
        self.selection = q.select(self.record, asset_ids=crops, authority_ref="fictional-test:selector", reason="sibling geometry test")
        _, promotion, drawer, _ = self.executed(self.grant(crops[:1]))
        self.assertEqual([r["id"] for r in drawer["artifacts"]], crops[:1])
        self.assertTrue(any(r["assetId"] == crops[1] and r["state"] == "quarantined-inspection-only" for r in promotion["stillQuarantined"]))

    def test_old_quarantine_source_harvest_grant_and_event_never_change(self):
        old_source, old_event, old_set = m.tree_bytes(self.source), m.tree_bytes(self.ancestor), atlas._stable(self.record)
        self.executed()
        self.assertEqual(old_source, m.tree_bytes(self.source))
        self.assertEqual(old_event, m.tree_bytes(self.ancestor))
        self.assertEqual(old_set, atlas._stable(self.record))
        q.verify_quarantine(self.source, self.ancestor, self.record)

    def test_original_founding_refusal_and_grant_remain_valid(self):
        request = m.read(ROOT / "specimens/mangalize-001/refusal/mangalize.request.json")
        refusal = m.read(ROOT / "specimens/mangalize-001/refusal/mangalize.admission.json")
        m.verify_request(SOURCE, request)
        m.verify_admission(request, refusal)
        self.assertEqual(refusal["decision"], "refused")
        grant = m.read(SOURCE / "separate-authority/page-05.harvest-only-grant.json")
        self.assertEqual(grant["sourceGrantHash"], "b460c1963adb440fb7af9c8d1b612df7c1baaf95ebd07bc68550184ee78948ff")
        self.assertFalse(grant["grants"]["pixelReuse"])

    def test_parts_drawer_cannot_admit_original_quarantined_harvest(self):
        with self.assertRaises(PermissionError):
            atlas.page_harvest_to_parts_drawer(m.read(self.ancestor / "harvest/page-harvest.json"), self.root / "forbidden.json")

    def test_generic_role_proposal_boundary_preserves_entire_envelope_without_staging(self):
        _, _, drawer, _ = self.executed()
        proposal = parts.select_for_stage(drawer, max_per_role=2)
        self.assertEqual(proposal["authority"], "proposal-only")
        self.assertEqual(proposal["pathBase"], "material-root")
        by_id = {r["id"]: r for r in drawer["artifacts"]}
        selected = [r for values in proposal["selection"].values() for r in values]
        self.assertEqual({r["assetId"] for r in selected}, set(by_id))
        for row in selected:
            self.assertEqual(row["provenance"], by_id[row["assetId"]]["provenance"])
            self.assertFalse(row["provenance"]["authority"]["staging"])
        selected[0]["provenance"]["foreignAncestry"].clear()
        self.assertTrue(by_id[selected[0]["assetId"]]["provenance"]["foreignAncestry"])

    def test_generic_envelope_is_not_lemonpress_specific(self):
        _, _, drawer, _ = self.executed()
        row = drawer["artifacts"][0]
        row["provenance"]["foreignAncestry"] = [{"system": "some-future-system", "opaqueLocator": {"part": "native-17"}}]
        row["provenance"]["futureCustodyExtension"] = {"unknownDimension": "retained"}
        proposal = parts.select_for_stage(drawer, roles=("poster", "texture"), max_per_role=2)
        carried = next(r for values in proposal["selection"].values() for r in values if r["assetId"] == row["id"])
        self.assertEqual(carried["provenance"], row["provenance"])

    def test_existing_001_foreign_drawer_rows_get_generic_envelope(self):
        row = {"id": "generic-asset", "kind": "crop", "sha256": "a" * 64, "sourceSha256": "b" * 64,
               "path": "relative.png", "harvestId": "harvest", "foreignAncestry": [{"opaque": "foreign"}],
               "eventLineage": [{"opaque": "event"}], "recipe": {"crop": [1, 2, 3, 4]}}
        drawer = parts.index_materials([row], source_count=1, harvest_ids=["harvest"], laws=[])
        selected = parts.select_for_stage(drawer, roles=("poster",), max_per_role=1)["selection"]["poster"][0]
        self.assertEqual(selected["assetId"], row["id"])
        self.assertEqual(selected["provenance"]["foreignAncestry"], row["foreignAncestry"])
        self.assertEqual(selected["provenance"]["eventLineage"], row["eventLineage"])

    def test_mismatching_provenance_artifact_refuses(self):
        _, _, drawer, _ = self.executed()
        drawer["artifacts"][0]["provenance"]["artifact"]["sha256"] = "c" * 64
        with self.assertRaisesRegex(ValueError, "identity/SHA mismatch"):
            parts.select_for_stage(drawer, max_per_role=2)

    def test_promotion_drawer_and_trace_deterministic_across_roots(self):
        grant, promotion, drawer, out = self.executed()
        other = self.root / "other-root" / "release"
        replayed = q.execute(self.source, self.ancestor, self.record, self.selection, grant, other)
        self.assertEqual(atlas._stable(replayed), atlas._stable(promotion))
        self.assertEqual(m.tree_bytes(out), m.tree_bytes(other))
        self.assertEqual(q.verify(self.source, self.ancestor, self.record, self.selection, grant, out), promotion["promotionHash"])

    def test_tampered_descendant_refuses_even_though_receipt_exists(self):
        grant, _, drawer, out = self.executed()
        (self.ancestor / drawer["artifacts"][0]["path"]).write_bytes(b"tampered pixels")
        with self.assertRaisesRegex(ValueError, "verification failure"):
            q.verify(self.source, self.ancestor, self.record, self.selection, grant, out)

    def test_rehashed_selection_with_fabricated_sha_refuses(self):
        changed = copy.deepcopy(self.selection)
        changed["selected"][0]["sha256"] = "a" * 64
        changed = q.seal("selection", changed)
        with self.assertRaisesRegex(ValueError, "identities/SHAs"):
            q.verify_selection(self.record, changed)

    def test_tampered_grant_binding_refuses_even_if_rehashed(self):
        for field in ("quarantineSetHash", "selectionHash"):
            changed = self.grant()
            changed[field] = "a" * 64
            with self.assertRaisesRegex(ValueError, "bound source/event"):
                q.verify_grant(self.record, self.selection, q.seal("grant", changed))
        changed = self.grant()
        changed["assets"][0]["sha256"] = "a" * 64
        with self.assertRaisesRegex(ValueError, "bound source/event"):
            q.verify_grant(self.record, self.selection, q.seal("grant", changed))

    def test_tampered_promotion_refuses_after_rehash(self):
        grant, promotion, _, _ = self.executed()
        promotion["promotedAssets"][0]["effectivePermissions"]["publicationReuse"] = True
        with self.assertRaisesRegex(ValueError, "independent authority reconstruction"):
            q.verify_promotion(self.record, self.selection, grant, q.seal("promotion", promotion))

    def test_tampered_persisted_grant_or_drawer_refuses_replay(self):
        grant, _, _, out = self.executed()
        path = out / "asset-grant.json"
        value = m.read(path)
        value["permissions"]["publicationReuse"] = True
        path.write_bytes(atlas._stable(q.seal("grant", value)))
        with self.assertRaisesRegex(ValueError, "persisted event differs"):
            q.verify(self.source, self.ancestor, self.record, self.selection, grant, out)

    def test_rehashed_quarantine_permission_promotion_refuses_external_replay(self):
        record = copy.deepcopy(self.record)
        record["members"][0]["effectivePermissions"]["pixelReuse"] = True
        with self.assertRaisesRegex(ValueError, "independent ancestor replay"):
            q.verify_quarantine(self.source, self.ancestor, q.seal("set", record))

    def test_output_cannot_overwrite_ancestor_evidence(self):
        with self.assertRaisesRegex(ValueError, "cannot write inside ancestor"):
            q.execute(self.source, self.ancestor, self.record, self.selection, self.grant(), self.ancestor / "release")

    def test_complete_synthetic_trace_and_pending_trace_are_distinct(self):
        _, _, _, out = self.executed()
        text = (out / "TRACE.md").read_text()
        for label in ("MANGALIZE EVENT 002", "ANCESTOR EVENT", "LATER GRANT", "PROMOTED", "STILL QUARANTINED", "UNCHANGED", "not admitted"):
            self.assertIn(label, text)
        pending = q.trace(self.record, self.selection)
        self.assertIn("SELECTION READY", pending)
        self.assertIn("GRANT REQUIRED", pending)
        self.assertNotIn("LATER GRANT", pending)

    def test_cli_cannot_mint_grant_and_selection_stops_at_required_boundary(self):
        record_path, selection_path = self.root / "quarantine.json", self.root / "selection.json"
        m.persist(record_path, self.record)
        args = [sys.executable, "-m", "haunted_blender.manga_quarantine_cli", "select", str(record_path), str(selection_path),
                "--source-root", str(self.source), "--ancestor-event", str(self.ancestor),
                "--authority-ref", "fictional-test:selector", "--reason", "CLI geometry test"]
        for asset_id in self.ids:
            args.extend(["--candidate", asset_id])
        result = subprocess.run(args, capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("GRANT REQUIRED", result.stdout)
        self.assertFalse(any(m.read(selection_path)["effectivePermissions"].values()))
        self.assertFalse((self.root / "asset-grant.json").exists())


if __name__ == "__main__":
    unittest.main()
