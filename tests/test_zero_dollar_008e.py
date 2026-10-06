import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from haunted_blender import flow_pantry, resource_compass, zero_dollar_mill


class ZeroDollarFilmMill008eTests(unittest.TestCase):
    def setUp(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("FFmpeg required")

    def make_video(self, path: Path, *, color: str, duration: float = 0.8):
        subprocess.run(
            [
                "ffmpeg", "-v", "error", "-y",
                "-f", "lavfi", "-i", f"color=c={color}:s=160x90:d={duration}:r=12",
                "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path),
            ],
            check=True,
        )

    def test_plan_guarantees_full_coverage_at_zero_provider_cost(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_video(root / "a.mp4", color="red")
            self.make_video(root / "b.mp4", color="blue")
            manifest = flow_pantry.index_flow_folder(root, probe=True)

            plan = zero_dollar_mill.build_plan(
                manifest,
                root,
                target_seconds=9.5,
                slug_seconds=2.0,
                width=160,
                height=90,
                fps=12,
            )
            self.assertEqual(plan["slugCount"], 5)
            self.assertAlmostEqual(plan["plannedCoverageSeconds"], 9.5, places=6)
            self.assertEqual(plan["coverageRatio"], 1.0)
            self.assertEqual(plan["cost"]["externalGenerations"], 0)
            self.assertEqual(plan["cost"]["providerCredits"], 0)
            self.assertEqual(plan["cost"]["usdMicros"], 0)
            self.assertEqual(plan["uniqueSourceCountPlanned"], 2)
            self.assertGreaterEqual(len({s["recipe"] for s in plan["slugs"]}), 3)

    def test_render_expands_tiny_sources_into_full_zero_dollar_cut(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            source.mkdir()
            self.make_video(source / "a.mp4", color="green", duration=0.55)
            self.make_video(source / "b.mp4", color="yellow", duration=0.65)
            manifest = flow_pantry.index_flow_folder(source, probe=True)
            plan = zero_dollar_mill.build_plan(
                manifest,
                source,
                target_seconds=4.5,
                slug_seconds=1.5,
                width=160,
                height=90,
                fps=12,
            )

            receipt = zero_dollar_mill.render_plan(plan, source, root / "out")
            self.assertEqual(receipt["status"], "full-zero-dollar-coverage")
            self.assertEqual(receipt["externalGenerations"], 0)
            self.assertEqual(receipt["providerCredits"], 0)
            self.assertEqual(receipt["usdMicros"], 0)
            self.assertGreaterEqual(receipt["coverageRatio"], 0.99)
            self.assertGreaterEqual(receipt["observedOutputSeconds"], 4.4)
            self.assertEqual(receipt["slugCount"], 3)
            self.assertEqual(receipt["uniqueSourceCount"], 2)
            self.assertGreater(receipt["derivativeYield"], 1.0)
            self.assertTrue(Path(receipt["outputPath"]).is_file())
            self.assertTrue((root / "out" / "zero-dollar-current-cut.receipt.json").is_file())

    def test_render_refuses_source_bytes_changed_after_plan(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_video(root / "a.mp4", color="black")
            manifest = flow_pantry.index_flow_folder(root, probe=True)
            plan = zero_dollar_mill.build_plan(
                manifest,
                root,
                target_seconds=1.0,
                slug_seconds=1.0,
                width=160,
                height=90,
                fps=12,
            )
            self.make_video(root / "a.mp4", color="white")
            with self.assertRaises(ValueError):
                zero_dollar_mill.render_plan(plan, root, root / "out")

    def test_resource_compass_puts_repeatability_before_one_shot_quality(self):
        observation = {
            "providers": [
                {
                    "providerId": "repeatable",
                    "profileId": "x",
                    "models": [{
                        "model": "ugly-free",
                        "routeKind": "image-to-video",
                        "available": True,
                        "spendClass": "free",
                        "repeatableFree": True,
                        "maxSeconds": 4,
                    }],
                },
                {
                    "providerId": "daily",
                    "profileId": "x",
                    "models": [{
                        "model": "daily-free",
                        "routeKind": "image-to-video",
                        "available": True,
                        "spendClass": "free",
                        "resetSeconds": 86400,
                        "maxRunsPerWindow": 3,
                        "maxSeconds": 5,
                    }],
                },
                {
                    "providerId": "included",
                    "profileId": "x",
                    "models": [{
                        "model": "included-reset",
                        "routeKind": "image-to-video",
                        "available": True,
                        "spendClass": "included",
                        "regeneratingAllowance": True,
                        "maxRunsPerWindow": 10,
                        "maxSeconds": 5,
                    }],
                },
                {
                    "providerId": "finite",
                    "profileId": "x",
                    "models": [{
                        "model": "finite-credits",
                        "routeKind": "image-to-video",
                        "available": True,
                        "spendClass": "free",
                        "creditCost": 2,
                        "creditBalance": 20,
                        "maxSeconds": 5,
                    }],
                },
                {
                    "providerId": "higgsfield",
                    "profileId": "higgsfield",
                    "models": [{
                        "model": "excellent-one-shot",
                        "routeKind": "motion-control",
                        "available": True,
                        "spendClass": "free",
                        "freeRunsRemaining": 1,
                        "entitlement": "one-free-run",
                        "maxSeconds": 30,
                    }],
                },
                {
                    "providerId": "paid",
                    "profileId": "x",
                    "models": [{
                        "model": "hero",
                        "routeKind": "image-to-video",
                        "available": True,
                        "spendClass": "paid",
                        "estimatedUsdMicros": 1000,
                        "maxSeconds": 10,
                    }],
                },
            ]
        }
        usage = {
            "providers": {
                "higgsfield": {
                    "events": 10,
                    "successes": 10,
                    "models": {
                        "excellent-one-shot": {
                            "events": 10, "candidateReady": 10, "accepted": 10, "declined": 0
                        }
                    },
                },
                "repeatable": {
                    "events": 10,
                    "successes": 4,
                    "models": {
                        "ugly-free": {
                            "events": 10, "candidateReady": 4, "accepted": 0, "declined": 4
                        }
                    },
                },
            }
        }
        ranked = resource_compass.rank_observation(observation, usage)
        rows = ranked["rows"]
        self.assertEqual(rows[0]["availabilityClass"], "local_repeatable_zero")
        provider_order = [row["providerId"] for row in rows[1:]]
        self.assertLess(provider_order.index("repeatable"), provider_order.index("higgsfield"))
        self.assertLess(provider_order.index("daily"), provider_order.index("higgsfield"))
        self.assertLess(provider_order.index("included"), provider_order.index("higgsfield"))
        self.assertLess(provider_order.index("finite"), provider_order.index("higgsfield"))
        self.assertLess(provider_order.index("higgsfield"), provider_order.index("paid"))
        h = next(row for row in rows if row["providerId"] == "higgsfield")
        self.assertEqual(h["availabilityClass"], "one_shot_promo")
        self.assertEqual(h["quality"]["keepRate"], 1.0)

    def test_compass_capacity_breaks_ties_before_quality(self):
        observation = {
            "providers": [
                {
                    "providerId": "small",
                    "models": [{
                        "model": "pretty",
                        "routeKind": "image-to-video",
                        "available": True,
                        "spendClass": "free",
                        "resetSeconds": 86400,
                        "maxRunsPerWindow": 1,
                        "secondsPerRun": 5,
                    }],
                },
                {
                    "providerId": "big",
                    "models": [{
                        "model": "rough",
                        "routeKind": "image-to-video",
                        "available": True,
                        "spendClass": "free",
                        "resetSeconds": 86400,
                        "maxRunsPerWindow": 6,
                        "secondsPerRun": 5,
                    }],
                },
            ]
        }
        usage = {
            "providers": {
                "small": {
                    "events": 2, "successes": 2,
                    "models": {"pretty": {"events": 2, "accepted": 2, "declined": 0}},
                },
                "big": {
                    "events": 2, "successes": 2,
                    "models": {"rough": {"events": 2, "accepted": 0, "declined": 2}},
                },
            }
        }
        rows = resource_compass.rank_observation(observation, usage)["rows"]
        providers = [r["providerId"] for r in rows]
        self.assertLess(providers.index("big"), providers.index("small"))
        big = next(r for r in rows if r["providerId"] == "big")
        small = next(r for r in rows if r["providerId"] == "small")
        self.assertEqual(big["capacitySeconds"], 30.0)
        self.assertEqual(small["capacitySeconds"], 5.0)


if __name__ == "__main__":
    unittest.main()
