import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from haunted_blender import accepted_video, motion_organ
from haunted_blender.motion_video_resolver import resolve_accepted_motion_video_for_serve


class MotionOrgan006Tests(unittest.TestCase):
    def setUp(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("FFmpeg required")

    def root(self, td):
        root = Path(td)
        root.mkdir(exist_ok=True)
        return root

    def make_video(self, path: Path, color: str, duration=2.0):
        subprocess.run(
            [
                "ffmpeg", "-v", "error", "-y",
                "-f", "lavfi", "-i", f"color=c={color}:s=96x64:d={duration}:r=8",
                "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path),
            ],
            check=True,
        )

    def request(self, root):
        return motion_organ.freeze_request(
            root,
            scene_id="scene-006",
            scene_sha256="a" * 64,
            window_id="awaken-chorus",
            start_seconds=12.0,
            duration_seconds=1.5,
            prompt="The cardboard world briefly becomes fully moving desert wind.",
            source_address="sha256:" + "b" * 64,
            input_mode="image-to-video",
            aspect_ratio="16:9",
            remote_disclosure_approved=True,
        )

    def offers(self, root):
        snapshot = {
            "schema": motion_organ.OFFERS_SCHEMA,
            "observedAt": "2026-10-05T23:00:00Z",
            "offers": [
                {
                    "offerId": "paid-fast",
                    "providerId": "provider-paid",
                    "model": "v1",
                    "available": True,
                    "spendClass": "paid",
                    "estimatedUsdMicros": 250000,
                    "inputModes": ["image-to-video"],
                    "aspectRatios": ["16:9"],
                    "minSeconds": 1,
                    "maxSeconds": 10,
                },
                {
                    "offerId": "free-heavy-burn",
                    "providerId": "provider-free-b",
                    "model": "free-b",
                    "available": True,
                    "spendClass": "free",
                    "creditCost": 40,
                    "creditBalance": 50,
                    "inputModes": ["image-to-video"],
                    "aspectRatios": ["16:9"],
                    "minSeconds": 1,
                    "maxSeconds": 4,
                },
                {
                    "offerId": "free-light-burn",
                    "providerId": "provider-free-a",
                    "model": "free-a",
                    "available": True,
                    "spendClass": "free",
                    "creditCost": 2,
                    "creditBalance": 20,
                    "inputModes": ["image-to-video"],
                    "aspectRatios": ["16:9"],
                    "minSeconds": 1,
                    "maxSeconds": 8,
                },
                {
                    "offerId": "wrong-ratio",
                    "providerId": "provider-x",
                    "model": "x",
                    "available": True,
                    "spendClass": "free",
                    "creditCost": 1,
                    "creditBalance": 100,
                    "inputModes": ["image-to-video"],
                    "aspectRatios": ["9:16"],
                    "minSeconds": 1,
                    "maxSeconds": 8,
                },
            ],
        }
        return motion_organ.freeze_offers(root, snapshot)

    def test_router_prefers_eligible_free_low_burn_then_paid(self):
        with tempfile.TemporaryDirectory() as td:
            root = self.root(td)
            request = self.request(root)
            offers = self.offers(root)
            route = motion_organ.route_request(root, request["request"], offers["offers"])
            ids = [a["offerId"] for a in route["routeBody"]["attempts"]]
            self.assertEqual(ids, ["free-light-burn", "free-heavy-burn", "paid-fast"])
            self.assertNotIn("wrong-ratio", ids)

    def test_relatte_spec_is_provider_opaque(self):
        with tempfile.TemporaryDirectory() as td:
            root = self.root(td)
            request = self.request(root)
            offers = self.offers(root)
            route = motion_organ.route_request(root, request["request"], offers["offers"])
            spec = motion_organ.to_relatte_organ_spec(
                root, route["route"],
                created_at="2026-10-05T23:00:00Z",
                source_world="franken-blender",
                source_particular="scene-006:awaken-chorus",
                return_address="blender://motion-organ/return",
            )
            self.assertEqual(spec["schema"], "relatte.opaque-organ-spec/v0")
            self.assertEqual(spec["artifact_kind"], "MOTION_AWAKENING_REQUEST")
            self.assertTrue(spec["donor_claims"]["provider_semantics_opaque"])
            self.assertNotIn("provider-free-a", json.dumps(spec))

    def test_candidate_board_keep_and_generic_resolver(self):
        with tempfile.TemporaryDirectory() as td:
            root = self.root(td)
            request = self.request(root)
            offers = self.offers(root)
            route = motion_organ.route_request(root, request["request"], offers["offers"])

            a = root / "a.mp4"
            b = root / "b.mp4"
            self.make_video(a, "red")
            self.make_video(b, "blue")
            ca = motion_organ.admit_candidate(
                root, route["route"], "free-light-burn", a, provider_job_id="job-a-001"
            )
            cb = motion_organ.admit_candidate(
                root, route["route"], "free-heavy-burn", b, provider_job_id="job-b-001"
            )
            board = motion_organ.candidate_board(root, request["request"])
            self.assertEqual(board["authority"], "comparison-only")
            self.assertEqual(len(board["candidates"]), 2)

            kept = motion_organ.accept_candidate(
                root, request["request"], ca["video"], filmmaker_approval=True
            )
            address = "sha256:" + kept["videoSha256"]
            descriptor, video = resolve_accepted_motion_video_for_serve(root, address)
            self.assertEqual(descriptor["providerId"], "provider-free-a")
            self.assertEqual(video, Path(kept["video"]))
            composite, composite_video = accepted_video.resolve_accepted_video_for_serve(root, address)
            self.assertEqual(composite["sha256"], kept["videoSha256"])
            self.assertEqual(composite_video, Path(kept["video"]))

    def test_acceptance_refuses_changed_candidate_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            root = self.root(td)
            request = self.request(root)
            offers = self.offers(root)
            route = motion_organ.route_request(root, request["request"], offers["offers"])
            a = root / "a.mp4"
            self.make_video(a, "red")
            candidate = motion_organ.admit_candidate(
                root, route["route"], "free-light-burn", a, provider_job_id="job-a-001"
            )
            kept = motion_organ.accept_candidate(
                root, request["request"], candidate["video"], filmmaker_approval=True
            )
            Path(kept["video"]).write_bytes(b"tampered")
            with self.assertRaises(Exception):
                resolve_accepted_motion_video_for_serve(root, "sha256:" + kept["videoSha256"])


if __name__ == "__main__":
    unittest.main()
