"""Experimental, additive Creative Claw take bridge for an accepted Scene Artifact.

This module never calls a provider or grants publication rights. The upload and
generation are explicit external steps; admission attests local bytes only.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

from . import catalog, project, scene_artifact

REQUEST_SCHEMA = "haunted-blender/creative-claw-take-request/v0"
RECEIPT_SCHEMA = "haunted-blender/creative-claw-take-receipt/v0"
MODEL = "video/gemini-omni-flash"


def _require(value, message):
    if not value:
        raise ValueError(message)


def _sha(value):
    return hashlib.sha256(project.stable_bytes(value)).hexdigest()


def _root(root):
    return Path(root).expanduser().resolve()


def _save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = project.stable_bytes(value) + b"\n"
    try:
        with path.open("xb") as handle:
            handle.write(payload)
    except FileExistsError:
        _require(path.read_bytes() == payload, "Existing take witness changed")


def _request_path(root, digest):
    return _root(root) / "snapshots" / "creative-takes" / (digest + ".json")


def _shot(root, artifact_snapshot, beat):
    artifact, digest = scene_artifact.load(root, artifact_snapshot)
    _require(type(beat) is int, "Beat must be an integer")
    matches = [shot for shot in artifact["shots"] if shot["beat"] == beat]
    _require(len(matches) == 1, "Beat is not an accepted shot")
    return artifact, digest, matches[0]


def request(root, artifact_snapshot, beat, prompt, *, synthetic_source=False,
            disclose_to_provider=False, duration=3):
    """Freeze a specific approved synthetic still and generation instruction.

    An accepted local preview does not authorize a remote disclosure; both
    independent assertions are mandatory in this first experiment.
    """
    _require(synthetic_source is True and disclose_to_provider is True,
             "Synthetic source and explicit Creative Claw disclosure approval required")
    _require(isinstance(prompt, str) and 1 <= len(prompt.strip()) <= 1800,
             "Provide a bounded nonempty creative prompt")
    _require(type(duration) is int and 3 <= duration <= 10, "Duration must be 3–10 seconds")
    root = _root(root)
    artifact, digest, shot = _shot(root, artifact_snapshot, beat)
    con = catalog.connect(root)
    try:
        row = con.execute("SELECT path,sha256 FROM assets WHERE id=?",
                          (shot["frame_asset_id"],)).fetchone()
        _require(row is not None and row["sha256"] == shot["frame_sha256"],
                 "Accepted frame is missing or changed")
        frame = Path(row["path"])
        _require(frame.is_file() and catalog.digest_file(frame) == shot["frame_sha256"],
                 "Accepted frame bytes changed")
    finally:
        con.close()
    body = {
        "schema": REQUEST_SCHEMA, "provider": "Creative Claw", "model": MODEL,
        "artifact_snapshot": str(Path(artifact_snapshot).expanduser().resolve(strict=True)),
        "artifact_sha256": digest, "artifact_id": artifact["id"],
        "beat": beat, "beat_id": shot["beat_id"],
        "frame_asset_id": shot["frame_asset_id"], "frame_sha256": shot["frame_sha256"],
        "prompt": prompt.strip(), "duration_seconds": duration,
        "source_assertion": "operator_asserted_synthetic",
        "disclosure_scope": "one approved still image and prompt to Creative Claw",
        "distribution_authorized": False,
        "status": "approved_remote_preview_request_not_executed",
        "nonclaims": ["A request is not a completed generation",
                      "Synthetic source is an operator assertion, not pixel recognition",
                      "Motion does not establish a real depicted event or character identity"],
    }
    digest = _sha(body)
    path = _request_path(root, digest)
    _save(path, body)
    return {"request": str(path), "request_sha256": digest, "frame": str(frame),
            "frame_sha256": shot["frame_sha256"], "model": MODEL,
            "prompt": body["prompt"], "duration_seconds": duration}


def load_request(root, request_path):
    path = Path(request_path).expanduser().resolve(strict=True)
    body = json.loads(path.read_text(encoding="utf-8"))
    _require(body.get("schema") == REQUEST_SCHEMA and path == _request_path(root, _sha(body)),
             "Take request identity or schema changed")
    artifact, digest, shot = _shot(root, body["artifact_snapshot"], body["beat"])
    _require(body["artifact_sha256"] == digest and body["artifact_id"] == artifact["id"]
             and body["frame_asset_id"] == shot["frame_asset_id"]
             and body["frame_sha256"] == shot["frame_sha256"]
             and body["beat_id"] == shot["beat_id"]
             and body["model"] == MODEL and body["source_assertion"] == "operator_asserted_synthetic"
             and body["distribution_authorized"] is False,
             "Take request no longer matches accepted source and scope")
    return body, _sha(body)


def admit(root, request_path, video, *, provider_job_id):
    """Copy one completed clip into the private vault; never pretend to verify provider execution."""
    root = _root(root)
    body, digest = load_request(root, request_path)
    _require(isinstance(provider_job_id, str) and re.fullmatch(r"[A-Za-z0-9_-]{6,128}", provider_job_id),
             "Provider job ID must be supplied from the completed generation")
    supplied = Path(video).expanduser()
    _require(not supplied.is_symlink(), "Symlink videos are not admitted")
    source = supplied.resolve(strict=True)
    _require(source.is_file() and source.suffix.lower() == ".mp4", "Expected completed MP4")
    probe = shutil.which("ffprobe")
    _require(probe is not None, "ffprobe required to verify video stream")
    check = subprocess.run([probe, "-v", "error", "-select_streams", "v:0",
                            "-show_entries", "stream=codec_type", "-of", "csv=p=0",
                            str(source)], capture_output=True, text=True, timeout=20, check=True)
    _require(check.stdout.strip() == "video", "MP4 has no usable video stream")
    video_sha = catalog.digest_file(source)
    folder = root / "renders" / "creative-takes"
    target = folder / (digest + "-" + video_sha + ".mp4")
    receipt_path = target.with_suffix(".mp4.receipt.json")
    _require(not target.exists() and not receipt_path.exists(), "Refusing to overwrite a take or receipt")
    folder.mkdir(parents=True, exist_ok=True)
    try:
        with source.open("rb") as src, target.open("xb") as dst:
            shutil.copyfileobj(src, dst)
        _require(catalog.digest_file(target) == video_sha, "Video changed during private admission")
        receipt = {
            "schema": RECEIPT_SCHEMA, "status": "candidate_admitted_not_filmmaker_accepted",
            "request_sha256": digest, "artifact_sha256": body["artifact_sha256"],
            "beat": body["beat"], "frame_sha256": body["frame_sha256"],
            "provider": body["provider"], "model": body["model"],
            "provider_job_id_reported": provider_job_id,
            "provider_execution_independently_verified": False,
            "output_sha256": video_sha, "distribution_authorized": False,
            "nonclaims": ["Admission checks local video bytes, not provider job authenticity",
                          "Generated motion is not a witnessed real-world event",
                          "Filmmaker has not accepted this candidate as a scene take"],
        }
        _save(receipt_path, receipt)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    return {"video": str(target), "receipt": str(receipt_path),
            "output_sha256": video_sha, "status": receipt["status"]}


def accept(root, request_path, video, *, filmmaker_approval=False):
    """Bind an admitted local candidate to this shot, without changing the Scene Artifact."""
    _require(filmmaker_approval is True, "Explicit filmmaker acceptance required")
    body, digest = load_request(root, request_path)
    path = Path(video).expanduser().resolve(strict=True)
    receipt_path = path.with_suffix(".mp4.receipt.json")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    _require(receipt.get("schema") == RECEIPT_SCHEMA
             and receipt.get("status") == "candidate_admitted_not_filmmaker_accepted"
             and receipt.get("request_sha256") == digest
             and receipt.get("output_sha256") == catalog.digest_file(path)
             and receipt.get("artifact_sha256") == body["artifact_sha256"]
             and receipt.get("beat") == body["beat"]
             and path == _root(root) / "renders" / "creative-takes" /
             (digest + "-" + receipt["output_sha256"] + ".mp4"),
             "Admitted take bytes or lineage changed")
    witness = {
        "schema": "haunted-blender/accepted-creative-take/v0",
        "request_sha256": digest, "admission_receipt_sha256": catalog.digest_file(receipt_path),
        "artifact_sha256": body["artifact_sha256"], "beat": body["beat"],
        "video_sha256": receipt["output_sha256"], "status": "filmmaker_accepted_private_preview",
        "distribution_authorized": False,
        "nonclaims": ["Acceptance is not a release or publication authorization",
                      "This take does not replace N0's film snapshot or renderer"],
    }
    dest = _root(root) / "snapshots" / "creative-take-acceptances" / (_sha(witness) + ".json")
    _save(dest, witness)
    return {"acceptance": str(dest), "video": str(path), "video_sha256": receipt["output_sha256"]}
