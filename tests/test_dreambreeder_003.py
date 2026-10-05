import unittest

from haunted_blender.dreambreeder import (
    GHOST_SCHEMA,
    RECOMBINATION_SCHEMA,
    admit_ghost,
    create_ecology,
    keep_proposal,
    recombine,
    resolve_descendant,
    scrape_ecology,
)


class Dreambreeder003Tests(unittest.TestCase):
    def ecology(self):
        return create_ecology(
            relation_id="relation-amber-blue",
            common_checkpoint_id="checkpoint-common",
            source_receipt_ids=["receipt-amber", "receipt-blue"],
            donor_ids=[f"flow-video:{i:02d}" for i in range(12)],
        )

    def test_six_up_is_deterministic_and_proposal_only(self):
        a = self.ecology()
        b = self.ecology()
        self.assertEqual(a, b)
        self.assertEqual(len(a["proposals"]), 6)
        self.assertTrue(all(p["authorityClass"] == "proposal" for p in a["proposals"]))
        self.assertIsNone(a["disposition"])

    def test_scrape_mints_no_history_and_no_ghosts(self):
        result = scrape_ecology(self.ecology())
        self.assertEqual(result["disposition"]["kind"], "SCRAPE")
        self.assertFalse(result["disposition"]["negativePreferenceModel"])
        self.assertFalse(result["disposition"]["createsHistory"])
        self.assertFalse(result["disposition"]["createsGhostInfluence"])
        self.assertEqual(result["ghostCandidates"], [])

    def test_keep_makes_one_descendant_and_five_inert_ghost_candidates(self):
        ecology = self.ecology()
        kept = ecology["proposals"][2]
        result = keep_proposal(ecology, kept["id"])
        self.assertEqual(result["ecology"]["disposition"]["kind"], "KEEP")
        self.assertEqual(result["descendant"]["status"], "unrendered-descendant")
        self.assertEqual(result["descendant"]["authorityClass"], "continuation-permission")
        self.assertEqual(len(result["ecology"]["ghostCandidates"]), 5)
        self.assertTrue(all(g["state"] == "inert-unselected-possibility" for g in result["ecology"]["ghostCandidates"]))

    def test_ghost_requires_separate_explicit_act(self):
        ecology = self.ecology()
        result = keep_proposal(ecology, ecology["proposals"][0]["id"])
        ghost_candidate = result["ecology"]["ghostCandidates"][0]
        ghost = admit_ghost(result["ecology"], ghost_candidate["proposalId"], local_note="hinge residue")
        self.assertEqual(ghost["schema"], GHOST_SCHEMA)
        self.assertEqual(ghost["authorityClass"], "influence-only")
        self.assertFalse(ghost["historicalAncestry"])
        self.assertEqual(ghost["localNote"], "hinge residue")

    def test_recombine_two_resolved_descendants_without_canonical_parent(self):
        e1 = self.ecology()
        a = keep_proposal(e1, e1["proposals"][0]["id"])
        left = resolve_descendant(a["descendant"], receipt_id="receipt-left", performance_id="film-left")

        e2 = create_ecology(
            relation_id="relation-amber-blue",
            common_checkpoint_id="checkpoint-common",
            source_receipt_ids=["receipt-amber", "receipt-blue"],
            generation=2,
            donor_ids=[f"flow-video:{i:02d}" for i in range(12)],
        )
        b = keep_proposal(e2, e2["proposals"][1]["id"])
        right = resolve_descendant(b["descendant"], receipt_id="receipt-right", performance_id="film-right")

        ghost = admit_ghost(a["ecology"], a["ecology"]["ghostCandidates"][0]["proposalId"])
        child = recombine(left, right, local_label="third-film", ghost_influences=[ghost])
        self.assertEqual(child["schema"], RECOMBINATION_SCHEMA)
        self.assertIsNone(child["canonicalParent"])
        self.assertFalse(child["inheritsParentAuthority"])
        self.assertEqual(len(child["parents"]), 2)
        self.assertEqual(child["ghostInfluenceIds"], [ghost["id"]])
        self.assertEqual(child["status"], "fresh-child-proposal")

    def test_unresolved_descendant_cannot_recombine(self):
        e = self.ecology()
        a = keep_proposal(e, e["proposals"][0]["id"])["descendant"]
        b = keep_proposal(
            create_ecology(
                relation_id="r2",
                common_checkpoint_id="checkpoint-common",
                source_receipt_ids=["receipt-x"],
                generation=2,
            ),
            create_ecology(
                relation_id="r2",
                common_checkpoint_id="checkpoint-common",
                source_receipt_ids=["receipt-x"],
                generation=2,
            )["proposals"][0]["id"],
        )["descendant"]
        with self.assertRaises(ValueError):
            recombine(a, b, local_label="illegal")


if __name__ == "__main__":
    unittest.main()
