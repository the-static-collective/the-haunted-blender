import copy
import json
import unittest
from pathlib import Path

from haunted_blender import narrative_performance
from haunted_blender.paper_director import SHOT_TYPES


FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "specimens"
    / "008n"
    / "bus-page-5-a-page-you-can-hear-001.json"
)


class ParticularToPerformance008nTests(unittest.TestCase):
    def spec(self):
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_golden_page_five_compiles_through_all_four_boundaries(self):
        bundle = narrative_performance.compile_spec(self.spec())
        self.assertEqual(
            bundle["source"]["schema"],
            narrative_performance.SOURCE_SCHEMA,
        )
        self.assertEqual(
            bundle["proposal"]["schema"],
            narrative_performance.PROPOSAL_SCHEMA,
        )
        self.assertEqual(
            bundle["admission"]["schema"],
            narrative_performance.ADMISSION_SCHEMA,
        )
        self.assertEqual(
            bundle["plan"]["schema"],
            narrative_performance.PLAN_SCHEMA,
        )
        self.assertEqual(bundle["plan"]["beatCount"], 8)
        self.assertAlmostEqual(bundle["plan"]["durationSeconds"], 6.8, places=6)
        self.assertEqual(bundle["receipt"]["performedBeatCount"], 8)
        self.assertEqual(bundle["receipt"]["receiptAuthority"], "none")

    def test_exact_replay_is_deterministic(self):
        first = narrative_performance.compile_spec(self.spec())
        second = narrative_performance.compile_spec(self.spec())
        self.assertEqual(first, second)

    def test_staging_cannot_invent_causal_authority(self):
        spec = self.spec()
        source = narrative_performance.particular_source(
            label=spec["label"],
            source_locator=spec["sourceLocator"],
            particulars=spec["particulars"],
            boundary_claims=spec["boundaryClaims"],
        )
        hostile = copy.deepcopy(spec["beats"])
        hostile[0]["authorityClaims"] = [
            "the bus conducted the musicians and caused the arrangement"
        ]
        with self.assertRaisesRegex(ValueError, "cannot synthesize"):
            narrative_performance.staging_proposal(source, hostile)

    def test_source_particular_hash_survives_into_performance_and_return(self):
        bundle = narrative_performance.compile_spec(self.spec())
        source_hashes = {
            row["id"]: row["particularHash"]
            for row in bundle["source"]["particulars"]
        }
        for beat in bundle["plan"]["beats"]:
            self.assertEqual(
                beat["sourceParticularHash"],
                source_hashes[beat["sourceParticularId"]],
            )
            self.assertEqual(beat["sourceAuthority"], "preserved")
        returned = {
            row["sourceParticularId"]: row["sourceParticularHash"]
            for row in bundle["receipt"]["performedParticulars"]
        }
        self.assertEqual(returned, source_hashes)

    def test_partial_editorial_admission_does_not_erase_unperformed_source(self):
        spec = self.spec()
        spec["admittedBeatIds"] = ["beat-01", "beat-07", "beat-08"]
        bundle = narrative_performance.compile_spec(spec)
        self.assertEqual(bundle["plan"]["beatCount"], 3)
        self.assertEqual(len(bundle["source"]["particulars"]), 8)
        self.assertEqual(
            bundle["admission"]["rejectedBeatIds"],
            ["beat-02", "beat-03", "beat-04", "beat-05", "beat-06"],
        )

    def test_plan_uses_existing_paper_director_vocabulary_only(self):
        bundle = narrative_performance.compile_spec(self.spec())
        self.assertTrue(
            all(row["type"] in SHOT_TYPES for row in bundle["plan"]["beats"])
        )
        self.assertEqual(
            [row["type"] for row in bundle["plan"]["beats"]],
            [
                "INSERT",
                "INSERT",
                "CLOSE_UP",
                "INSERT",
                "CLOSE_UP",
                "INSERT",
                "REACTION",
                "WIDE",
            ],
        )

    def test_proposal_cannot_point_at_an_invented_particular(self):
        spec = self.spec()
        source = narrative_performance.particular_source(
            label=spec["label"],
            source_locator=spec["sourceLocator"],
            particulars=spec["particulars"],
            boundary_claims=spec["boundaryClaims"],
        )
        hostile = copy.deepcopy(spec["beats"])
        hostile[0]["sourceParticularId"] = "p-imaginary-conductor"
        with self.assertRaisesRegex(ValueError, "unknown source particular"):
            narrative_performance.staging_proposal(source, hostile)


if __name__ == "__main__":
    unittest.main()
