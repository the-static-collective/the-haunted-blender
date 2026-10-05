"""FRANKEN BLENDER 006 — provider-agnostic motion organ router.

The durable contract is local:
  awakening request -> current provider offers -> deterministic route plan
  -> externally executed candidate -> local admission -> explicit filmmaker KEEP.

Provider APIs, pricing, credits and availability remain runtime facts supplied as
offer snapshots. Blender never treats a provider as editorial authority.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

from . import catalog, project

REQUEST_SCHEMA = "haunted-blender/motion-organ-request/v1"
OFFERS_SCHEMA = "haunted-blender/motion-provider-offers/v1"
ROUTE_SCHEMA = "haunted-blender/motion-route-plan/v1"
CANDIDATE_RECEIPT_SCHEMA = "haunted-blender/motion-candidate-receipt/v1"
ACCEPTANCE_SCHEMA = "haunted-blender/accepted-motion-organ/v1"
BOARD_SCHEMA = "haunted-blender/motion-candidate-board/v1"

_SPEND_ORDER = {"free": 0, "included": 1, "paid": 2}


def _canonical(value: object) -> bytes:
    return project.stable_bytes(value)


def _sha(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _root(root) -> Path:
    return Path(root).expanduser().resolve()


def _save(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _canonical(value) + b"\n"
    try:
        with path.open("xb") as handle:
            handle.write(payload)
    except FileExistsError:
        if path.read_bytes() != payload:
            raise ValueError("Existing motion-organ witness changed")


def _request_path(root: Path, digest: str) -> Path:
    return root / "snapshots" / "motion-organ-requests" / f"{digest}.json"


def _offer_path(root: Path, digest: str) -> Path:
    return root / "snapshots" / "motion-provider-offers" / f"{digest}.json"


def _route_path(root: Path, digest: str) -> Path:
    return root / "snapshots" / "motion-route-plans" / f"{digest}.json"


def _candidate_folder(root: Path) -> Path:
    return root / "renders" / "motion-organ-candidates"


def _acceptance_path(root: Path, digest: str) -> Path:
    return root / "snapshots" / "motion-organ-acceptances" / f"{digest}.json"


def _nonnull_string(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")
    return value.strip()


def freeze_request(
    root,
    *,
    scene_id: str,
    scene_sha256: str,
    window_id: str,
    start_seconds: float,
    duration_seconds: float,
    prompt: str,
    source_address: str,
    input_mode: str = "image-to-video",
    aspect_ratio: str = "16:9",
    source_assertion: str = "operator_asserted_synthetic",
    remote_disclosure_approved: bool = False,
) -> dict:
    root = _root(root)
    if remote_disclosure_approved is not True:
        raise ValueError("Explicit remote disclosure approval is required")
    scene_id = _nonnull_string(scene_id, "scene_id")
    window_id = _nonnull_string(window_id, "window_id")
    prompt = _nonnull_string(prompt, "prompt")
    source_address = _nonnull_string(source_address, "source_address")
    if not re.fullmatch(r"[a-f0-9]{64}", str(scene_sha256)):
        raise ValueError("scene_sha256 must be lowercase SHA-256")
    start_seconds = float(start_seconds)
    duration_seconds = float(duration_seconds)
    if start_seconds < 0 or not (0.5 <= duration_seconds <= 30):
        raise ValueError("Motion request timing is outside supported bounds")
    if input_mode not in {"image-to-video", "text-to-video", "video-to-video"}:
        raise ValueError("Unsupported motion input mode")
    if aspect_ratio not in {"16:9", "9:16", "1:1", "4:3", "3:4"}:
        raise ValueError("Unsupported aspect ratio")
    if source_assertion not in {"operator_asserted_synthetic", "operator_asserted_owned_or_permitted"}:
        raise ValueError("Explicit source assertion is required")

    body = {
        "schema": REQUEST_SCHEMA,
        "sceneId": scene_id,
        "sceneSha256": scene_sha256,
        "windowId": window_id,
        "startSeconds": round(start_seconds, 6),
        "durationSeconds": round(duration_seconds, 6),
        "prompt": prompt,
        "sourceAddress": source_address,
        "inputMode": input_mode,
        "aspectRatio": aspect_ratio,
        "sourceAssertion": source_assertion,
        "remoteDisclosureApproved": True,
        "distributionAuthorized": False,
        "status": "portable-motion-request-not-executed",
        "laws": [
            "REQUEST != GENERATION",
            "ROUTE != PROVIDER AUTHORITY",
            "REMOTE DISCLOSURE REQUIRES EXPLICIT APPROVAL",
            "CANDIDATE MOTION != ACCEPTED TAKE",
        ],
    }
    digest = _sha(body)
    path = _request_path(root, digest)
    _save(path, body)
    return {"request": str(path), "requestSha256": digest, "requestBody": body}


def load_request(root, request_path):
    root = _root(root)
    path = Path(request_path).expanduser().resolve(strict=True)
    body = json.loads(path.read_text(encoding="utf-8"))
    if body.get("schema") != REQUEST_SCHEMA:
        raise ValueError("Unsupported motion-organ request")
    digest = _sha(body)
    if path != _request_path(root, digest):
        raise ValueError("Motion-organ request identity changed")
    if body.get("remoteDisclosureApproved") is not True or body.get("distributionAuthorized") is not False:
        raise ValueError("Motion-organ disclosure/release boundary changed")
    return body, digest


def freeze_offers(root, offers: dict) -> dict:
    root = _root(root)
    if not isinstance(offers, dict) or offers.get("schema") != OFFERS_SCHEMA:
        raise ValueError("Expected motion-provider-offers/v1")
    observed_at = _nonnull_string(offers.get("observedAt"), "observedAt")
    raw = offers.get("offers")
    if not isinstance(raw, list) or not raw:
        raise ValueError("At least one provider offer is required")

    normalized = []
    ids = set()
    for offer in raw:
        if not isinstance(offer, dict):
            raise ValueError("Provider offer must be an object")
        offer_id = _nonnull_string(offer.get("offerId"), "offerId")
        if offer_id in ids:
            raise ValueError("Provider offer ids must be unique")
        ids.add(offer_id)
        provider = _nonnull_string(offer.get("providerId"), "providerId")
        spend = offer.get("spendClass")
        if spend not in _SPEND_ORDER:
            raise ValueError("spendClass must be free, included, or paid")
        modes = sorted(set(offer.get("inputModes") or []))
        ratios = sorted(set(offer.get("aspectRatios") or []))
        min_s = float(offer.get("minSeconds", 0))
        max_s = float(offer.get("maxSeconds", 0))
        if min_s < 0 or max_s < min_s:
            raise ValueError("Provider duration bounds are invalid")
        available = bool(offer.get("available"))
        cost_micros = offer.get("estimatedUsdMicros")
        if cost_micros is not None:
            cost_micros = int(cost_micros)
            if cost_micros < 0:
                raise ValueError("estimatedUsdMicros must be nonnegative")
        if spend == "paid" and available and cost_micros is None:
            raise ValueError("Available paid offers require estimatedUsdMicros")
        credit_cost = offer.get("creditCost")
        credit_balance = offer.get("creditBalance")
        burn_ppm = 1_000_000
        if credit_cost is not None and credit_balance is not None:
            cc, cb = float(credit_cost), float(credit_balance)
            if cc < 0 or cb < 0:
                raise ValueError("Credit observations must be nonnegative")
            burn_ppm = 1_000_000 if cb <= 0 else min(1_000_000, round(cc / cb * 1_000_000))
        normalized.append(
            {
                "offerId": offer_id,
                "providerId": provider,
                "model": str(offer.get("model") or ""),
                "available": available,
                "spendClass": spend,
                "estimatedUsdMicros": cost_micros,
                "creditCost": credit_cost,
                "creditBalance": credit_balance,
                "creditBurnPpm": burn_ppm,
                "inputModes": modes,
                "aspectRatios": ratios,
                "minSeconds": min_s,
                "maxSeconds": max_s,
                "notes": list(offer.get("notes") or []),
            }
        )
    body = {
        "schema": OFFERS_SCHEMA,
        "observedAt": observed_at,
        "offers": sorted(normalized, key=lambda x: x["offerId"]),
        "authority": "runtime-observation-only",
        "laws": [
            "OFFER SNAPSHOT != PROVIDER GUARANTEE",
            "CREDIT UNIT != CROSS-PROVIDER MONEY UNIT",
            "ROUTER MAY ORDER OFFERS BUT CANNOT EXECUTE THEM",
        ],
    }
    digest = _sha(body)
    path = _offer_path(root, digest)
    _save(path, body)
    return {"offers": str(path), "offersSha256": digest, "offersBody": body}


def load_offers(root, offers_path):
    root = _root(root)
    path = Path(offers_path).expanduser().resolve(strict=True)
    body = json.loads(path.read_text(encoding="utf-8"))
    if body.get("schema") != OFFERS_SCHEMA:
        raise ValueError("Unsupported provider-offer snapshot")
    digest = _sha(body)
    if path != _offer_path(root, digest):
        raise ValueError("Provider-offer snapshot identity changed")
    return body, digest


def _eligible(request: dict, offer: dict) -> bool:
    return (
        offer["available"]
        and request["inputMode"] in offer["inputModes"]
        and request["aspectRatio"] in offer["aspectRatios"]
        and offer["minSeconds"] <= request["durationSeconds"] <= offer["maxSeconds"]
    )


def _rank_key(offer: dict):
    spend = _SPEND_ORDER[offer["spendClass"]]
    # Free/included offers are ranked by proportion of their own observed balance
    # consumed. Paid offers are ranked by observed USD estimate.
    if offer["spendClass"] == "paid":
        economic = int(offer["estimatedUsdMicros"])
        burn = 0
    else:
        economic = 0
        burn = int(offer["creditBurnPpm"])
    return (spend, economic, burn, offer["providerId"], offer["offerId"])


def route_request(root, request_path, offers_path, *, max_attempts: int = 8) -> dict:
    root = _root(root)
    request, request_sha = load_request(root, request_path)
    offers, offers_sha = load_offers(root, offers_path)
    max_attempts = int(max_attempts)
    if not (1 <= max_attempts <= 32):
        raise ValueError("max_attempts must be 1–32")
    eligible = [offer for offer in offers["offers"] if _eligible(request, offer)]
    ordered = sorted(eligible, key=_rank_key)[:max_attempts]
    if not ordered:
        raise ValueError("No eligible provider offers exist for this request")

    attempts = []
    for index, offer in enumerate(ordered, start=1):
        attempts.append(
            {
                "attempt": index,
                "offerId": offer["offerId"],
                "providerId": offer["providerId"],
                "model": offer["model"],
                "spendClass": offer["spendClass"],
                "estimatedUsdMicros": offer["estimatedUsdMicros"],
                "creditBurnPpm": offer["creditBurnPpm"],
                "status": "not_attempted",
            }
        )
    body = {
        "schema": ROUTE_SCHEMA,
        "requestSha256": request_sha,
        "offersSha256": offers_sha,
        "observedAt": offers["observedAt"],
        "attempts": attempts,
        "policy": "eligible_then_spend_class_then_observed_cost_then_credit_burn_then_stable_id",
        "authority": "execution-order-proposal-only",
        "laws": [
            "ROUTE ORDER != GENERATION",
            "FAILED PROVIDER != FAILED FILM",
            "PROVIDER != EDITOR",
            "CHEAPEST ELIGIBLE FIRST, SUBJECT TO OBSERVED RUNTIME FACTS",
        ],
    }
    digest = _sha(body)
    path = _route_path(root, digest)
    _save(path, body)
    return {"route": str(path), "routeSha256": digest, "routeBody": body}


def load_route(root, route_path):
    root = _root(root)
    path = Path(route_path).expanduser().resolve(strict=True)
    body = json.loads(path.read_text(encoding="utf-8"))
    if body.get("schema") != ROUTE_SCHEMA:
        raise ValueError("Unsupported route plan")
    digest = _sha(body)
    if path != _route_path(root, digest):
        raise ValueError("Route plan identity changed")
    request_path = _request_path(root, body["requestSha256"])
    offers_path = _offer_path(root, body["offersSha256"])
    load_request(root, request_path)
    load_offers(root, offers_path)
    return body, digest


def to_relatte_organ_spec(root, route_path, *, created_at: str, source_world: str,
                          source_particular: str, return_address: str | None = None) -> dict:
    root = _root(root)
    route, route_sha = load_route(root, route_path)
    request, _ = load_request(root, _request_path(root, route["requestSha256"]))
    body = {
        "schema": "relatte.opaque-organ-spec/v0",
        "family_ref": "franken-blender/motion-organ/v1",
        "donor_contract_ref": "runtime-provider-offer/v1",
        "artifact_kind": "MOTION_AWAKENING_REQUEST",
        "source_world": _nonnull_string(source_world, "source_world"),
        "source_particular": _nonnull_string(source_particular, "source_particular"),
        "source_history_head": route_sha,
        "payload_refs": [
            {
                "address": f"sha256:{route['requestSha256']}",
                "role": "motion-request",
                "media_type": "application/json",
            },
            {
                "address": request["sourceAddress"],
                "role": "source-visual",
                "media_type": "application/octet-stream",
            },
        ],
        "donor_claims": {
            "route_policy": route["policy"],
            "attempt_count": len(route["attempts"]),
            "provider_semantics_opaque": True,
        },
        "requested_effect": {
            "window_id": request["windowId"],
            "duration_seconds": request["durationSeconds"],
            "aspect_ratio": request["aspectRatio"],
            "input_mode": request["inputMode"],
            "prompt": request["prompt"],
        },
        "return_address": return_address,
        "created_at": _nonnull_string(created_at, "created_at"),
    }
    return body


def _probe_video(path: Path) -> dict:
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        raise RuntimeError("ffprobe is required")
    proc = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration:stream=index,codec_type,width,height",
         "-of", "json", str(path)],
        check=True, capture_output=True, text=True, timeout=30,
    )
    raw = json.loads(proc.stdout)
    video = next((s for s in raw.get("streams", []) if s.get("codec_type") == "video"), None)
    if video is None:
        raise ValueError("Candidate MP4 has no usable video stream")
    return {
        "durationSeconds": float(raw["format"]["duration"]),
        "width": int(video.get("width") or 0),
        "height": int(video.get("height") or 0),
    }


def admit_candidate(root, route_path, offer_id: str, video, *, provider_job_id: str) -> dict:
    root = _root(root)
    route, route_sha = load_route(root, route_path)
    request, request_sha = load_request(root, _request_path(root, route["requestSha256"]))
    attempt = next((a for a in route["attempts"] if a["offerId"] == offer_id), None)
    if attempt is None:
        raise ValueError("Offer is not present in this route plan")
    provider_job_id = _nonnull_string(provider_job_id, "provider_job_id")
    if not re.fullmatch(r"[A-Za-z0-9._:-]{3,160}", provider_job_id):
        raise ValueError("provider_job_id has unsupported characters")
    supplied = Path(video).expanduser()
    if supplied.is_symlink():
        raise ValueError("Symlink videos are not admitted")
    source = supplied.resolve(strict=True)
    if not source.is_file() or source.suffix.lower() != ".mp4":
        raise ValueError("Expected completed MP4 candidate")
    info = _probe_video(source)
    if info["durationSeconds"] + 0.05 < request["durationSeconds"]:
        raise ValueError("Candidate is shorter than requested motion window")
    video_sha = catalog.digest_file(source)
    folder = _candidate_folder(root)
    target = folder / f"{request_sha}-{offer_id}-{video_sha}.mp4"
    receipt_path = target.with_suffix(".mp4.receipt.json")
    if target.exists() or receipt_path.exists():
        raise ValueError("Refusing to overwrite candidate or receipt")
    folder.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as src, target.open("xb") as dst:
        shutil.copyfileobj(src, dst)
    if catalog.digest_file(target) != video_sha:
        target.unlink(missing_ok=True)
        raise ValueError("Candidate changed during admission")
    receipt = {
        "schema": CANDIDATE_RECEIPT_SCHEMA,
        "status": "candidate_admitted_not_filmmaker_accepted",
        "requestSha256": request_sha,
        "routeSha256": route_sha,
        "offerId": offer_id,
        "providerId": attempt["providerId"],
        "model": attempt["model"],
        "providerJobIdReported": provider_job_id,
        "providerExecutionIndependentlyVerified": False,
        "outputSha256": video_sha,
        "durationSeconds": info["durationSeconds"],
        "width": info["width"],
        "height": info["height"],
        "distributionAuthorized": False,
        "nonclaims": [
            "Admission verifies local bytes, not provider execution authenticity",
            "Provider-generated motion is not an editorial decision",
            "Candidate admission is not filmmaker acceptance",
        ],
    }
    _save(receipt_path, receipt)
    return {
        "video": str(target),
        "receipt": str(receipt_path),
        "outputSha256": video_sha,
        "providerId": attempt["providerId"],
        "offerId": offer_id,
    }


def candidate_board(root, request_path) -> dict:
    root = _root(root)
    request, request_sha = load_request(root, request_path)
    folder = _candidate_folder(root)
    candidates = []
    if folder.is_dir():
        for receipt_path in sorted(folder.glob(f"{request_sha}-*.mp4.receipt.json")):
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            if receipt.get("schema") != CANDIDATE_RECEIPT_SCHEMA:
                continue
            video_path = receipt_path.with_suffix("").with_suffix("")
            # .mp4.receipt.json -> strip .json then .receipt => .mp4
            if not video_path.is_file():
                # pathlib suffix stripping above leaves .mp4; guard only.
                continue
            if catalog.digest_file(video_path) != receipt.get("outputSha256"):
                continue
            candidates.append(
                {
                    "providerId": receipt["providerId"],
                    "model": receipt["model"],
                    "offerId": receipt["offerId"],
                    "videoSha256": receipt["outputSha256"],
                    "durationSeconds": receipt["durationSeconds"],
                    "video": str(video_path),
                    "receipt": str(receipt_path),
                }
            )
    body = {
        "schema": BOARD_SCHEMA,
        "requestSha256": request_sha,
        "windowId": request["windowId"],
        "candidates": candidates,
        "authority": "comparison-only",
        "laws": ["BOARD != RANKING", "VIEWING != ACCEPTANCE", "PROVIDER COUNT != CONSENSUS"],
    }
    return body


def accept_candidate(root, request_path, video, *, filmmaker_approval: bool = False) -> dict:
    if filmmaker_approval is not True:
        raise ValueError("Explicit filmmaker KEEP is required")
    root = _root(root)
    request, request_sha = load_request(root, request_path)
    path = Path(video).expanduser().resolve(strict=True)
    receipt_path = path.with_suffix(".mp4.receipt.json")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (
        receipt.get("schema") != CANDIDATE_RECEIPT_SCHEMA
        or receipt.get("status") != "candidate_admitted_not_filmmaker_accepted"
        or receipt.get("requestSha256") != request_sha
        or receipt.get("outputSha256") != catalog.digest_file(path)
        or path.parent != _candidate_folder(root)
    ):
        raise ValueError("Motion candidate bytes or lineage changed")

    witness = {
        "schema": ACCEPTANCE_SCHEMA,
        "requestSha256": request_sha,
        "candidateReceiptSha256": catalog.digest_file(receipt_path),
        "sceneId": request["sceneId"],
        "sceneSha256": request["sceneSha256"],
        "windowId": request["windowId"],
        "providerId": receipt["providerId"],
        "offerId": receipt["offerId"],
        "videoSha256": receipt["outputSha256"],
        "status": "filmmaker_accepted_private_motion_organ",
        "distributionAuthorized": False,
        "laws": [
            "HUMAN KEEP != RELEASE",
            "ACCEPTED PROVIDER OUTPUT != PROVIDER AUTHORITY",
            "ACCEPTED MOTION MAY ENTER ONLY ITS FROZEN WINDOW",
        ],
    }
    digest = _sha(witness)
    dest = _acceptance_path(root, digest)
    _save(dest, witness)
    return {"acceptance": str(dest), "video": str(path), "videoSha256": witness["videoSha256"]}
