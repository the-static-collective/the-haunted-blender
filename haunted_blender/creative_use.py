"""Experimental additive lineage binding for distinct uses of identical media."""
from __future__ import annotations

import json
import re
from pathlib import Path

from . import catalog, creative_take, project, take_cut

SCHEMA = "haunted-blender/creative-use/v0"
COMPARISON_SCHEMA = "haunted-blender/creative-use-comparison/v0"


def _require(value, message):
    if not value:
        raise ValueError(message)


def _root(root):
    return Path(root).expanduser().resolve()


def _path(root, digest):
    return _root(root) / "snapshots" / "creative-uses" / (digest + ".json")


def _save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = project.stable_bytes(data) + b"\n"
    try:
        with path.open("xb") as handle:
            handle.write(payload)
    except FileExistsError:
        _require(path.read_bytes() == payload, "Existing use receipt changed")


def record(root, artifact_snapshot, acceptance_snapshot, *, role, intent):
    """Name one accepted placement; this does not assert that a cut was rendered."""
    _require(isinstance(role, str) and re.fullmatch(r"[a-z][a-z0-9-]{1,47}", role),
             "Role must be a short lowercase token")
    _require(isinstance(intent, str) and 1 <= len(intent.strip()) <= 500,
             "An explicit, bounded filmmaker intent is required")
    root = _root(root)
    artifact, artifact_sha, witness, request_sha, video = take_cut._accepted_take(
        root, artifact_snapshot, acceptance_snapshot)
    request_path = root / "snapshots" / "creative-takes" / (request_sha + ".json")
    request, _ = creative_take.load_request(root, request_path)
    body = {
        "schema": SCHEMA,
        "status": "accepted_placement_not_render_evidence",
        "material_sha256": witness["video_sha256"],
        "source_frame_sha256": request["frame_sha256"],
        "artifact_snapshot": str(Path(artifact_snapshot).expanduser().resolve(strict=True)),
        "artifact_sha256": artifact_sha, "artifact_id": artifact["id"],
        "beat": witness["beat"],
        "request_sha256": request_sha,
        "acceptance_snapshot": str(Path(acceptance_snapshot).expanduser().resolve(strict=True)),
        "acceptance_bytes_sha256": catalog.digest_file(Path(acceptance_snapshot)),
        "role": role, "intent": intent.strip(), "distribution_authorized": False,
        "nonclaims": ["Same media bytes can be used in different accepted contexts",
                      "An accepted placement is not proof that a cut was rendered",
                      "Intent is filmmaker-authored, not inferred from pixels",
                      "This use conveys no publication or story authority to other uses"],
    }
    # The placement, its context and an authored role identify the use, while
    # the material digest remains a *separate* shared byte identity.
    body["use_id"] = "use-" + creative_take._sha(body)[:20]
    digest = creative_take._sha(body)
    path = _path(root, digest)
    _save(path, body)
    return {"use": str(path), "use_sha256": digest, "use_id": body["use_id"],
            "material_sha256": body["material_sha256"]}


def load(root, use_snapshot):
    root = _root(root)
    path = Path(use_snapshot).expanduser().resolve(strict=True)
    body = json.loads(path.read_text(encoding="utf-8"))
    _require(body.get("schema") == SCHEMA and path == _path(root, creative_take._sha(body))
             and body.get("status") == "accepted_placement_not_render_evidence"
             and body.get("distribution_authorized") is False,
             "Use receipt has changed or is outside its private vault")
    artifact, artifact_sha, witness, request_sha, video = take_cut._accepted_take(
        root, body["artifact_snapshot"], body["acceptance_snapshot"])
    request, _ = creative_take.load_request(root, root / "snapshots" / "creative-takes" /
                                            (request_sha + ".json"))
    _require(body["material_sha256"] == witness["video_sha256"]
             and body["source_frame_sha256"] == request["frame_sha256"]
             and body["artifact_sha256"] == artifact_sha
             and body["artifact_id"] == artifact["id"]
             and body["beat"] == witness["beat"]
             and body["request_sha256"] == request_sha
             and body["acceptance_bytes_sha256"] == catalog.digest_file(
                 Path(body["acceptance_snapshot"]))
             and body["use_id"] == "use-" + creative_take._sha(
                 {k: v for k, v in body.items() if k != "use_id"})[:20]
             and catalog.digest_file(video) == body["material_sha256"],
             "Use receipt no longer matches source, acceptance or material")
    return body, creative_take._sha(body)


def compare(root, left_snapshot, right_snapshot):
    """Witness one same-byte/two-placement pair without granting inherited authority."""
    root = _root(root)
    left, left_sha = load(root, left_snapshot)
    right, right_sha = load(root, right_snapshot)
    _require(left_sha != right_sha and left["use_id"] != right["use_id"],
             "Two distinct use receipts are required")
    _require(left["material_sha256"] == right["material_sha256"],
             "Compared uses must contain identical media bytes")
    _require(left["source_frame_sha256"] == right["source_frame_sha256"],
             "Identical media must retain the same accepted source frame")
    _require((left["artifact_sha256"], left["beat"]) !=
             (right["artifact_sha256"], right["beat"]),
             "Different roles alone do not create distinct scene placements")
    _require(left["acceptance_bytes_sha256"] != right["acceptance_bytes_sha256"],
             "Each placement needs its own acceptance")
    pair = {
        "schema": COMPARISON_SCHEMA, "status": "scoped_complete",
        "material_sha256": left["material_sha256"],
        "source_frame_sha256": left["source_frame_sha256"],
        "uses": [{"use_id": item["use_id"], "use_sha256": sha,
                  "artifact_sha256": item["artifact_sha256"], "beat": item["beat"],
                  "acceptance_bytes_sha256": item["acceptance_bytes_sha256"]}
                 for item, sha in ((left, left_sha), (right, right_sha))],
        "proved": ["Same media byte digest in two independently accepted placements",
                   "Each placement has a distinct use and acceptance identity",
                   "Both source chains were revalidated at comparison time"],
        "nonclaims": ["The identical bytes do not carry narrative meaning across uses",
                      "The two placements need not have rendered output",
                      "The reported provider job is not independently verified",
                      "This is not permission to publish or recursively reimport media"],
        "distribution_authorized": False,
    }
    digest = creative_take._sha(pair)
    path = root / "snapshots" / "creative-use-comparisons" / (digest + ".json")
    _save(path, pair)
    return {"comparison": str(path), "comparison_sha256": digest,
            "material_sha256": pair["material_sha256"],
            "use_ids": [u["use_id"] for u in pair["uses"]]}
