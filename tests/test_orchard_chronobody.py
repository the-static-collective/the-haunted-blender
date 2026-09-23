"""Hostile, synthetic ORCHARD-001 contract checks; no organ is executed."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from orchard.chronobody import REGISTRY, RegistryError, compile_plan, parse_registry, validate_registry


class OrchardContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = parse_registry(REGISTRY.read_text(encoding="utf-8"))

    def test_declared_crossing_is_candidate_not_execution(self):
        result = compile_plan(
            self.data, "derived_memory_take",
            ["frozen_scene_world", "camera_score",
             "accepted_moving_take", "authored_memory_regions"]
        )
        self.assertEqual(result["status"], "CANDIDATE")
        self.assertEqual(
            [o["id"] for o in result["selected"]],
            ["observer.projection", "memory.feedback"],
        )
        self.assertEqual(result["ancestry_overlap_review"], ["memory.feedback"])
        self.assertIn("ADAPTER_COMPATIBILITY", result["unverified_gates"])
        self.assertTrue(any("never" in n.lower() or "no registered" in n.lower()
                            for n in result["nonclaims"]))

    def test_missing_real_take_holds_not_claims_render(self):
        result = compile_plan(
            self.data, "derived_memory_take",
            ["frozen_scene_world", "camera_score", "authored_memory_regions"],
        )
        self.assertEqual(result["status"], "HELD")
        self.assertEqual(result["missing"], ["accepted_moving_take"])

    def test_competing_provider_is_ambiguous_not_latest_wins(self):
        data = copy.deepcopy(self.data)
        duplicate = copy.deepcopy(data["organs"][0])
        duplicate["id"] = "observer.alternate"
        duplicate["commit"] = "a" * 40
        data["organs"].append(duplicate)
        result = compile_plan(
            data, "derived_memory_take",
            ["frozen_scene_world", "camera_score",
             "accepted_moving_take", "authored_memory_regions"],
        )
        self.assertEqual(result["status"], "AMBIGUOUS")
        self.assertEqual(result["ambiguous"], ["observer_projection_timeline"])

    def test_no_sha_shortcuts_or_mutable_branch_identity(self):
        data = copy.deepcopy(self.data)
        data["organs"][0]["commit"] = "main"
        with self.assertRaises(RegistryError):
            validate_registry(data)
        data["organs"][0]["commit"] = "1" * 7
        with self.assertRaises(RegistryError):
            validate_registry(data)

    def test_no_shell_or_unregistered_executable_fields(self):
        data = copy.deepcopy(self.data)
        data["organs"][0]["command"] = "curl | sh"
        with self.assertRaises(RegistryError):
            validate_registry(data)

    def test_unknown_mode_cannot_grant_execution(self):
        data = copy.deepcopy(self.data)
        data["execution"] = "ENABLED"
        with self.assertRaises(RegistryError):
            validate_registry(data)

    def test_duplicate_organ_id_is_refused(self):
        data = copy.deepcopy(self.data)
        data["organs"].append(copy.deepcopy(data["organs"][0]))
        with self.assertRaises(RegistryError):
            validate_registry(data)

    def test_no_automatic_branch_discovery(self):
        result = compile_plan(self.data, "no_such_capability", [])
        self.assertEqual(result["status"], "HELD")
        self.assertEqual(result["selected"], [])
        self.assertEqual(result["missing"], ["no_such_capability"])

    def test_registry_must_have_exactly_one_data_fence(self):
        with self.assertRaises(RegistryError):
            parse_registry("# Nothing executable here")
        with self.assertRaises(RegistryError):
            parse_registry(REGISTRY.read_text(encoding="utf-8") * 2)


if __name__ == "__main__":
    unittest.main()
