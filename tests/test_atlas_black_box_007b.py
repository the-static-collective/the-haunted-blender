import json
import tempfile
import unittest
from pathlib import Path

from haunted_blender import atlas_black_box, motion_executor, motion_organ


class AtlasBlackBox007bTests(unittest.TestCase):
    def make_plan(self, root):
        req = motion_organ.freeze_request(
            root,
            scene_id="private scene title",
            scene_sha256="a" * 64,
            window_id="chorus-1",
            start_seconds=1,
            duration_seconds=2,
            prompt="PRIVATE PROMPT MUST NOT ENTER TELEMETRY",
            source_address="sha256:" + "b" * 64,
            remote_disclosure_approved=True,
        )
        offers = motion_organ.freeze_offers(
            root,
            {
                "schema": motion_organ.OFFERS_SCHEMA,
                "observedAt": "2026-10-06T01:00:00Z",
                "offers": [
                    {
                        "offerId": "free-a",
                        "providerId": "provider-a",
                        "model": "m1",
                        "available": True,
                        "spendClass": "free",
                        "creditCost": 1,
                        "creditBalance": 10,
                        "inputModes": ["image-to-video"],
                        "aspectRatios": ["16:9"],
                        "minSeconds": 1,
                        "maxSeconds": 8,
                    }
                ],
            },
        )
        route = motion_organ.route_request(root, req["request"], offers["offers"])
        plan = motion_executor.build_plan(
            root,
            route["route"],
            occurrence_budget_usd_micros=10000,
            per_job_budget_usd_micros=10000,
        )
        return plan, req

    def test_operational_events_are_automatic_hash_chained_and_prompt_free(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            plan, req = self.make_plan(root)
            caps = {
                "schema": motion_executor.CAP_SCHEMA,
                "offerId": "free-a",
                "providerId": "provider-a",
                "model": "m1",
                "available": True,
                "inputModes": ["image-to-video"],
                "aspectRatios": ["16:9"],
                "minSeconds": 1,
                "maxSeconds": 8,
                "observedAt": "2026-10-06T01:00:01Z",
            }
            state = motion_executor.record_capabilities(root, plan["plan"], plan["state"], caps)
            quote = {
                "schema": motion_executor.QUOTE_SCHEMA,
                "offerId": "free-a",
                "exactConfiguration": True,
                "generatedDurationSeconds": 4,
                "denomination": "provider-credits",
                "amount": 1,
                "wholeJobUsdMicros": 0,
                "observedAt": "2026-10-06T01:00:02Z",
            }
            motion_executor.record_quote(root, plan["plan"], state["state"], quote)
            check = atlas_black_box.verify_lane(root, "operational")
            self.assertEqual(check["eventCount"], 2)
            payload = "\n".join(path.read_text() for _seq, path, _body in atlas_black_box._events(root, "operational"))
            self.assertNotIn("PRIVATE PROMPT", payload)
            self.assertNotIn("private scene title", payload)
            self.assertNotIn(req["requestBody"]["prompt"], payload)

    def test_public_operational_creative_lanes_remain_distinct(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            atlas_black_box.record_atlas_target(
                root,
                observed_at="2026-10-06T01:00:00Z",
                endpoint_id="fal/model",
                atlas_state="proposal-only",
                package_sha256="d" * 64,
                quote_unit="seconds",
                indicative_usd=0.005,
            )
            atlas_black_box.record_operational(
                root,
                kind="provider.status",
                observed_at="2026-10-06T01:00:01Z",
                plan_sha256="e" * 64,
                provider_id="p",
                offer_id="o",
                attempt=1,
                facts={"status": "completed"},
            )
            atlas_black_box.record_creative_keep(
                root,
                observed_at="2026-10-06T01:00:02Z",
                request_sha256="f" * 64,
                scene_sha256="a" * 64,
                window_id="w",
                provider_id="p",
                offer_id="o",
                candidate_sha256="b" * 64,
            )
            self.assertEqual(atlas_black_box.verify_lane(root, "public_catalog")["eventCount"], 1)
            self.assertEqual(atlas_black_box.verify_lane(root, "operational")["eventCount"], 1)
            self.assertEqual(atlas_black_box.verify_lane(root, "creative")["eventCount"], 1)
            summary = atlas_black_box.summarize(root)
            self.assertEqual(summary["providers"]["p"]["completedJobsObserved"], 1)
            self.assertEqual(summary["providers"]["p"]["candidatesKeptObserved"], 1)
            self.assertIn("SUMMARY != QUALITY RANKING", summary["laws"])

    def test_chain_detects_tampering(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            event = atlas_black_box.record_operational(
                root,
                kind="provider.status",
                observed_at="x",
                plan_sha256="e" * 64,
                provider_id="p",
                offer_id="o",
                attempt=1,
                facts={"status": "completed"},
            )
            path = Path(event["event"])
            body = json.loads(path.read_text())
            body["facts"]["status"] = "definitively_failed"
            path.write_text(json.dumps(body))
            with self.assertRaises(ValueError):
                atlas_black_box.verify_lane(root, "operational")

    def test_forbidden_default_fields_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                atlas_black_box.append_event(
                    Path(td),
                    "operational",
                    kind="x",
                    observed_at="x",
                    facts={"prompt": "secret"},
                )


if __name__ == "__main__":
    unittest.main()
