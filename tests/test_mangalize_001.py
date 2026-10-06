import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from haunted_blender import mangalize as m, manga_atlas as atlas, parts_harvester

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "specimens/mangalize-001/lemonpress"
HANDOFF = "works/manga-press-specimen/manga/001/blender-compatibility-handoff.json"
PAGE = "works/manga-press-specimen/manga/001/pages/page-05.json"
COMMIT = "88978ff88f9b07a72040976b426b04afc2abd835"


class Mangalize001Tests(unittest.TestCase):
    def setUp(self):
        try:
            import PIL
        except ImportError:
            self.skipTest("Pillow required; full MANGALIZE CI installs the pinned dependency")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.evidence = self.root / "evidence"
        shutil.copytree(EVIDENCE, self.evidence)
        self.handoff = m.read(self.evidence / HANDOFF)
        self.identity = self.handoff["pages"][0]["identity"]

    def request(self, *, supplemental=True, operations=("harvest",), target="page-quarry", authorized=False):
        grant_paths = []
        handoff_path, page_path = self.evidence / HANDOFF, self.evidence / PAGE
        if authorized:
            # Independent fictional permission case, NOT the pinned handoff or
            # the user-approved harvest-only event. Proves the optional drawer
            # door only under separate full synthetic rights.
            page = m.read(page_path)
            page["grants"]["pixelHarvest"] = True
            page["pageHash"] = atlas._hash({k: v for k, v in page.items() if k != "pageHash"})
            handoff = copy.deepcopy(self.handoff)
            handoff["grants"]["pixelHarvest"] = True
            handoff["pages"][0]["grants"]["pixelHarvest"] = True
            handoff["pages"][0]["identity"]["pageHash"] = page["pageHash"]
            handoff["handoffHash"] = atlas._hash({k: v for k, v in handoff.items() if k != "handoffHash"})
            self.identity = handoff["pages"][0]["identity"]
            handoff_path, page_path = self.evidence / "test-only-authorized-handoff.json", self.evidence / "test-only-authorized-page.json"
            m.persist(handoff_path, handoff)
            m.persist(page_path, page)
            supplemental = False
        if supplemental:
            # Explicitly fictional authority used for unit tests only. The real
            # founding execution needs an independently supplied source grant.
            path = self.evidence / "test-only-harvest-grant.json"
            grant = m.source_grant(self.identity, self.handoff["handoffHash"], authority_ref="synthetic-unit-test:harvest-only", source_commit=COMMIT)
            m.persist(path, grant)
            grant_paths = [path]
        return m.make_request(self.evidence, handoff_path, page_path, page_id="page-05",
            authority_ref="synthetic-unit-test:requester", source_commit=COMMIT, grant_paths=grant_paths, operations=operations, target=target)

    def admission(self, request, allow=("harvest",)):
        return m.admit(request, allow=allow, authority_ref="synthetic-unit-test:independent-admitter")

    def run_event(self, *, allow=("harvest", "reuse", "derive")):
        request = self.request(operations=allow, authorized=any(op in allow for op in ("reuse", "derive")))
        admission = self.admission(request, allow)
        out = self.root / "event"
        returned = m.execute(self.evidence, request, admission, out)
        return request, admission, returned, out

    def inventory(self):
        return m.tree_bytes(self.evidence)

    def test_event_is_immutable_explicit_verb_not_property(self):
        request, admission, returned, out = self.run_event()
        for kind, record in (("request", request), ("admission", admission), ("execution", m.read(out / "mangalize.execution.json")), ("return", returned)):
            m.verify_event(kind, record)
            self.assertEqual(record["verb"], "MANGALIZE")
            self.assertNotIn("mangalized", record)
        with self.assertRaisesRegex(ValueError, "create-only"):
            m.persist(out / "mangalize.request.json", {"mangalized": True})

    def test_deterministic_request_and_admission_replay(self):
        a, b = self.request(), self.request()
        self.assertEqual(atlas._stable(a), atlas._stable(b))
        self.assertEqual(atlas._stable(self.admission(a)), atlas._stable(self.admission(b)))

    def test_execution_and_return_replay_across_locations_byte_identical(self):
        request, admission, returned, a = self.run_event()
        b = self.root / "different-host-path" / "event"
        other = m.execute(self.evidence, request, admission, b)
        self.assertEqual(atlas._stable(returned), atlas._stable(other))
        self.assertEqual(m.tree_bytes(a), m.tree_bytes(b))
        self.assertEqual(returned["returnHash"], m.verify(self.evidence, request, admission, a))
        m.execute(self.evidence, request, admission, a)

    def test_foreign_source_root_does_not_change_event_identity(self):
        request, admission, returned, out = self.run_event()
        other_root = self.root / "another-machine" / "source"
        shutil.copytree(self.evidence, other_root)
        another = self.root / "another-machine" / "event"
        replayed = m.execute(other_root, request, admission, another)
        self.assertEqual(returned["returnHash"], replayed["returnHash"])
        self.assertEqual(m.tree_bytes(out), m.tree_bytes(another))

    def test_original_pinned_handoff_refuses_harvest_despite_reuse(self):
        request = self.request(supplemental=False)
        self.assertTrue(request["suppliedGrants"]["pixelReuse"])
        self.assertTrue(request["suppliedGrants"]["derivativeReuse"])
        self.assertFalse(request["suppliedGrants"]["pixelHarvest"])
        with self.assertRaisesRegex(ValueError, "pixelHarvest"):
            self.admission(request)
        refusal = m.decide(request, allow=["harvest"], authority_ref="synthetic-test:refusing-admitter")
        self.assertEqual(refusal["decision"], "refused")
        m.verify_admission(request, refusal)
        with self.assertRaisesRegex(ValueError, "refused admission"):
            m.execute(self.evidence, request, refusal, self.root / "refused-event")
        self.assertFalse((self.root / "refused-event").exists())

    def test_existing_008m_cannot_bypass_the_closed_foreign_harvest_door(self):
        request = self.request(supplemental=False, operations=["analyze", "reuse", "derive"])
        admission = self.admission(request, ["analyze", "reuse", "derive"])
        source = m.adapt_page(self.evidence, request, admission)
        self.assertTrue(source["rights"]["pixelReuse"])
        self.assertTrue(source["rights"]["derivativeReuse"])
        self.assertFalse(source["rights"]["pixelHarvest"])
        atlas.analyze_page(source, source_root=self.evidence)
        with self.assertRaisesRegex(PermissionError, "independent pixelHarvest"):
            atlas.harvest_page(source, self.root / "forbidden-quarry", source_root=self.evidence)
        # Stripping the explicit bit cannot invoke legacy 008m authority.
        del source["rights"]["pixelHarvest"]
        with self.assertRaisesRegex(PermissionError, "independent pixelHarvest"):
            atlas.harvest_page(source, self.root / "forbidden-quarry", source_root=self.evidence)

    def test_source_class_vocabulary_cannot_create_derivative_permission(self):
        request = self.request(operations=["harvest", "reuse"], authorized=True)
        admission = self.admission(request, ["harvest", "reuse"])
        source = m.adapt_page(self.evidence, request, admission)
        self.assertEqual(source["sourceClass"], "licensed")
        self.assertFalse(source["rights"]["derivativeReuse"])
        self.assertFalse(source["rights"]["publicationReuse"])

    def test_request_cannot_promote_permission_even_if_rehashed(self):
        request = self.request(supplemental=False)
        request["suppliedGrants"]["pixelHarvest"] = True
        request = m.seal("request", request)
        with self.assertRaisesRegex(ValueError, "promote its own"):
            self.admission(request)
        with self.assertRaisesRegex(ValueError, "independent foreign evidence"):
            m.verify_request(self.evidence, request)

    def test_request_cannot_self_admit(self):
        request = self.request()
        with self.assertRaisesRegex(ValueError, "cannot self-admit"):
            m.admit(request, allow=["harvest"], authority_ref=request["requestingAuthority"])

    def test_admission_cannot_exceed_request_or_supported_operations(self):
        request = self.request(operations=["harvest", "stage", "render", "publish", "animate"])
        for allow in (["reuse"], ["stage"], ["render"], ["publish"], ["animate"]):
            with self.assertRaisesRegex(ValueError, "subset exceeds"):
                self.admission(request, allow)
        admission = self.admission(request, ["harvest"])
        self.assertEqual(admission["excludedOperations"], ["animate", "publish", "render", "stage"])
        self.assertFalse(admission["effectiveGrants"]["motionAdaptation"])

    def test_forged_admission_effective_grants_refuse(self):
        request = self.request()
        admission = self.admission(request, ["harvest"])
        admission["effectiveGrants"]["pixelReuse"] = True
        admission = m.seal("admission", admission)
        with self.assertRaisesRegex(ValueError, "independent request/grant"):
            m.verify_admission(request, admission)

    def test_harvest_only_is_quarantined_not_reusable(self):
        request, admission, returned, out = self.run_event(allow=["harvest"])
        harvest = m.read(out / "harvest/page-harvest.json")
        self.assertFalse(harvest["rights"]["pixelReuse"])
        self.assertTrue(harvest["rights"]["pixelHarvest"])
        self.assertEqual(harvest["materialAuthority"], "quarantined-inspection-only")
        self.assertTrue(all(a["materialAuthority"] == "quarantined-inspection-only" for a in harvest["assets"]))
        self.assertFalse((out / "parts-drawer.combined.json").exists())
        with self.assertRaises(PermissionError):
            atlas.page_harvest_to_parts_drawer(harvest, self.root / "forbidden-drawer.json")

    def test_reuse_without_derivative_admission_never_enters_drawer(self):
        _, admission, _, out = self.run_event(allow=["harvest", "reuse"])
        self.assertTrue(admission["effectiveGrants"]["pixelReuse"])
        self.assertFalse(admission["effectiveGrants"]["derivativeReuse"])
        self.assertFalse((out / "parts-drawer.combined.json").exists())

    def test_derivative_does_not_grant_publication_motion_or_sound(self):
        request, admission, returned, out = self.run_event()
        self.assertTrue(admission["effectiveGrants"]["derivativeReuse"])
        for key in ("publicationReuse", "motionAdaptation", "synthesizedSound"):
            self.assertFalse(returned["grantsCarried"][key])
            self.assertIn(key, returned["grantsNotCarried"])
        self.assertIsNone(returned["publicationStateChange"])
        self.assertFalse(any(returned["authority"].values()))

    def test_ancestry_survives_source_analysis_quarry_assets_and_drawer(self):
        request, admission, returned, out = self.run_event()
        records = [m.read(out / "page-source.json"), m.read(out / "page-analysis.json"), m.read(out / "harvest/page-harvest.json"), m.read(out / "parts-drawer.combined.json")]
        records.extend(records[2]["assets"])
        records.extend(records[3]["artifacts"])
        for record in records:
            self.assertEqual(record["foreignAncestry"][0]["locator"], self.identity)
            self.assertEqual(record["foreignAncestry"][0]["commit"], COMMIT)
            self.assertEqual(record["eventLineage"][0]["requestHash"], request["requestHash"])
            self.assertEqual(record["eventLineage"][0]["admissionHash"], admission["admissionHash"])
            if "sourceSha256" in record:
                self.assertEqual(record["sourceSha256"], self.identity["sourceImageSha256"])
        self.assertTrue(all(n["foreignAncestry"][0]["locator"]["pageHash"] == self.identity["pageHash"] for n in returned["descendants"]))
        self.assertTrue(records[0]["id"].startswith("page-source:"))
        self.assertEqual(records[0]["sourceClass"], "licensed")

    def test_geometry_and_masks_have_no_semantic_identity(self):
        _, _, _, out = self.run_event()
        report = m.read(out / "page-analysis.json")
        self.assertIn("PANEL MAP IS GEOMETRY, NOT SEMANTIC UNDERSTANDING", report["laws"])
        self.assertNotIn("characters", report)
        harvest = m.read(out / "harvest/page-harvest.json")
        for asset in harvest["assets"]:
            if asset["kind"] in ("edge-mask", "quarry-candidate"):
                self.assertIs(asset["recipe"]["semantic"], False)

    def test_every_drawer_artifact_binds_a_returned_local_asset_identity(self):
        _, _, returned, out = self.run_event()
        drawer = m.read(out / "parts-drawer.combined.json")
        by_id = {n["id"]: n for n in returned["descendants"]}
        for row in drawer["artifacts"]:
            self.assertEqual(row["sha256"], by_id[row["id"]]["artifact"]["sha256"])
            self.assertEqual(atlas._file_sha(out / row["path"]), row["sha256"])
            self.assertEqual(parts_harvester.resolve_drawer_artifact(drawer, row, artifact_root=out), out / row["path"])
            self.assertFalse(row["rights"]["pixelHarvest"])
        self.assertEqual(drawer["schema"], parts_harvester.DRAWER_SCHEMA)
        self.assertTrue({"still", "crop", "mask"} <= set(drawer["byKind"]))
        with self.assertRaisesRegex(ValueError, "explicit artifact_root"):
            parts_harvester.resolve_drawer_artifact(drawer, drawer["artifacts"][0])

    def test_source_and_foreign_handoff_remain_unchanged(self):
        request = self.request()
        before = self.inventory()
        m.execute(self.evidence, request, self.admission(request), self.root / "event")
        self.assertEqual(before, self.inventory())

    def test_source_mutation_invalidates_replay(self):
        request, admission, _, out = self.run_event()
        image = self.evidence / self.handoff["pages"][0]["sourceImage"]["path"]
        image.write_bytes(b"new pixels")
        with self.assertRaisesRegex(ValueError, "bound bytes changed"):
            m.verify(self.evidence, request, admission, out)

    def test_handoff_and_page_manifest_mutation_invalidates_replay(self):
        for rel in (HANDOFF, PAGE):
            with self.subTest(rel=rel):
                request = self.request()
                path = self.evidence / rel
                original = path.read_bytes()
                path.write_bytes(original + b" ")
                with self.assertRaisesRegex(ValueError, "bound bytes changed"):
                    m.verify_request(self.evidence, request)
                path.write_bytes(original)

    def test_descendant_receipt_and_request_tamper_invalidate_verification(self):
        request, admission, returned, out = self.run_event()
        crop = next(n for n in returned["descendants"] if n["kind"] == "quarry-candidate")
        path = out / crop["artifact"]["path"]
        path.write_bytes(b"fake descendant")
        with self.assertRaisesRegex(ValueError, "verification failure"):
            m.verify(self.evidence, request, admission, out)

    def test_tampered_return_even_if_rehashed_refuses_independent_replay(self):
        request, admission, returned, out = self.run_event()
        returned["authority"]["publication"] = True
        path = out / "mangalize.return.json"
        path.write_bytes(atlas._stable(m.seal("return", returned)))
        with self.assertRaisesRegex(ValueError, "verification failure"):
            m.verify(self.evidence, request, admission, out)

    def test_fabricated_source_hash_and_ownership_label_do_not_grant_harvest(self):
        request = self.request(supplemental=False)
        request["ancestors"][0]["sourceHash"] = "a" * 64
        request["ancestors"][0]["ownership"] = "owned"
        request = m.seal("request", request)
        with self.assertRaisesRegex(ValueError, "independent foreign evidence"):
            m.verify_request(self.evidence, request)
        with self.assertRaisesRegex(ValueError, "pixelHarvest"):
            self.admission(self.request(supplemental=False))

    def test_supplemental_grant_cannot_cover_other_page_or_extra_permission(self):
        grant = m.source_grant({**self.identity, "pageId": "page-01"}, self.handoff["handoffHash"], authority_ref="test:grant", source_commit=COMMIT)
        path = self.evidence / "wrong-grant.json"
        m.persist(path, grant)
        with self.assertRaisesRegex(ValueError, "this exact ancestor"):
            m.make_request(self.evidence, self.evidence / HANDOFF, self.evidence / PAGE, page_id="page-05", authority_ref="test:request", source_commit=COMMIT, grant_paths=[path])

    def test_later_grant_is_a_ceiling_not_retroactive_authority(self):
        request = self.request(operations=["harvest", "reuse", "derive"])
        self.assertEqual(request["suppliedGrants"], {k: k == "pixelHarvest" for k in m.GRANTS})
        for op in ("reuse", "derive"):
            with self.assertRaisesRegex(ValueError, "not supplied/requested"):
                self.admission(request, ["harvest", op])
        self.assertFalse(self.handoff["grants"]["pixelHarvest"])
        original = m.read(ROOT / "specimens/mangalize-001/refusal/mangalize.request.json")
        refusal = m.read(ROOT / "specimens/mangalize-001/refusal/mangalize.admission.json")
        m.verify_request(self.evidence, original)
        m.verify_admission(original, refusal)
        self.assertEqual(original["requestHash"], "75b7cca097cb051c87bf35ccf36875b480cf46c3d2d97abf2eeb56c3e868e727")
        self.assertEqual(refusal["admissionHash"], "61db2753f08ec42a2f18ef500bd89ad0196846a7bb76b16168f1fc5982ab8ad6")

    def test_grant_binds_commit_experiment_and_all_exact_ancestry(self):
        request = self.request()
        declaration = request["supplementalGrants"][0]["declaration"]
        self.assertEqual(declaration["sourceCommit"], COMMIT)
        self.assertEqual(declaration["experiment"], "MANGALIZE-001")
        self.assertEqual(declaration["ancestor"], self.identity)
        for field, value in (("sourceCommit", "a" * 40), ("experiment", "MANGALIZE-002"),
                             ("handoffHash", "a" * 64)):
            changed = copy.deepcopy(declaration)
            changed[field] = value
            path = self.evidence / (field + "-wrong-grant.json")
            m.persist(path, m.seal("source-grant", changed))
            with self.assertRaisesRegex(ValueError, "this exact ancestor"):
                m.make_request(self.evidence, self.evidence / HANDOFF, self.evidence / PAGE, page_id="page-05",
                    authority_ref="test:request", source_commit=COMMIT, grant_paths=[path])
        changed = copy.deepcopy(declaration)
        changed["grants"]["pixelReuse"] = True
        path = self.evidence / "expanded-grant.json"
        m.persist(path, m.seal("source-grant", changed))
        with self.assertRaisesRegex(ValueError, "only harvest"):
            m.make_request(self.evidence, self.evidence / HANDOFF, self.evidence / PAGE, page_id="page-05",
                authority_ref="test:request", source_commit=COMMIT, grant_paths=[path])

    def test_source_grant_mutation_breaks_independent_replay(self):
        request = self.request()
        admission = self.admission(request)
        out = self.root / "harvest-only"
        m.execute(self.evidence, request, admission, out)
        path = self.evidence / request["supplementalGrants"][0]["binding"]["path"]
        path.write_bytes(path.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "bound bytes changed"):
            m.verify(self.evidence, request, admission, out)

    def test_committed_founding_event_replays_only_harvest_authority(self):
        out = ROOT / "specimens/mangalize-001/executed"
        request = m.read(out / "mangalize.request.json")
        admission = m.read(out / "mangalize.admission.json")
        returned = m.read(out / "mangalize.return.json")
        self.assertEqual(m.verify(self.evidence, request, admission, out), returned["returnHash"])
        self.assertEqual(request["requestedOperations"], ["harvest"])
        self.assertEqual(admission["admittedOperations"], ["harvest"])
        self.assertEqual(admission["effectiveGrants"], {k: k == "pixelHarvest" for k in m.GRANTS})
        self.assertFalse(any(returned["grantsCarried"].values()))
        self.assertFalse((out / "parts-drawer.combined.json").exists())
        self.assertIsNone(returned["publicationStateChange"])
        assets = m.read(out / "harvest/page-harvest.json")["assets"]
        self.assertEqual(len(assets), 25)
        for row in assets:
            self.assertEqual(row["foreignAncestry"][0]["locator"], self.identity)
            self.assertEqual(row["materialAuthority"], "quarantined-inspection-only")
            self.assertFalse(row["rights"]["pixelReuse"])
            self.assertFalse(row["rights"]["derivativeReuse"])

    def test_smash_is_identical_custody_not_implicit_grant(self):
        founding = ROOT / "specimens/mangalize-001/executed"
        request = m.read(founding / "mangalize.request.json")
        admission = m.read(founding / "mangalize.admission.json")
        out = self.root / "smash"
        result = subprocess.run([sys.executable, "-m", "haunted_blender.mangalize_cli", "smash",
            str(self.evidence / HANDOFF), str(out), "--page", "page-05", "--page-manifest", str(self.evidence / PAGE),
            "--evidence-root", str(self.evidence), "--source-commit", COMMIT,
            "--source-grant", str(self.evidence / "separate-authority/page-05.harvest-only-grant.json"),
            "--operation", "harvest", "--allow", "harvest", "--requesting-authority", request["requestingAuthority"],
            "--admitting-authority", admission["authorityRef"]], capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(m.tree_bytes(out), m.tree_bytes(founding))

    def test_source_root_and_symlink_escape_refuses(self):
        request, admission, _, out = self.run_event()
        manifest = m.read(out / "page-source.json")
        with self.assertRaisesRegex(ValueError, "explicit source_root"):
            atlas.analyze_page(manifest)
        manifest["sourcePath"] = "../escape.png"
        with self.assertRaisesRegex(ValueError, "escapes"):
            atlas.analyze_page(manifest, source_root=self.evidence)

    def test_graph_descendants_do_not_replace_source_and_have_distinct_recipes(self):
        _, _, returned, out = self.run_event()
        kinds = {n["kind"] for n in returned["descendants"]}
        self.assertTrue({"panel", "quarry-candidate", "edge-mask", parts_harvester.DRAWER_SCHEMA} <= kinds)
        self.assertFalse(any("replace" in n for n in returned["descendants"]))
        self.assertTrue((self.evidence / self.handoff["pages"][0]["sourceImage"]["path"]).exists())

    def test_unsupported_manga_targets_remain_unimplemented(self):
        for target in ("page", "panel-sequence"):
            request = self.request(target=target)
            with self.assertRaisesRegex(ValueError, "not implemented"):
                self.admission(request)

    def test_trace_names_actual_event_and_foreign_identity(self):
        request, admission, returned, out = self.run_event()
        trace = (out / "TRACE.md").read_text()
        for value in self.identity.values():
            self.assertIn(value, trace)
        self.assertIn("PERFORMED", trace)
        self.assertIn("ANCESTRY", trace)
        self.assertIn("UNCHANGED", trace)
        self.assertIn(returned["returnHash"], trace)

    def test_cli_refusal_persists_request_and_separate_refusal_admission(self):
        request = self.request(supplemental=False)
        request_file = self.root / "request.json"
        output = self.root / "refusal.json"
        m.persist(request_file, request)
        result = subprocess.run([sys.executable, "-m", "haunted_blender.mangalize_cli", "admit", str(request_file), str(output),
                                 "--evidence-root", str(self.evidence), "--allow", "harvest", "--authority-ref", "test:independent-refusal"], capture_output=True, text=True, cwd=ROOT)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(m.read(output)["decision"], "refused")
        self.assertIn("pixelHarvest", result.stdout)


if __name__ == "__main__":
    unittest.main()
