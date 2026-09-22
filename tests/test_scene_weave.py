"""Synthetic-only tests. Production scene, alchemy and panorama semantics are not claimed."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from haunted_blender import catalog, alchemy
from haunted_blender import scene_weave as weave


def story():
    return {
        "title": "The Unopened Letter",
        "entities": [
            {"id": "mother", "kind": "character", "name": "Mother", "basis": weave.AUTHOR},
            {"id": "daughter", "kind": "character", "name": "Daughter", "basis": weave.AUTHOR},
            {"id": "letter", "kind": "prop", "name": "Letter", "basis": weave.AUTHOR},
            {"id": "kitchen", "kind": "location", "name": "Kitchen", "basis": weave.AUTHOR},
        ],
        "facts": [
            {"id": "sealed", "subject": "letter", "predicate": "state", "value": "sealed",
             "since_beat": 0, "basis": weave.AUTHOR},
            {"id": "sender", "subject": "letter", "predicate": "sender", "value": "the mother",
             "since_beat": 0, "basis": weave.AUTHOR},
        ],
        "beats": [
            {"id": "arrival", "index": 0},
            {"id": "decision", "index": 1},
            {"id": "aftermath", "index": 2},
        ],
        "knowledge": [
            {"id": "mother-knows", "observer": "mother", "fact_id": "sender",
             "since_beat": 0, "basis": weave.AUTHOR},
            {"id": "audience-sees", "observer": "audience", "fact_id": "sealed",
             "since_beat": 0, "basis": weave.AUTHOR},
            {"id": "daughter-sees", "observer": "daughter", "fact_id": "sealed",
             "since_beat": 1, "basis": weave.AUTHOR},
        ],
        "relations": [
            {"id": "letter-in-room", "from": "letter", "to": "kitchen",
             "basis": weave.AUTHOR, "kind": "located-in"},
        ],
        "affordances": [
            {"id": "open-letter", "actor": "daughter", "object": "letter",
             "requires_fact_ids": ["sealed"], "status": "proposed"},
        ],
        "questions": [{"id": "who", "text": "When will she discover the sender?", "status": "open"}],
    }


def make_world():
    return {
        "schema": weave.WORLD, "id": "world-0123456789abcdef", "mode": "fiction",
        "material": {"alchemy_snapshot_sha256": "a" * 64,
                     "alchemy_recipe_id": "alchemy-0123456789abcdef",
                     "roles": [
                         {"role": "source", "requested_asset_id": "asset-a", "frame_sha256": "b" * 64},
                         {"role": "bridge", "requested_asset_id": "asset-b", "frame_sha256": "c" * 64},
                         {"role": "target", "requested_asset_id": "asset-c", "frame_sha256": "d" * 64},
                     ]},
        **story(),
    }


def opened():
    return {"id": "opened", "subject": "letter", "predicate": "state",
            "value": "open", "basis": weave.AUTHOR, "since_beat": 2,
            "supersedes": "sealed"}


class SceneWeaveTests(unittest.TestCase):
    def setUp(self):
        self.world = make_world()
        weave.validate(self.world)
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)

    def test_three_deterministic_presentations_cannot_edit_story(self):
        original = weave.sha(self.world)
        result = weave.compose(self.world, 0)
        self.assertEqual(result, weave.compose(self.world, 0))
        self.assertEqual(weave.sha(self.world), original)
        self.assertEqual([c["framing"] for c in result["candidates"]],
                         ["establishing", "insert", "negative-space"])
        self.assertTrue(all(not c["story_patch"] and not c["knowledge_patch"]
                            for c in result["candidates"]))

    def test_character_knowledge_does_not_leak_to_audience_or_actor(self):
        arrival = weave.compose(self.world, 0)
        self.assertNotIn("sender", arrival["candidates"][0]["audience_fact_ids"])
        self.assertIn("sender", arrival["candidates"][1]["possible_reveals"])
        self.assertNotIn("the mother", json.dumps(arrival).lower())
        self.assertEqual(arrival["available_proposed_affordance_ids"], [])
        self.assertEqual(weave.compose(self.world, 1)["available_proposed_affordance_ids"],
                         ["open-letter"])

    def test_undeclared_fact_and_unattested_subject_are_rejected(self):
        altered = copy.deepcopy(self.world)
        altered["knowledge"][0]["fact_id"] = "unknown"
        with self.assertRaisesRegex(ValueError, "undeclared"):
            weave.validate(altered)
        altered = copy.deepcopy(self.world)
        altered["entities"][0]["basis"] = "model_inferred"
        with self.assertRaisesRegex(ValueError, "attestation"):
            weave.validate(altered)
        altered = copy.deepcopy(self.world)
        altered["entities"][0]["face_embedding"] = [0.1]
        with self.assertRaisesRegex(ValueError, "identification"):
            weave.validate(altered)

    def test_branch_requires_approval_and_leaves_parent_unchanged(self):
        before = weave.sha(self.world)
        proposal = weave.propose_branch(self.world, source_fact_id="sealed", new_fact=opened())
        self.assertEqual(weave.sha(self.world), before)
        with self.assertRaisesRegex(ValueError, "approval"):
            weave.approve_branch(self.world, proposal)
        descendant = weave.approve_branch(self.world, proposal, filmmaker_approval=True)
        self.assertNotEqual(descendant["id"], self.world["id"])
        self.assertEqual(descendant["parent_sha256"], before)
        self.assertEqual([f["id"] for f in descendant["facts"]],
                         ["sealed", "sender", "opened"])
        self.assertEqual(weave.sha(self.world), before)
        self.assertTrue(weave.save_child(self.root, descendant).is_file())
        with self.assertRaises(FileExistsError):
            weave.save_child(self.root, descendant)

    def test_tamper_stale_or_backdated_branch_refused(self):
        proposal = weave.propose_branch(self.world, source_fact_id="sealed", new_fact=opened())
        proposal["patch"]["new_fact"]["value"] = "shredded"
        with self.assertRaisesRegex(ValueError, "tampered"):
            weave.approve_branch(self.world, proposal, filmmaker_approval=True)
        proposal = weave.propose_branch(self.world, source_fact_id="sealed", new_fact=opened())
        changed = copy.deepcopy(self.world)
        changed["questions"][0]["text"] = "What is written inside?"
        with self.assertRaisesRegex(ValueError, "Stale"):
            weave.approve_branch(changed, proposal, filmmaker_approval=True)
        bad = opened()
        bad["since_beat"] = 0
        with self.assertRaisesRegex(ValueError, "rewrite"):
            weave.propose_branch(self.world, source_fact_id="sealed", new_fact=bad)

    def test_frozen_world_hash_and_identity_are_checked(self):
        path = weave._path(self.root, self.world["id"])
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(self.world), encoding="utf-8")
        snap = weave.freeze(self.root, self.world["id"])
        self.assertEqual(snap, weave.freeze(self.root, self.world["id"]))
        self.assertEqual(weave.compose(weave.load_snapshot(self.root, snap), 0),
                         weave.compose(self.world, 0))
        broken = copy.deepcopy(self.world)
        broken["title"] = "Forged"
        snap.write_text(json.dumps(broken), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "hash"):
            weave.load_snapshot(self.root, snap)

    def test_real_alchemy_parent_and_pantry_are_unchanged(self):
        catalog.init(self.root)
        pictures = self.root / "synthetic"
        pictures.mkdir()
        for label in ("cup", "water", "moon"):
            (pictures / (label + ".png")).write_bytes(("fixture-" + label).encode())
        catalog.scan(self.root, pictures)
        con = catalog.connect(self.root)
        ids = {Path(item["path"]).stem: item["id"]
               for item in con.execute("SELECT path,id FROM assets")}
        digest_before = {item["id"]: item["sha256"]
                         for item in con.execute("SELECT id,sha256 FROM assets")}
        con.close()
        recipe = alchemy.create(self.root, ids["cup"], ids["moon"], bridge=ids["water"],
                                relation="triadic-bridge", statement="Artist-authored fiction")
        snapshot = alchemy.freeze(self.root, recipe["id"])
        frozen_before = snapshot.read_bytes()
        created = weave.from_alchemy(self.root, snapshot, story())
        frozen_world = weave.freeze(self.root, created["world_id"])
        self.assertEqual(weave.compose(weave.load_snapshot(self.root, frozen_world), 1)
                         ["available_proposed_affordance_ids"], ["open-letter"])
        self.assertEqual(snapshot.read_bytes(), frozen_before)
        con = catalog.connect(self.root)
        digest_after = {item["id"]: item["sha256"]
                        for item in con.execute("SELECT id,sha256 FROM assets")}
        con.close()
        self.assertEqual(digest_before, digest_after)


if __name__ == "__main__":
    unittest.main()
