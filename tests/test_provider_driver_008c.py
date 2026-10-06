import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from haunted_blender import cockpit, cockpit_engine, cockpit_media, provider_driver
from haunted_blender.dream_cutout_compiler import KIT_SCHEMA
from haunted_blender.motion_organ import OFFERS_SCHEMA


ADAPTER_SCRIPT = r'''
import hashlib
import json
import subprocess
import sys
from pathlib import Path

packet = json.loads(sys.stdin.read())
phase = packet["phase"]
provider = packet["providerId"]
payload = packet["payload"]
root = Path.cwd()
count = root / ("submit-count-" + provider + ".txt")

def result(value):
    print(json.dumps({
        "schema": "haunted-blender/provider-adapter-result/v1",
        "providerId": provider,
        "phase": phase,
        "ok": True,
        "result": value,
    }))
    raise SystemExit(0)

if phase == "CAPABILITIES":
    result({
        "observedAt": "2026-10-06T03:00:00Z",
        "available": True,
        "inputModes": ["image-to-video"],
        "aspectRatios": ["16:9"],
        "minSeconds": 0.5,
        "maxSeconds": 8,
    })

if phase == "QUOTE":
    paid = provider == "provider-paid"
    result({
        "observedAt": "2026-10-06T03:00:01Z",
        "exactConfiguration": True,
        "generatedDurationSeconds": max(1.0, float(payload["request"]["durationSeconds"])),
        "denomination": "USD",
        "amount": 0.05 if paid else 0,
        "wholeJobUsdMicros": 50000 if paid else 0,
    })

if phase == "SUBMIT":
    n = int(count.read_text() or "0") + 1 if count.exists() else 1
    count.write_text(str(n))
    if provider == "provider-crash":
        raise SystemExit(17)
    digest = hashlib.sha256(
        json.dumps(payload["request"], sort_keys=True).encode("utf-8")
    ).hexdigest()
    result({
        "observedAt": "2026-10-06T03:00:02Z",
        "vendorRequestId": "job-" + provider + "-" + str(n),
        "submittedParameterSha256": digest,
    })

if phase == "STATUS":
    result({
        "observedAt": "2026-10-06T03:00:03Z",
        "status": "completed",
        "queueSeconds": 0.1,
        "runtimeSeconds": 0.2,
    })

if phase == "FETCH":
    out = Path(payload["outputPath"])
    out.parent.mkdir(parents=True, exist_ok=True)
    duration = max(1.0, float(payload["request"]["durationSeconds"]) + 0.1)
    subprocess.run([
        "ffmpeg", "-v", "error", "-y",
        "-f", "lavfi", "-i", f"color=c=blue:s=96x54:d={duration}:r=8",
        "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)
    ], check=True)
    result({
        "observedAt": "2026-10-06T03:00:04Z",
        "container": "mp4",
        "codec": "h264",
    })

print(json.dumps({
    "schema": "haunted-blender/provider-adapter-result/v1",
    "providerId": provider,
    "phase": phase,
    "ok": False,
    "error": "unknown phase",
}))
'''


class ProviderDriver008cTests(unittest.TestCase):
    def setUp(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("FFmpeg required")
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow required")
        self.Image = Image

    def make_project(self, root: Path, offers):
        cockpit.create_project(root, project_id="provider-008c", title="Provider Film", local_only=True)
        cockpit.add_section(root, section_id="chorus", kind="chorus", start=0, end=2.0, label="Chorus")

        self.Image.new("RGBA", (96, 54), (30, 35, 50, 255)).save(root / "bg.png")
        self.Image.new("RGBA", (20, 30), (220, 180, 80, 255)).save(root / "actor.png")
        kit = {
            "schema": KIT_SCHEMA,
            "canvas": {"width": 96, "height": 54},
            "layers": [
                {"id": "background", "role": "background", "source": "bg.png", "z": 0, "x": 0, "y": 0},
                {"id": "actor", "role": "actor", "source": "actor.png", "z": 1, "x": 20, "y": 20},
            ],
        }
        (root / "kit.json").write_text(json.dumps(kit), encoding="utf-8")
        snapshot = {
            "schema": OFFERS_SCHEMA,
            "observedAt": "2026-10-06T02:59:00Z",
            "offers": offers,
        }
        (root / "offers.json").write_text(json.dumps(snapshot), encoding="utf-8")
        (root / "adapter.py").write_text(ADAPTER_SCRIPT, encoding="utf-8")

        cockpit_engine.configure_project(
            root,
            source_receipt_ids=["receipt-provider-test"],
            kit_path="kit.json",
            motion_offers_path="offers.json",
            fps=8,
            preview_seconds=0.5,
            occurrence_budget_usd_micros=100000,
            per_job_budget_usd_micros=75000,
        )

        provider_ids = sorted({o["providerId"] for o in offers})
        provider_driver.configure_adapters(
            root,
            [
                {
                    "providerId": provider_id,
                    "transport": "command",
                    "argv": [sys.executable, str(root / "adapter.py")],
                    "cwd": ".",
                    "timeoutSeconds": 60,
                }
                for provider_id in provider_ids
            ],
        )
        cockpit_engine.grow(root, "chorus")
        cockpit_engine.keep(root, "chorus", slot=1)
        cockpit.set_local_only(root, False)
        cockpit_engine.awaken(root, "chorus")

    def offer(self, offer_id, provider_id, spend="free", usd=None, burn=1):
        value = {
            "offerId": offer_id,
            "providerId": provider_id,
            "model": "test-i2v",
            "available": True,
            "spendClass": spend,
            "inputModes": ["image-to-video"],
            "aspectRatios": ["16:9"],
            "minSeconds": 0.5,
            "maxSeconds": 8,
        }
        if spend == "paid":
            value["estimatedUsdMicros"] = usd if usd is not None else 50000
        else:
            value["creditCost"] = burn
            value["creditBalance"] = 100
        return value

    def test_free_adapter_runs_to_candidate_and_human_keep_splices_window(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_project(root, [self.offer("free-a", "provider-free")])

            result = provider_driver.drive(root, "chorus")
            self.assertEqual(result["status"], "candidate_ready")
            view = provider_driver.provider_view(root, "chorus")
            self.assertEqual(view["nextAction"], "PRESENT")
            self.assertEqual(len(view["candidates"]), 1)
            candidate = view["candidates"][0]["relativePath"]
            self.assertTrue(candidate)

            kept = provider_driver.accept_candidate(root, "chorus", candidate)
            self.assertEqual(kept["status"], "witnessed")
            self.assertEqual(cockpit.cockpit_view(root)["sections"][0]["temperature"], "witnessed")
            self.assertTrue(Path(kept["awakenedScene"]).is_file())
            media = cockpit_media.media_view(root, "chorus")
            self.assertIn("awakened-", media["scene"]["path"])

    def test_paid_exact_quote_requires_separate_one_time_approval(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_project(root, [self.offer("paid-a", "provider-paid", spend="paid", usd=50000)])

            first = provider_driver.drive(root, "chorus")
            self.assertEqual(first["status"], "approval_required")
            view = provider_driver.provider_view(root, "chorus")
            self.assertTrue(view["approvalRequired"])
            self.assertEqual(view["quote"]["wholeJobUsdMicros"], 50000)
            self.assertFalse((root / "submit-count-provider-paid.txt").exists())

            with self.assertRaises(ValueError):
                provider_driver.approve_spend(
                    root, "chorus", expected_usd_micros=49999,
                    approved_at="2026-10-06T03:01:00Z"
                )
            provider_driver.approve_spend(
                root, "chorus", expected_usd_micros=50000,
                approved_at="2026-10-06T03:01:00Z"
            )
            second = provider_driver.drive(root, "chorus")
            self.assertEqual(second["status"], "candidate_ready")
            self.assertEqual((root / "submit-count-provider-paid.txt").read_text(), "1")

    def test_interrupted_submit_never_resubmits_and_can_reconcile_existing_job(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_project(root, [self.offer("free-crash", "provider-crash")])

            with self.assertRaises(RuntimeError):
                provider_driver.drive(root, "chorus")
            count = root / "submit-count-provider-crash.txt"
            self.assertEqual(count.read_text(), "1")

            second = provider_driver.drive(root, "chorus")
            self.assertEqual(second["status"], "reconcile_required")
            self.assertEqual(count.read_text(), "1")
            view = provider_driver.provider_view(root, "chorus")
            self.assertTrue(view["reconcileRequired"])
            self.assertEqual(view["nextAction"], "RECONCILE_SUBMISSION")

            provider_driver.reconcile_submission(
                root,
                "chorus",
                vendor_request_id="job-provider-crash-1",
                submitted_parameter_sha256="c" * 64,
                observed_at="2026-10-06T03:02:00Z",
            )
            final = provider_driver.drive(root, "chorus")
            self.assertEqual(final["status"], "candidate_ready")
            self.assertEqual(count.read_text(), "1")

    def test_editorial_decline_preserves_candidate_and_opens_next_provider(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_project(
                root,
                [
                    self.offer("free-a", "provider-a", burn=1),
                    self.offer("free-b", "provider-b", burn=2),
                ],
            )

            first = provider_driver.drive(root, "chorus")
            self.assertEqual(first["status"], "candidate_ready")
            self.assertEqual(len(provider_driver.provider_view(root, "chorus")["candidates"]), 1)

            declined = provider_driver.decline_current_candidate(
                root, "chorus", reason="want another texture"
            )
            self.assertEqual(declined["view"]["nextAction"], "CAPABILITIES")

            second = provider_driver.drive(root, "chorus")
            self.assertEqual(second["status"], "candidate_ready")
            board = provider_driver.provider_view(root, "chorus")
            self.assertEqual(len(board["candidates"]), 2)
            self.assertNotEqual(
                board["candidates"][0]["providerId"],
                board["candidates"][1]["providerId"],
            )


if __name__ == "__main__":
    unittest.main()
