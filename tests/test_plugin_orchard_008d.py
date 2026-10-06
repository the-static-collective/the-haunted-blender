import json
import shutil
import tempfile
import unittest
from pathlib import Path

from haunted_blender import (
    cockpit,
    cockpit_engine,
    motion_organ,
    plugin_bridge,
    plugin_orchard,
    provider_driver,
)
from haunted_blender.dream_cutout_compiler import KIT_SCHEMA


class PluginOrchard008dTests(unittest.TestCase):
    def setUp(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("FFmpeg required")
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow required")
        self.Image = Image

    def observation(self, *, provider_id="higgsfield", profile_id="higgsfield"):
        return [
            {
                "providerId": provider_id,
                "profileId": profile_id,
                "label": "Bridge Provider",
                "connected": True,
                "accountClass": "free",
                "models": [
                    {
                        "model": "free-motion-control",
                        "routeKind": "motion-control",
                        "available": True,
                        "spendClass": "free",
                        "creditCost": 0,
                        "creditBalance": 10,
                        "aspectRatios": ["16:9"],
                        "minSeconds": 0.5,
                        "maxSeconds": 30,
                        "freeRunsRemaining": 1,
                        "entitlement": "one-free-run",
                    }
                ],
            }
        ]

    def make_project(self, root: Path):
        cockpit.create_project(root, project_id="orchard-008d", title="Orchard Film", local_only=True)
        cockpit.add_section(root, section_id="chorus", kind="chorus", start=0, end=2.0, label="Chorus")
        self.Image.new("RGBA", (96, 54), (20, 30, 40, 255)).save(root / "bg.png")
        self.Image.new("RGBA", (20, 30), (230, 180, 70, 255)).save(root / "actor.png")
        kit = {
            "schema": KIT_SCHEMA,
            "canvas": {"width": 96, "height": 54},
            "layers": [
                {"id": "background", "role": "background", "source": "bg.png", "z": 0, "x": 0, "y": 0},
                {"id": "actor", "role": "actor", "source": "actor.png", "z": 1, "x": 20, "y": 20},
            ],
        }
        (root / "kit.json").write_text(json.dumps(kit), encoding="utf-8")
        cockpit_engine.configure_project(
            root,
            source_receipt_ids=["receipt-orchard-test"],
            kit_path="kit.json",
            fps=8,
            preview_seconds=0.5,
            occurrence_budget_usd_micros=100000,
            per_job_budget_usd_micros=50000,
        )
        plugin_orchard.ingest_observation(
            root,
            observed_at="2026-10-06T03:30:00Z",
            providers=self.observation(),
            source="test-crawler",
        )
        provider_driver.configure_adapters(
            root,
            [
                {
                    "providerId": "higgsfield",
                    "transport": "plugin_bridge",
                    "profileId": "higgsfield",
                }
            ],
        )
        cockpit_engine.grow(root, "chorus")
        cockpit_engine.keep(root, "chorus", slot=1)
        cockpit.set_local_only(root, False)
        awakened = cockpit_engine.awaken(root, "chorus")
        return awakened

    def resolve_pending(self, root: Path, result: dict, *, claim=False):
        pending = plugin_bridge.pending(root)
        self.assertEqual(len(pending), 1)
        call = pending[0]
        if claim:
            plugin_bridge.claim(
                root,
                call["callSha256"],
                claimed_at="2026-10-06T03:31:00Z",
                actor="test-bridge",
            )
        plugin_bridge.resolve(
            root,
            call["callSha256"],
            result=result,
            resolved_at="2026-10-06T03:31:01Z",
            raw_reference="test-plugin-result",
        )
        return call

    def make_video(self, path: Path, duration=1.2):
        path.parent.mkdir(parents=True, exist_ok=True)
        import subprocess
        subprocess.run(
            [
                "ffmpeg", "-v", "error", "-y",
                "-f", "lavfi", "-i", f"color=c=purple:s=96x54:d={duration}:r=8",
                "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                str(path),
            ],
            check=True,
        )

    def test_orchard_snapshot_exports_free_motion_offer_and_latest_pointer(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            result = plugin_orchard.ingest_observation(
                root,
                observed_at="2026-10-06T03:30:00Z",
                providers=self.observation(),
                source="test-crawler",
            )
            latest = plugin_orchard.latest(root)
            self.assertEqual(latest["motionOffersSha256"], result["offersSha256"])
            offers, _ = motion_organ.load_offers(root, result["offers"])
            self.assertEqual(len(offers["offers"]), 1)
            offer = offers["offers"][0]
            self.assertEqual(offer["providerId"], "higgsfield")
            self.assertEqual(offer["spendClass"], "free")
            self.assertTrue(offer["available"])
            self.assertIn("image-to-video", offer["inputModes"])
            observation_text = Path(result["observation"]).read_text(encoding="utf-8")
            self.assertNotIn("email", observation_text.lower())

    def test_orchard_marks_unquoted_paid_plugin_unavailable(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            providers = [
                {
                    "providerId": "openart",
                    "profileId": "openart",
                    "connected": True,
                    "models": [
                        {
                            "model": "pixverseV6",
                            "routeKind": "image-to-video",
                            "available": True,
                            "spendClass": "paid",
                            "aspectRatios": ["16:9"],
                            "minSeconds": 1,
                            "maxSeconds": 10,
                        }
                    ],
                }
            ]
            result = plugin_orchard.ingest_observation(
                root,
                observed_at="2026-10-06T03:30:00Z",
                providers=providers,
            )
            offers, _ = motion_organ.load_offers(root, result["offers"])
            self.assertFalse(offers["offers"][0]["available"])
            self.assertIn("refresh/preflight", " ".join(offers["offers"][0]["notes"]))

    def test_awaken_uses_orchard_and_extracts_bounded_driving_clip(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            awakened = self.make_project(root)
            view = cockpit_engine.engine_view(root, "chorus")
            self.assertEqual(view["engine"]["motionOffersSource"], "plugin-orchard")
            self.assertTrue((root / view["engine"]["motionSourceImagePath"]).is_file())
            self.assertTrue((root / view["engine"]["motionSourceVideoPath"]).is_file())
            self.assertTrue(Path(awakened["sourceDrivingClip"]).is_file())
            self.assertEqual(awakened["next"]["action"], "CAPABILITIES")

    def test_plugin_bridge_full_free_route_reaches_real_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_project(root)

            first = provider_driver.drive(root, "chorus")
            self.assertEqual(first["status"], "plugin_bridge_required")
            self.assertEqual(first["bridge"]["packet"]["phase"], "CAPABILITIES")
            first_sha = first["bridge"]["callSha256"]

            same = provider_driver.drive(root, "chorus")
            self.assertEqual(same["status"], "plugin_bridge_required")
            self.assertEqual(same["bridge"]["callSha256"], first_sha)

            self.resolve_pending(
                root,
                {
                    "observedAt": "2026-10-06T03:31:02Z",
                    "available": True,
                    "inputModes": ["image-to-video"],
                    "aspectRatios": ["16:9"],
                    "minSeconds": 0.5,
                    "maxSeconds": 30,
                },
            )
            second = provider_driver.drive(root, "chorus")
            self.assertEqual(second["status"], "plugin_bridge_required")
            self.assertEqual(second["bridge"]["packet"]["phase"], "QUOTE")

            self.resolve_pending(
                root,
                {
                    "observedAt": "2026-10-06T03:31:03Z",
                    "exactConfiguration": True,
                    "generatedDurationSeconds": 1.0,
                    "denomination": "provider-credits",
                    "amount": 0,
                    "wholeJobUsdMicros": 0,
                },
            )
            third = provider_driver.drive(root, "chorus")
            self.assertEqual(third["status"], "plugin_bridge_required")
            self.assertEqual(third["bridge"]["packet"]["phase"], "SUBMIT")
            self.resolve_pending(
                root,
                {
                    "observedAt": "2026-10-06T03:31:04Z",
                    "vendorRequestId": "plugin-job-1",
                    "submittedParameterSha256": "a" * 64,
                },
                claim=True,
            )

            fourth = provider_driver.drive(root, "chorus")
            self.assertEqual(fourth["status"], "plugin_bridge_required")
            self.assertEqual(fourth["bridge"]["packet"]["phase"], "STATUS")
            self.resolve_pending(
                root,
                {
                    "observedAt": "2026-10-06T03:31:05Z",
                    "status": "completed",
                    "queueSeconds": 0.1,
                    "runtimeSeconds": 0.2,
                },
            )

            fifth = provider_driver.drive(root, "chorus")
            self.assertEqual(fifth["status"], "plugin_bridge_required")
            self.assertEqual(fifth["bridge"]["packet"]["phase"], "FETCH")
            source = root / "external-plugin-output.mp4"
            self.make_video(source, duration=1.2)
            self.resolve_pending(
                root,
                {
                    "observedAt": "2026-10-06T03:31:06Z",
                    "localPath": str(source),
                    "container": "mp4",
                    "codec": "h264",
                },
            )
            final = provider_driver.drive(root, "chorus")
            self.assertEqual(final["status"], "candidate_ready")
            view = provider_driver.provider_view(root, "chorus")
            self.assertEqual(view["nextAction"], "PRESENT")
            self.assertEqual(len(view["candidates"]), 1)
            self.assertEqual(view["adapter"]["transport"], "plugin_bridge")
            usage = plugin_orchard.usage_summary(root)
            self.assertGreaterEqual(usage["events"], 5)
            self.assertEqual(usage["providers"]["higgsfield"]["candidateReady"], 1)

    def test_claimed_unresolved_plugin_submit_refuses_replay(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_project(root)
            provider_driver.drive(root, "chorus")
            self.resolve_pending(
                root,
                {
                    "observedAt": "2026-10-06T03:32:00Z",
                    "available": True,
                    "inputModes": ["image-to-video"],
                    "aspectRatios": ["16:9"],
                    "minSeconds": 0.5,
                    "maxSeconds": 30,
                },
            )
            provider_driver.drive(root, "chorus")
            self.resolve_pending(
                root,
                {
                    "observedAt": "2026-10-06T03:32:01Z",
                    "exactConfiguration": True,
                    "generatedDurationSeconds": 1.0,
                    "denomination": "provider-credits",
                    "amount": 0,
                    "wholeJobUsdMicros": 0,
                },
            )
            pending_submit = provider_driver.drive(root, "chorus")
            self.assertEqual(pending_submit["bridge"]["packet"]["phase"], "SUBMIT")
            plugin_bridge.claim(
                root,
                pending_submit["bridge"]["callSha256"],
                claimed_at="2026-10-06T03:32:02Z",
            )

            stopped = provider_driver.drive(root, "chorus")
            self.assertEqual(stopped["status"], "reconcile_required")
            self.assertIn("do not replay", stopped["reason"])
            view = provider_driver.provider_view(root, "chorus")
            self.assertTrue(view["reconcileRequired"])
            self.assertEqual(view["nextAction"], "RECONCILE_SUBMISSION")

    def test_usage_index_learns_accept_and_decline_counts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            plugin_orchard.record_usage(
                root,
                observed_at="2026-10-06T03:33:00Z",
                provider_id="picsart",
                model="model-a",
                phase="fetch",
                outcome="candidate_ready",
                latency_ms=1200,
                candidate_sha256="b" * 64,
            )
            plugin_orchard.record_usage(
                root,
                observed_at="2026-10-06T03:33:01Z",
                provider_id="picsart",
                model="model-a",
                phase="editorial",
                outcome="accepted",
                latency_ms=800,
                candidate_sha256="b" * 64,
            )
            summary = plugin_orchard.usage_summary(root)
            row = summary["providers"]["picsart"]
            self.assertEqual(row["events"], 2)
            self.assertEqual(row["meanLatencyMs"], 1000.0)
            self.assertEqual(row["models"]["model-a"]["accepted"], 1)


if __name__ == "__main__":
    unittest.main()
