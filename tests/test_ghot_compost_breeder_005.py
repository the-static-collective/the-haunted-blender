import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "integrations" / "ghot" / "compost_breeder_adapter.py"
MANIFEST = ROOT / "integrations" / "ghot" / "adapter-manifest.json"


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class GhotCompostBreeder005Tests(unittest.TestCase):
    def setUp(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("FFmpeg and FFprobe required")
        try:
            import PIL  # noqa: F401
        except ImportError:
            self.skipTest("Pillow required")

    def request(self):
        return {
            "schema": "ghot.compost-breeder-request/v0",
            "authority": "proposal-request-only",
            "parentHistoryRef": {
                "schema": "static-collective/rendered-history-capsule/v0",
                "capsuleHash": "a" * 64,
                "generation": 1,
                "renderedMediaSha256": "b" * 64,
                "parentCapsuleHashes": [],
                "authority": "provenance-only",
            },
            "relationId": "relation:history-compost:live-blender",
            "sourceReceiptIds": ["receipt:render:g1"],
            "requestedEffect": "GROW_SIX_UNBORN_FILM_PREVIEWS",
            "donorContractRefs": {},
            "laws": [],
        }

    def run_adapter(self, payload, out_root):
        env = {
            **os.environ,
            "HAUNTED_BLENDER_GHOT_OUTPUT_DIR": str(out_root),
        }
        return subprocess.run(
            ["python3", str(ADAPTER)],
            input=json.dumps(payload),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(ROOT),
            env=env,
            check=False,
            timeout=60,
        )

    def test_manifest_exposes_only_bounded_sixup_capability(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema"], "ghot.external-adapter-manifest/v0")
        self.assertEqual(manifest["adapter_id"], "haunted-blender.compost-breeder")
        self.assertEqual(len(manifest["capabilities"]), 1)
        capability = manifest["capabilities"][0]
        self.assertEqual(capability["capability"], "creative.blender.dreambreed.sixup")
        self.assertEqual(capability["protocol"], "stdin-json/stdout-json-v0")
        self.assertFalse(capability["limits"]["network"])
        self.assertFalse(capability["limits"]["arbitrary_shell"])
        self.assertFalse(capability["limits"]["selection"])
        self.assertFalse(capability["limits"]["keep"])

    def test_real_dreambreeder_and_cutout_sixup_return_unresolved_donor_evidence(self):
        with tempfile.TemporaryDirectory(prefix="blender-ghot-005-") as td:
            out_root = Path(td) / "out"
            first = self.run_adapter(self.request(), out_root)
            self.assertEqual(first.returncode, 0, first.stderr)
            result = json.loads(first.stdout)

            self.assertEqual(
                result["schema"],
                "haunted-blender/ghot-compost-breeder-result/v1",
            )
            self.assertEqual(
                result["capability"],
                "creative.blender.dreambreed.sixup",
            )
            self.assertEqual(result["authority"], "donor-result-evidence")

            ecology = result["ecology"]
            self.assertEqual(ecology["schema"], "haunted-blender/dream-ecology/v1")
            self.assertEqual(ecology["relationId"], self.request()["relationId"])
            self.assertEqual(
                ecology["commonCheckpointId"],
                self.request()["parentHistoryRef"]["capsuleHash"],
            )
            self.assertEqual(ecology["generation"], 2)
            self.assertEqual(len(ecology["proposals"]), 6)
            self.assertIsNone(ecology["disposition"])
            self.assertTrue(
                all(item["authorityClass"] == "proposal" for item in ecology["proposals"])
            )

            sixup = result["sixup"]
            self.assertEqual(
                sixup["schema"],
                "haunted-blender/dream-sixup-preview/v1",
            )
            self.assertEqual(sixup["authorityClass"], "proposal-preview")
            self.assertEqual(sixup["ecologyId"], ecology["id"])
            self.assertEqual(len(sixup["previews"]), 6)
            self.assertTrue(
                all(item["authorityClass"] == "proposal-preview" for item in sixup["previews"])
            )

            contact = Path(sixup["contactSheetVideo"])
            self.assertTrue(contact.is_file())
            self.assertGreater(contact.stat().st_size, 0)
            self.assertEqual(
                hashlib.sha256(contact.read_bytes()).hexdigest(),
                sixup["contactSheetSha256"],
            )
            for preview in sixup["previews"]:
                path = Path(preview["videoPath"])
                self.assertTrue(path.is_file())
                self.assertGreater(path.stat().st_size, 0)
                self.assertEqual(
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                    preview["videoSha256"],
                )

            for name, value in (("ecology", ecology), ("sixup", sixup)):
                text_value = result["artifact"][f"{name}_text"]
                self.assertEqual(
                    result["artifact"][f"{name}_sha256"],
                    sha256_text(text_value),
                )
                self.assertEqual(json.loads(text_value), value)

            second = self.run_adapter(self.request(), out_root)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(json.loads(second.stdout), result)
            self.assertIsNone(result["ecology"]["disposition"])

    def test_invalid_request_refuses_before_output(self):
        with tempfile.TemporaryDirectory(prefix="blender-ghot-005-bad-") as td:
            out_root = Path(td) / "out"
            bad = self.request()
            bad["authority"] = "continuation-permission"
            completed = self.run_adapter(bad, out_root)
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn(
                "COMPOST_BREEDER_REQUEST_AUTHORITY_MISMATCH",
                completed.stderr,
            )
            self.assertFalse(out_root.exists())


if __name__ == "__main__":
    unittest.main()
