"""Accepted-video resolver contract."""
from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path

from haunted_blender import catalog, creative_take, video_resolver
from test_scene_artifact import ArtifactBridgeTests


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg unavailable")
class VideoResolverTests(unittest.TestCase):
    def setUp(self):
        ArtifactBridgeTests.setUp(self)
        self.artifact = ArtifactBridgeTests.accept(self)
        request = creative_take.request(
            self.root,
            self.artifact["snapshot"],
            1,
            "Synthetic moving patterns; no people.",
            synthetic_source=True,
            disclose_to_provider=True,
        )
        self.request = request["request"]

        source = Path(self.temp.name) / "moving.mp4"
        subprocess.run(
            [
                "ffmpeg", "-nostdin", "-loglevel", "error",
                "-f", "lavfi", "-i", "testsrc2=s=320x180:r=24",
                "-t", "1", "-c:v", "mpeg4", str(source),
            ],
            check=True,
        )
        admitted = creative_take.admit(
            self.root,
            request["request"],
            source,
            provider_job_id="resolver-video-job-001",
        )
        self.video = Path(admitted["video"])
        accepted = creative_take.accept(
            self.root,
            request["request"],
            self.video,
            filmmaker_approval=True,
        )
        self.acceptance = Path(accepted["acceptance"])
        self.digest = accepted["video_sha256"]
        self.address = "sha256:" + self.digest

    def test_filmmaker_accepted_take_resolves_after_reverification(self):
        descriptor = video_resolver.resolve_accepted_video(self.root, self.address)
        self.assertEqual(
            descriptor["status"],
            "resolved-filmmaker-accepted-private-take",
        )
        self.assertEqual(descriptor["address"], self.address)
        self.assertEqual(descriptor["sha256"], self.digest)
        self.assertEqual(descriptor["mediaType"], "video/mp4")
        self.assertFalse(descriptor["distributionAuthorized"])
        self.assertEqual(descriptor["authority"], "none")
        self.assertGreater(descriptor["durationSeconds"], 0)
        self.assertIn("RESOLUTION REQUIRES BYTE REVERIFICATION", descriptor["boundary"])

    def test_unaccepted_candidate_does_not_resolve(self):
        self.acceptance.unlink()
        with self.assertRaises(video_resolver.VideoResolverError) as caught:
            video_resolver.resolve_accepted_video(self.root, self.address)
        self.assertEqual(caught.exception.code, "NOT_FOUND")

    def test_changed_video_bytes_fail_closed(self):
        self.video.write_bytes(b"tampered")
        with self.assertRaises(video_resolver.VideoResolverError) as caught:
            video_resolver.resolve_accepted_video(self.root, self.address)
        self.assertEqual(caught.exception.code, "STALE_ACCEPTANCE")

    def test_changed_acceptance_identity_fails_closed(self):
        witness = json.loads(self.acceptance.read_text(encoding="utf-8"))
        witness["beat"] = 99
        self.acceptance.write_text(json.dumps(witness), encoding="utf-8")
        with self.assertRaises(video_resolver.VideoResolverError) as caught:
            video_resolver.resolve_accepted_video(self.root, self.address)
        self.assertEqual(caught.exception.code, "STALE_ACCEPTANCE")

    def test_non_sha_address_refuses(self):
        with self.assertRaises(video_resolver.VideoResolverError) as caught:
            video_resolver.resolve_accepted_video(self.root, "file:///private/movie.mp4")
        self.assertEqual(caught.exception.code, "INVALID_ADDRESS")


if __name__ == "__main__":
    unittest.main()
