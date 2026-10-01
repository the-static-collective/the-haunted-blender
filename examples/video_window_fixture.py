"""Build one fully local synthetic filmmaker-accepted MP4 fixture for Video Window."""
from __future__ import annotations

import argparse
import json
import struct
import subprocess
import zlib
from pathlib import Path

from haunted_blender import alchemy, catalog, creative_take, scene_artifact, scene_weave


def png(path: Path, rgb):
    width, height = 48, 32
    pixels = (b"\x00" + bytes(rgb) * width) * height

    def chunk(kind, data):
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">2I5B", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(pixels))
        + chunk(b"IEND", b"")
    )


def story():
    by = scene_weave.AUTHOR
    return {
        "title": "Video Window Fixture",
        "entities": [
            {"id": "door", "kind": "prop", "name": "Door", "basis": by},
        ],
        "facts": [
            {"id": "closed", "subject": "door", "predicate": "state",
             "value": "closed", "since_beat": 0, "basis": by},
        ],
        "beats": [
            {"id": "arrival", "index": 0},
            {"id": "motion", "index": 1},
            {"id": "return", "index": 2},
        ],
        "knowledge": [
            {"id": "audience-sees", "observer": "audience",
             "fact_id": "closed", "since_beat": 0, "basis": by},
        ],
        "relations": [],
        "affordances": [],
        "questions": [],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    catalog.init(root)

    source_dir = root / "fixture-source"
    source_dir.mkdir(parents=True, exist_ok=True)
    for name, rgb in (
        ("source", (80, 120, 180)),
        ("bridge", (180, 100, 80)),
        ("target", (120, 180, 100)),
    ):
        png(source_dir / (name + ".png"), rgb)
    catalog.scan(root, source_dir)

    con = catalog.connect(root)
    try:
        ids = {
            Path(row["path"]).stem: row["id"]
            for row in con.execute("SELECT path,id FROM assets")
        }
    finally:
        con.close()

    recipe = alchemy.create(
        root,
        ids["source"],
        ids["target"],
        bridge=ids["bridge"],
        relation="triadic-bridge",
        statement="Synthetic Video Window fixture",
    )
    alchemy_snapshot = alchemy.freeze(root, recipe["id"])
    seed = scene_weave.from_alchemy(root, alchemy_snapshot, story())
    world_snapshot = scene_weave.freeze(root, seed["world_id"])

    accepted = scene_artifact.accept(
        root,
        world_snapshot,
        alchemy_snapshot,
        [
            {"beat": 0, "role": "source", "candidate": "wide"},
            {"beat": 1, "role": "bridge", "candidate": "wide"},
            {"beat": 2, "role": "target", "candidate": "wide"},
        ],
        filmmaker_approval=True,
    )

    request = creative_take.request(
        root,
        accepted["snapshot"],
        1,
        "Synthetic moving test pattern; no people.",
        synthetic_source=True,
        disclose_to_provider=True,
        duration=3,
    )

    source_video = source_dir / "candidate.mp4"
    subprocess.run(
        [
            "ffmpeg", "-nostdin", "-loglevel", "error",
            "-f", "lavfi", "-i", "testsrc2=s=320x180:r=24",
            "-t", "1", "-c:v", "mpeg4", str(source_video),
        ],
        check=True,
        timeout=60,
    )

    admitted = creative_take.admit(
        root,
        request["request"],
        source_video,
        provider_job_id="video-window-fixture-001",
    )
    accepted_take = creative_take.accept(
        root,
        request["request"],
        admitted["video"],
        filmmaker_approval=True,
    )

    print(json.dumps({
        "root": str(root),
        "address": "sha256:" + accepted_take["video_sha256"],
        "video_sha256": accepted_take["video_sha256"],
        "acceptance": accepted_take["acceptance"],
        "status": "filmmaker_accepted_private_preview",
        "distribution_authorized": False,
    }, indent=2))


if __name__ == "__main__":
    main()
