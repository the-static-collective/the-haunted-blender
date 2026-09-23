"""ORCHARD-002: exercise pinned Observer Vision + Memory Feedback on synthetic frames.

This is a separate *experiment*, not the CHRONOBODY resolver's execution path.
A single frozen Memory Feedback checkout contains its inherited Observer Vision
code. Before import, compare that inherited code to the independently pinned
Observer Vision checkout and validate both Git commit / source-blob identities.
No branch lookup, provider, filesystem mutation inside organ checkouts, personal
media, publication, or automatic promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import subprocess
import sys
from pathlib import Path

OBSERVER_SHA = "9beec9cce02f9c595386fc39fd7fb79a890434da"
MEMORY_SHA = "6aca64fdeeb458653e20558c4b23fa89ec622ba7"
OBSERVER_BLOB = "38447bf4c9e68be8b655ed32da16a14d0012689b"
MEMORY_BLOB = "833cc9c2a4d770bee566c2bbfa63fe9e0864e92a"
SCHEMA = "haunted-blender/orchard-crossing-receipt/v0"

WORLD = {
    "id": "orchard-synthetic-room-001",
    "beats": [{"id": "one", "index": 0}],
    "facts": [
        {"id": "room", "since_beat": 0},
        {"id": "figure", "since_beat": 0},
    ],
}
REGION = {"figure": [0.20, 0.20, 0.34, 0.40]}
THRESHOLD = {
    "id": "eye-threshold",
    "position": "threshold",
    "access_fact_ids": ["room"],
    "focus_fact_ids": ["figure"],
    "threshold_rules": [
        {"threshold_id": "door", "fact_id": "figure", "min_open": 0.4}
    ],
}
HALLWAY = {
    "id": "eye-hallway",
    "position": "hallway",
    "access_fact_ids": ["room"],
    "focus_fact_ids": [],
    "threshold_rules": [
        {"threshold_id": "door", "fact_id": "figure", "min_open": 0.8}
    ],
}


class CrossingRefusal(ValueError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable(data: object) -> bytes:
    return json.dumps(
        data, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CrossingRefusal(message)


def git(root: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=check,
        timeout=20,
    )
    return result.stdout.strip()


def verify_sources(observer_checkout: Path, memory_checkout: Path) -> dict:
    observer_checkout = observer_checkout.resolve(strict=True)
    memory_checkout = memory_checkout.resolve(strict=True)
    require(observer_checkout != memory_checkout, "Observer and memory inputs must be separate checkouts")
    expected = (
        (observer_checkout, OBSERVER_SHA, "haunted_blender/observer_local.py", OBSERVER_BLOB),
        (memory_checkout, MEMORY_SHA, "haunted_blender/observer_local.py", OBSERVER_BLOB),
        (memory_checkout, MEMORY_SHA, "haunted_blender/memory_feedback.py", MEMORY_BLOB),
    )
    for root, sha, path, blob in expected:
        require((root / ".git").exists(), "Source is not an explicit Git checkout")
        require(git(root, "rev-parse", "HEAD") == sha, "Pinned checkout commit mismatch")
        source = (root / path).resolve(strict=True)
        require(source.is_relative_to(root), "Source path escapes checkout")
        require(git(root, "rev-parse", "HEAD:" + path) == blob,
                "Pinned source blob differs from reviewed source")
        require(git(root, "hash-object", path) == blob,
                "Materialized source bytes differ from pinned source blob")
        require(not git(root, "status", "--porcelain", "--untracked-files=all"),
                "Pinned checkout is not clean")
    require(
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", OBSERVER_SHA, MEMORY_SHA],
            cwd=memory_checkout, capture_output=True, check=False, timeout=20,
        ).returncode == 0,
        "Memory commit does not contain pinned observer commit in its ancestry",
    )
    # Equal code, inherited through a *single* memory checkout. We do NOT import
    # two haunted_blender packages from overlapping stacked branches.
    return {
        "observer_commit": OBSERVER_SHA,
        "memory_commit": MEMORY_SHA,
        "observer_blob": OBSERVER_BLOB,
        "memory_blob": MEMORY_BLOB,
        "source_mode": "one_stacked_checkout_verified_against_two_exact_commits",
    }


def import_pinned_memory_stack(checkout: Path):
    root = checkout.resolve(strict=True)
    sys.path.insert(0, str(root))
    try:
        observer = importlib.import_module("haunted_blender.observer_local")
        memory = importlib.import_module("haunted_blender.memory_feedback")
        for module in (observer, memory):
            require(Path(module.__file__).resolve().is_relative_to(root),
                    "Unpinned organ module imported")
        return observer, memory
    finally:
        sys.path.remove(str(root))


def draw_synthetic_frames(memory, visible: bool) -> bytes:
    """This is a *fabricated test frame*, never an accepted moving take."""
    size = memory.WIDTH * memory.HEIGHT * 3
    black = bytes(size)
    first = bytearray(size)
    if visible:
        x0, y0, x1, y1 = memory._normalize_regions(REGION)["figure"]["pixels"]
        for y in range(y0, y1):
            for x in range(x0, x1):
                p = (y * memory.WIDTH + x) * 3
                first[p:p+3] = bytes((160, 110, 230))
    return bytes(first) * 2 + black * 2


def timeline(first: dict, second: dict) -> list[dict]:
    return [
        {"start_frame": 0, "end_frame_exclusive": 2, "projection": first},
        {"start_frame": 2, "end_frame_exclusive": 4, "projection": second},
    ]


def run_crossing(observer, memory, source_identity: dict) -> dict:
    frozen_world = stable(WORLD)
    world_digest = digest(frozen_world)

    threshold_first = observer.project(WORLD, 0, THRESHOLD, {"door": 0.6})
    hallway_first = observer.project(WORLD, 0, HALLWAY, {"door": 0.6})
    threshold_second = observer.project(
        WORLD, 0, THRESHOLD, {"door": 0.1},
        threshold_first["memory_receipt"],
    )
    hallway_second = observer.project(
        WORLD, 0, HALLWAY, {"door": 0.1},
        hallway_first["memory_receipt"],
    )

    require(world_digest == digest(stable(WORLD)), "Scene changed during projection")
    projections = (
        threshold_first, hallway_first, threshold_second, hallway_second
    )
    require(
        all(p["world_sha256"] == world_digest for p in projections),
        "Two cameras did not share the exact frozen world",
    )
    require(
        "figure" in threshold_first["visible_fact_ids"]
        and "figure" not in hallway_first["visible_fact_ids"],
        "Two cameras failed the distinct access test",
    )
    require(
        "figure" not in threshold_second["visible_fact_ids"]
        and {"fact_id": "figure", "mode": "memory_residue"}
        in threshold_second["environment_response"]
        and "figure" not in hallway_second["memory_receipt"]["memory_fact_ids"],
        "Later presentations did not preserve observer-local memory",
    )
    require(
        threshold_first["projection_sha256"] != hallway_first["projection_sha256"],
        "Different cameras produced identical projection identities",
    )

    threshold_compiled = memory._compile_timeline(
        4, timeline(threshold_first, threshold_second), REGION,
    )
    hallway_compiled = memory._compile_timeline(
        4, timeline(hallway_first, hallway_second), REGION,
    )
    threshold_source = draw_synthetic_frames(memory, visible=True)
    hallway_source = draw_synthetic_frames(memory, visible=False)
    threshold_output, threshold_stats = memory._memory_frames(
        threshold_source, threshold_compiled
    )
    hallway_output, hallway_stats = memory._memory_frames(
        hallway_source, hallway_compiled
    )
    frame_size = memory.WIDTH * memory.HEIGHT * 3
    afterimage_first = sum(threshold_output[2*frame_size:3*frame_size])
    afterimage_last = sum(threshold_output[3*frame_size:4*frame_size])
    require(
        afterimage_first > afterimage_last > 0,
        "Previously observed pixels failed to fade after occlusion",
    )
    require(
        hallway_output == hallway_source
        and hallway_stats["figure"]["captured_frames"] == 0
        and hallway_stats["figure"]["residue_frames"] == 0,
        "Never-seen figure generated a false visual memory",
    )
    require(
        threshold_stats["figure"]["captured_frames"] == 2
        and threshold_stats["figure"]["residue_frames"] == 2,
        "Visual memory did not use on-timeline capture",
    )
    require(world_digest == digest(stable(WORLD)),
            "Scene changed during pixel composition")

    hostile = []

    def rejects(name: str, callback, expected: str):
        try:
            callback()
        except ValueError as exc:
            require(expected in str(exc), name + " refused for wrong reason: " + str(exc))
            hostile.append(name)
            return
        raise CrossingRefusal(name + " was not refused")

    rejects(
        "cross_observer_receipt",
        lambda: observer.project(
            WORLD, 0, HALLWAY, {"door": 0.1},
            threshold_first["memory_receipt"],
        ),
        "another observer",
    )
    altered_world = json.loads(frozen_world)
    altered_world["facts"].append({"id": "invented", "since_beat": 0})
    rejects(
        "altered_world_receipt",
        lambda: observer.project(
            altered_world, 0, THRESHOLD, {"door": 0.1},
            threshold_first["memory_receipt"],
        ),
        "another world",
    )
    forged = json.loads(json.dumps(threshold_first))
    forged["visible_fact_ids"].remove("figure")
    rejects(
        "tampered_projection",
        lambda: memory._compile_timeline(
            4, timeline(forged, threshold_second), REGION,
        ),
        "digest mismatch",
    )
    rejects(
        "memory_without_on_timeline_capture",
        lambda: memory._memory_frames(
            bytes(frame_size * 4),
            memory._compile_timeline(
                4, [{"start_frame": 0, "end_frame_exclusive": 4,
                     "projection": threshold_second}],
                REGION,
            ),
        ),
        "no on-timeline visual capture",
    )
    # A receipt is evidence of test execution, not scene or media authority.
    receipt = {
        "schema": SCHEMA,
        "status": "SCOPED_PROOF",
        "experiment": "observer_projection_to_synthetic_pixel_memory",
        "source_identity": source_identity,
        "frozen_world_sha256": world_digest,
        "world_unchanged": world_digest == digest(stable(WORLD)),
        "camera_projections": {
            "threshold": [
                threshold_first["projection_sha256"],
                threshold_second["projection_sha256"],
            ],
            "hallway": [
                hallway_first["projection_sha256"],
                hallway_second["projection_sha256"],
            ],
        },
        "synthetic_frame_inputs": {
            "threshold_sha256": digest(threshold_source),
            "hallway_sha256": digest(hallway_source),
        },
        "synthetic_frame_outputs": {
            "threshold_sha256": digest(threshold_output),
            "hallway_sha256": digest(hallway_output),
            "different": digest(threshold_output) != digest(hallway_output),
        },
        "threshold_memory_stats": threshold_stats["figure"],
        "hallway_memory_stats": hallway_stats["figure"],
        "hostile_refusals": hostile,
        "unverified_gates": [
            "PRODUCTION_ADAPTER_API",
            "ACCEPTED_MOVING_TAKE",
            "REAL_VIDEO_RENDER_AND_OUTPUT_RECEIPT",
            "PIXEL_VISIBILITY_ACTUAL_CAMERA_CAPTURE",
            "SOURCE_MEDIA_RIGHTS_AND_SCENE_APPROVAL",
        ],
        "nonclaims": [
            "Only actual pinned source functions were executed on fabricated RGB frames",
            "No accepted moving take, video render, photoreal door geometry, or scene integration was tested",
            "Camera-local projection and drawn test pixels are authored fixtures, not a physical optical simulation",
            "Same-world projection does not imply shared camera history or audience knowledge",
            "A scoped test receipt is not creative acceptance, canon, publication rights, or a branch promotion",
        ],
    }
    receipt["receipt_sha256"] = digest(stable(receipt))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prove a bounded Observer Vision x Memory Feedback crossing"
    )
    parser.add_argument("--observer-checkout", required=True, type=Path)
    parser.add_argument("--memory-checkout", required=True, type=Path)
    parser.add_argument("--receipt-out", type=Path)
    args = parser.parse_args()
    try:
        identity = verify_sources(
            args.observer_checkout, args.memory_checkout
        )
        observer, memory = import_pinned_memory_stack(args.memory_checkout)
        result = run_crossing(observer, memory, identity)
        for root in (args.observer_checkout, args.memory_checkout):
            require(
                not git(root.resolve(), "status", "--porcelain", "--untracked-files=all"),
                "Experiment mutated a pinned organ checkout",
            )
    except (CrossingRefusal, ValueError, OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "REFUSE", "reason": str(exc)}, sort_keys=True))
        return 2
    data = stable(result) + b"\n"
    if args.receipt_out:
        target = args.receipt_out.resolve()
        require(not target.exists(), "Refusing to overwrite crossing receipt")
        for root in (args.observer_checkout, args.memory_checkout):
            require(not target.is_relative_to(root.resolve()),
                    "Refusing to write a receipt inside an organ checkout")
        with target.open("xb") as handle:
            handle.write(data)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
