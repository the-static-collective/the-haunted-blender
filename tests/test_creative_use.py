"""Prove byte reuse is independent of an accepted placement's identity."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

from haunted_blender import catalog, creative_take, creative_use, scene_artifact
from test_scene_artifact import ArtifactBridgeTests


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg unavailable")
class CreativeUseTests(unittest.TestCase):
    def setUp(self):
        ArtifactBridgeTests.setUp(self)
        source = Path(self.temp.name) / "one-synthetic-clip.mp4"
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i",
                        "testsrc2=s=320x180:r=24", "-t", "0.5", "-c:v", "mpeg4", str(source)],
                       capture_output=True, check=True)
        self.clip = source
        self.artifacts = []
        self.acceptances = []
        for choices in (self.choices[:1], self.choices):
            artifact = ArtifactBridgeTests.accept(self, choices)
            request = creative_take.request(self.root, artifact["snapshot"], 0,
                                            "Synthetic doorway motion only.",
                                            synthetic_source=True, disclose_to_provider=True)
            admitted = creative_take.admit(self.root, request["request"], source,
                                           provider_job_id="one-shared-video-job")
            acceptance = creative_take.accept(self.root, request["request"],
                                              admitted["video"], filmmaker_approval=True)
            self.artifacts.append(artifact)
            self.acceptances.append(acceptance)

    def test_same_bytes_two_uses_distinct_contexts_and_ancestors_survive(self):
        original_digest = catalog.digest_file(self.clip)
        a, b = [creative_use.record(self.root, art["snapshot"], acc["acceptance"],
                                    role="opening-shot", intent="Show the synthetic doorway")
                for art, acc in zip(self.artifacts, self.acceptances)]
        self.assertEqual(a["material_sha256"], b["material_sha256"])
        self.assertEqual(a["material_sha256"], original_digest)
        self.assertNotEqual(a["use_id"], b["use_id"])
        pair = creative_use.compare(self.root, a["use"], b["use"])
        witness = json.loads(Path(pair["comparison"]).read_text())
        self.assertEqual(len({u["artifact_sha256"] for u in witness["uses"]}), 2)
        self.assertEqual(creative_use.compare(self.root, a["use"], b["use"]), pair)
        self.assertEqual(catalog.digest_file(self.clip), original_digest)
        Path(a["use"]).unlink()
        # Removing a derived use does not alter another use or its source.
        self.assertEqual(creative_use.load(self.root, b["use"])[0]["material_sha256"], original_digest)
        self.assertEqual(catalog.digest_file(self.clip), original_digest)

    def test_roles_alone_and_changed_sources_cannot_masquerade_as_reuse(self):
        first = creative_use.record(self.root, self.artifacts[0]["snapshot"],
                                    self.acceptances[0]["acceptance"],
                                    role="opening-shot", intent="Door")
        second_role = creative_use.record(self.root, self.artifacts[0]["snapshot"],
                                          self.acceptances[0]["acceptance"],
                                          role="texture-study", intent="Door")
        with self.assertRaisesRegex(ValueError, "roles alone"):
            creative_use.compare(self.root, first["use"], second_role["use"])
        alternate = Path(self.temp.name) / "different-video.mp4"
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i",
                        "color=c=blue:s=320x180:r=24", "-t", "0.5", "-c:v", "mpeg4",
                        str(alternate)], capture_output=True, check=True)
        request = next(p for p in (self.root / "snapshots" / "creative-takes").glob("*.json")
                       if json.loads(p.read_text())["artifact_sha256"] == self.artifacts[1]["sha256"])
        admitted = creative_take.admit(self.root, request, alternate,
                                       provider_job_id="different-local-job")
        accepted = creative_take.accept(self.root, request, admitted["video"],
                                        filmmaker_approval=True)
        other = creative_use.record(self.root, self.artifacts[1]["snapshot"],
                                    accepted["acceptance"], role="opening-shot", intent="Other")
        with self.assertRaisesRegex(ValueError, "identical media bytes"):
            creative_use.compare(self.root, first["use"], other["use"])
        (self.photos / "cup.png").write_bytes(b"replaced")
        with self.assertRaisesRegex(ValueError, "Frozen source missing or changed"):
            creative_use.load(self.root, first["use"])


if __name__ == "__main__":
    unittest.main()
