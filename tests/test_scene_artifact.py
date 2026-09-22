"""Proof of the actual SceneWorld -> immutable artifact -> existing N0 MP4 bridge."""
import json
import shutil
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from haunted_blender import alchemy, catalog, project, render, scene_artifact, scene_weave


def png(path, rgb):
    width, height = 48, 32
    pixels = (b"\x00" + bytes(rgb) * width) * height

    def chunk(kind, data):
        return (struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff))
    path.write_bytes(b"\x89PNG\r\n\x1a\n"
                     + chunk(b"IHDR", struct.pack(">2I5B", width, height, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(pixels))
                     + chunk(b"IEND", b""))


def fictional_story():
    by = scene_weave.AUTHOR
    return {
        "title": "The Unopened Letter",
        "entities": [
            {"id": "mother", "kind": "character", "name": "Mother", "basis": by},
            {"id": "daughter", "kind": "character", "name": "Daughter", "basis": by},
            {"id": "letter", "kind": "prop", "name": "Letter", "basis": by},
        ],
        "facts": [
            {"id": "sealed", "subject": "letter", "predicate": "state",
             "value": "sealed", "since_beat": 0, "basis": by},
            {"id": "sender", "subject": "letter", "predicate": "sender",
             "value": "mother", "since_beat": 0, "basis": by},
        ],
        "beats": [
            {"id": "arrival", "index": 0},
            {"id": "decision", "index": 1},
            {"id": "departure", "index": 2},
        ],
        "knowledge": [
            {"id": "mother-knows", "observer": "mother",
             "fact_id": "sender", "since_beat": 0, "basis": by},
            {"id": "audience-sees", "observer": "audience",
             "fact_id": "sealed", "since_beat": 0, "basis": by},
        ],
        "relations": [],
        "affordances": [],
        "questions": [{"id": "who", "text": "Who wrote it?", "status": "open"}],
    }


class ArtifactBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "library"
        catalog.init(self.root)
        self.photos = Path(self.temp.name) / "photos"
        self.photos.mkdir()
        for name, rgb in (("cup", (150, 70, 50)), ("water", (25, 70, 160)),
                          ("moon", (200, 200, 150))):
            png(self.photos / (name + ".png"), rgb)
        catalog.scan(self.root, self.photos)
        con = catalog.connect(self.root)
        ids = {Path(r["path"]).stem: r["id"] for r in
               con.execute("SELECT path,id FROM assets")}
        con.close()
        recipe = alchemy.create(self.root, ids["cup"], ids["moon"], bridge=ids["water"],
                                relation="triadic-bridge", statement="Fictional motif")
        self.alchemy_snapshot = alchemy.freeze(self.root, recipe["id"])
        self.seed = scene_weave.from_alchemy(self.root, self.alchemy_snapshot, fictional_story())
        self.world_snapshot = scene_weave.freeze(self.root, self.seed["world_id"])
        self.choices = [{"beat": i, "role": role, "candidate": "wide"}
                        for i, role in enumerate(("source", "bridge", "target"))]

    def accept(self, selections=None):
        return scene_artifact.accept(self.root, self.world_snapshot, self.alchemy_snapshot,
                                     selections if selections is not None else self.choices,
                                     filmmaker_approval=True)

    def test_approval_and_real_source_alignment(self):
        with self.assertRaisesRegex(ValueError, "approval"):
            scene_artifact.accept(self.root, self.world_snapshot,
                                  self.alchemy_snapshot, self.choices)
        first = self.accept()
        second = self.accept()
        self.assertEqual(first, second)
        artifact, sha = scene_artifact.load(self.root, first["snapshot"])
        self.assertEqual(sha, first["sha256"])
        self.assertEqual([s["role"] for s in artifact["shots"]],
                         ["source", "bridge", "target"])
        self.assertEqual(artifact["distribution_authorized"], False)
        self.assertEqual(artifact["shots"][0]["known_to_audience"], ["sealed"])
        self.assertNotIn("sender", artifact["shots"][0]["known_to_audience"])
        film = scene_artifact._film(artifact, sha)
        self.assertEqual(film["schema"], project.SCHEMA)
        self.assertEqual(len(film["scenes"]), 3)

    def test_unsupported_camera_and_out_of_order_beats_refuse(self):
        variants = [
            [{"beat": 0, "role": "source", "candidate": "detail"}],
            [{"beat": 0, "role": "source", "candidate": "absence"}],
            [{"beat": 0, "role": "source", "candidate": "wide", "reveal": "sender"}],
            [{"beat": 2, "role": "source", "candidate": "wide"},
             {"beat": 0, "role": "target", "candidate": "wide"}],
            [{"beat": 0, "role": "source", "candidate": "wide"},
             {"beat": 0, "role": "target", "candidate": "wide"}],
        ]
        for choices in variants:
            with self.subTest(choices=choices):
                with self.assertRaises(ValueError):
                    self.accept(choices)

    def test_stale_world_and_source_refuse_without_altering_old_snapshots(self):
        accepted = self.accept()
        expected = self.world_snapshot.read_bytes()
        self.assertEqual(self.world_snapshot.read_bytes(), expected)
        self.world_snapshot.write_text('{"forged":"world"}')
        with self.assertRaises(ValueError):
            scene_artifact.load(self.root, accepted["snapshot"])
        self.world_snapshot.write_bytes(expected)
        self.assertIsNotNone(scene_artifact.load(self.root, accepted["snapshot"]))
        (self.photos / "water.png").write_bytes(b"source replaced")
        with self.assertRaisesRegex(ValueError, "Frozen source missing or changed"):
            scene_artifact.load(self.root, accepted["snapshot"])

    def test_tampered_artifact_and_changed_derivative_refuse(self):
        accepted = self.accept()
        path = Path(accepted["snapshot"])
        before = path.read_bytes()
        payload = json.loads(before)
        payload["shots"][0]["frame_sha256"] = "0" * 64
        path.write_text(json.dumps(payload))
        with self.assertRaisesRegex(ValueError, "hash"):
            scene_artifact.load(self.root, path)
        path.write_bytes(before)

        raw = self.photos / "camera.CR2"
        raw.write_bytes(b"synthetic RAW only")
        con = catalog.connect(self.root)
        try:
            raw_id, _ = catalog.index_file(con, raw)
            con.commit()
        finally:
            con.close()
        catalog.derivative(self.root, raw_id, self.photos / "cup.png")
        con = catalog.connect(self.root)
        try:
            # This does not modify the previously accepted photo relationships.
            other = catalog.source_for_render(con, raw_id)
        finally:
            con.close()
        self.assertEqual(other["id"], json.loads(before)["shots"][0]["frame_asset_id"])

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg unavailable")
    def test_actual_n0_render_and_independent_artifact_receipt(self):
        accepted = self.accept()
        output = self.root / "renders" / "three-beats.mp4"
        result = scene_artifact.render_accepted(self.root, accepted["snapshot"], output)
        self.assertTrue(output.is_file())
        self.assertEqual(result["shot_count"], 3)
        self.assertTrue(output.with_suffix(".mp4.receipt.json").is_file())
        witness_path = output.with_suffix(".mp4.scene-artifact.json")
        witness = json.loads(witness_path.read_text())
        self.assertEqual(witness["artifact_snapshot_sha256"], accepted["sha256"])
        self.assertEqual(witness["output_sha256"], catalog.digest_file(output))
        self.assertFalse(witness["distribution_authorized"])
        with self.assertRaisesRegex(ValueError, "overwrite"):
            scene_artifact.render_accepted(self.root, accepted["snapshot"], output)


if __name__ == "__main__":
    unittest.main()
