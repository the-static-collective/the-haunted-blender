"""Experimental two-cut comparison over separately accepted Scene Artifacts.

The compared worlds share authored events and source media. Their audience
knowledge cuts are explicit filmmaker assertions, not observations from video.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from . import catalog, project, scene_artifact, scene_weave

SCHEMA = "haunted-blender/counterfactual-pair/v0"
RECEIPT = "haunted-blender/counterfactual-pair-receipt/v0"
CORE = ("mode", "title", "material", "entities", "facts", "beats",
        "relations", "affordances", "questions")


def _root(root):
    return Path(root).expanduser().resolve()


def _digest(data):
    return hashlib.sha256(project.stable_bytes(data)).hexdigest()


def _prepare(root, first, second):
    cuts = []
    worlds = []
    for snapshot in (first, second):
        artifact, digest = scene_artifact.load(root, snapshot)
        world = scene_weave.load_snapshot(root, artifact["world_snapshot"])
        cuts.append({"artifact_snapshot": str(Path(snapshot).expanduser().resolve()),
                     "artifact_sha256": digest, "world_sha256": artifact["world_sha256"],
                     "artifact_id": artifact["id"], "shots": artifact["shots"]})
        worlds.append(world)
    a, b = cuts
    if a["artifact_sha256"] == b["artifact_sha256"]:
        raise ValueError("Two distinct accepted Scene Artifacts are required")
    if any(worlds[0][key] != worlds[1][key] for key in CORE):
        raise ValueError("The cuts must share the same authored events and source material")
    def character_knowledge(world):
        return [row for row in world["knowledge"] if row["observer"] != "audience"]
    if character_knowledge(worlds[0]) != character_knowledge(worlds[1]):
        raise ValueError("Character knowledge must remain identical across cuts")
    if [s["beat"] for s in a["shots"]] != [s["beat"] for s in b["shots"]]:
        raise ValueError("Cuts must select the same story beats")
    if Counter(s["frame_asset_id"] for s in a["shots"]) != Counter(
            s["frame_asset_id"] for s in b["shots"]):
        raise ValueError("Cuts must use the same source image multiset")
    if [s["frame_asset_id"] for s in a["shots"]] == [s["frame_asset_id"] for s in b["shots"]]:
        raise ValueError("The cuts need visibly different image orders")
    differences = []
    for left, right in zip(a["shots"], b["shots"]):
        if left["known_to_audience"] != right["known_to_audience"]:
            differences.append({"beat": left["beat"], "beat_id": left["beat_id"],
                                "cut_a_known": left["known_to_audience"],
                                "cut_b_known": right["known_to_audience"]})
    if not differences:
        raise ValueError("Selected beats need a different authored audience knowledge cut")
    return {"schema": SCHEMA, "status": "accepted_local_preview",
            "source_alchemy_sha256": worlds[0]["material"]["alchemy_snapshot_sha256"],
            "cuts": cuts, "knowledge_differences": differences,
            "distribution_authorized": False,
            "nonclaims": ["A still image does not demonstrate that a viewer learned a fact",
                          "Knowledge is filmmaker-authored in each SceneWorld, not inferred from a photograph",
                          "No depicted fictional event or real identity is established by either render"]}


def accept(root, first, second, *, filmmaker_approval=False):
    if filmmaker_approval is not True:
        raise ValueError("Explicit filmmaker approval of the two-cut comparison required")
    pair = _prepare(root, first, second)
    digest = _digest(pair)
    path = _root(root) / "snapshots" / "counterfactual" / (digest + ".json")
    path.parent.mkdir(parents=True, exist_ok=True)
    expected = project.stable_bytes(pair) + b"\n"
    try:
        with path.open("xb") as handle:
            handle.write(expected)
    except FileExistsError:
        if path.read_bytes() != expected:
            raise ValueError("Frozen counterfactual pair changed")
    return {"snapshot": str(path), "sha256": digest,
            "knowledge_differences": pair["knowledge_differences"]}


def load(root, snapshot):
    path = Path(snapshot).expanduser().resolve(strict=True)
    if path.parent != _root(root) / "snapshots" / "counterfactual":
        raise ValueError("Pair snapshot is outside the private vault")
    pair = json.loads(path.read_text(encoding="utf-8"))
    if pair.get("schema") != SCHEMA or pair.get("distribution_authorized") is not False:
        raise ValueError("Unknown pair schema or publication scope")
    if path.name != _digest(pair) + ".json":
        raise ValueError("Pair snapshot hash mismatch")
    fresh = _prepare(root, *(cut["artifact_snapshot"] for cut in pair["cuts"]))
    if fresh != pair:
        raise ValueError("Pair source, world or accepted cut changed")
    return pair, _digest(pair)


def render_pair(root, snapshot, out_a, out_b):
    pair, digest = load(root, snapshot)
    outputs = [Path(p).expanduser().resolve() for p in (out_a, out_b)]
    if outputs[0] == outputs[1] or any(p.suffix.lower() != ".mp4" for p in outputs):
        raise ValueError("Provide two distinct local MP4 output paths")
    pair_receipt = outputs[0].with_suffix(".mp4.counterfactual-pair.json")
    if pair_receipt in outputs:
        raise ValueError("Pair receipt path collides with a video output")
    for out in outputs:
        companions = (out, out.with_suffix(".mp4.receipt.json"),
                      out.with_suffix(".mp4.scene-artifact.json"))
        if any(path.exists() for path in companions):
            raise FileExistsError("A cut output or receipt already exists")
    if pair_receipt.exists():
        raise FileExistsError("Pair receipt already exists")
    rendered = []
    for cut, out in zip(pair["cuts"], outputs):
        result = scene_artifact.render_accepted(root, cut["artifact_snapshot"], out)
        rendered.append({"artifact_sha256": cut["artifact_sha256"],
                         "output_path": result["output"], "output_sha256": result["output_sha256"],
                         "n0_receipt_sha256": catalog.digest_file(out.with_suffix(".mp4.receipt.json")),
                         "artifact_receipt_sha256": catalog.digest_file(out.with_suffix(".mp4.scene-artifact.json"))})
    receipt = {"schema": RECEIPT, "status": "scoped_complete", "pair_sha256": digest,
               "cuts": rendered, "knowledge_differences": pair["knowledge_differences"],
               "distribution_authorized": False, "nonclaims": pair["nonclaims"]}
    with pair_receipt.open("xb") as handle:
        handle.write(project.stable_bytes(receipt) + b"\n")
    return {"receipt": str(pair_receipt), "pair_sha256": digest, "cuts": rendered}
