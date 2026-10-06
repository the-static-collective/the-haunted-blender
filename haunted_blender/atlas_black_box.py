"""FRANKEN BLENDER 007b — Motion Atlas Black Box.

Append-only, hash-chained observations separated into three evidence lanes:
public_catalog, operational, creative.

Default schemas exclude prompts, local paths, filenames, and account identity.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from . import project

EVENT_SCHEMA = "haunted-blender/motion-atlas-event/v1"
SUMMARY_SCHEMA = "haunted-blender/motion-atlas-summary/v1"
LANES = {"public_catalog", "operational", "creative"}
_FORBIDDEN_DEFAULT_FIELDS = {"prompt", "filePath", "filename", "accountId", "accountName", "localPath"}


def _canonical(value: object) -> bytes:
    return project.stable_bytes(value)


def _sha(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _root(root) -> Path:
    return Path(root).expanduser().resolve()


def _lane_dir(root: Path, lane: str) -> Path:
    if lane not in LANES:
        raise ValueError("Unknown Motion Atlas Black Box lane")
    return root / "snapshots" / "motion-atlas-black-box" / lane


def _head_path(root: Path, lane: str) -> Path:
    return _lane_dir(root, lane) / "HEAD"


def _read_head(root: Path, lane: str) -> str | None:
    path = _head_path(root, lane)
    if not path.exists():
        return None
    value = path.read_text(encoding="utf-8").strip()
    return value or None


def _event_path(root: Path, lane: str, sequence: int, digest: str) -> Path:
    return _lane_dir(root, lane) / f"{sequence:08d}-{digest}.json"


def _events(root: Path, lane: str):
    folder = _lane_dir(root, lane)
    if not folder.is_dir():
        return []
    result = []
    for path in sorted(folder.glob("????????-*.json")):
        try:
            sequence = int(path.name[:8])
            body = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if body.get("schema") == EVENT_SCHEMA and body.get("lane") == lane:
            result.append((sequence, path, body))
    return result


def _assert_privacy_defaults(facts: dict) -> None:
    bad = _FORBIDDEN_DEFAULT_FIELDS.intersection(facts)
    if bad:
        raise ValueError(f"Black Box facts contain forbidden default fields: {sorted(bad)}")


def append_event(root, lane: str, *, kind: str, observed_at: str, facts: dict,
                 source_digest: str | None = None) -> dict:
    root = _root(root)
    if lane not in LANES:
        raise ValueError("Unknown Motion Atlas Black Box lane")
    if not isinstance(kind, str) or not kind:
        raise ValueError("Event kind is required")
    if not isinstance(observed_at, str) or not observed_at:
        raise ValueError("observed_at is required")
    if not isinstance(facts, dict):
        raise ValueError("facts must be an object")
    _assert_privacy_defaults(facts)
    if source_digest is not None and (not isinstance(source_digest, str) or len(source_digest) != 64):
        raise ValueError("source_digest must be a SHA-256 string")

    prior = _events(root, lane)
    sequence = prior[-1][0] + 1 if prior else 1
    previous = _read_head(root, lane)
    body = {
        "schema": EVENT_SCHEMA,
        "lane": lane,
        "sequence": sequence,
        "previousEventSha256": previous,
        "kind": kind,
        "observedAt": observed_at,
        "sourceDigest": source_digest,
        "facts": facts,
        "authority": {
            "public_catalog": "public-evidence-only",
            "operational": "account-local-observation-only",
            "creative": "film-local-disposition-only",
        }[lane],
        "laws": [
            "OBSERVATION != PREFERENCE",
            "KEEP != UNIVERSAL QUALITY SCORE",
            "REJECTED TAKE != BAD MODEL",
            "ONE USE != PROVIDER REPUTATION",
        ],
    }
    digest = _sha(body)
    folder = _lane_dir(root, lane)
    folder.mkdir(parents=True, exist_ok=True)
    path = _event_path(root, lane, sequence, digest)
    payload = _canonical(body) + b"\n"
    try:
        with path.open("xb") as handle:
            handle.write(payload)
    except FileExistsError:
        if path.read_bytes() != payload:
            raise ValueError("Black Box event collision changed bytes")

    head = _head_path(root, lane)
    current = head.read_text(encoding="utf-8").strip() if head.exists() else None
    if current != previous:
        raise ValueError("Black Box lane head changed concurrently")
    head.write_text(digest + "\n", encoding="utf-8")
    return {"event": str(path), "eventSha256": digest, "lane": lane, "sequence": sequence}


def verify_lane(root, lane: str) -> dict:
    root = _root(root)
    prior = None
    count = 0
    for sequence, path, body in _events(root, lane):
        if body.get("sequence") != sequence:
            raise ValueError("Black Box sequence mismatch")
        if body.get("previousEventSha256") != prior:
            raise ValueError("Black Box hash chain broken")
        digest = _sha(body)
        if path != _event_path(root, lane, sequence, digest):
            raise ValueError("Black Box event identity changed")
        prior = digest
        count += 1
    if _read_head(root, lane) != prior:
        raise ValueError("Black Box HEAD does not match event chain")
    return {"lane": lane, "eventCount": count, "headSha256": prior, "verified": True}


def record_atlas_target(root, *, observed_at: str, endpoint_id: str, atlas_state: str,
                        package_sha256: str, quote_unit=None, indicative_usd=None) -> dict:
    return append_event(
        root,
        "public_catalog",
        kind="atlas.route-target",
        observed_at=observed_at,
        source_digest=package_sha256,
        facts={
            "endpointId": endpoint_id,
            "atlasState": atlas_state,
            "quoteUnit": quote_unit,
            "indicativeUsd": indicative_usd,
            "refreshRequired": True,
        },
    )


def record_operational(root, *, kind: str, observed_at: str, plan_sha256: str,
                       provider_id: str, offer_id: str, attempt: int, facts: dict) -> dict:
    safe = {
        "planSha256": plan_sha256,
        "providerId": provider_id,
        "offerId": offer_id,
        "attempt": int(attempt),
        **facts,
    }
    return append_event(
        root,
        "operational",
        kind=kind,
        observed_at=observed_at,
        source_digest=plan_sha256,
        facts=safe,
    )


def record_creative_keep(root, *, observed_at: str, request_sha256: str,
                         scene_sha256: str, window_id: str, provider_id: str,
                         offer_id: str, candidate_sha256: str) -> dict:
    return append_event(
        root,
        "creative",
        kind="candidate.keep",
        observed_at=observed_at,
        source_digest=request_sha256,
        facts={
            "requestSha256": request_sha256,
            "sceneSha256": scene_sha256,
            "windowId": window_id,
            "providerId": provider_id,
            "offerId": offer_id,
            "candidateSha256": candidate_sha256,
            "disposition": "KEEP",
            "universalPreferenceClaim": False,
        },
    )


def summarize(root) -> dict:
    root = _root(root)
    summary = {
        "schema": SUMMARY_SCHEMA,
        "lanes": {},
        "providers": {},
        "laws": [
            "SUMMARY != QUALITY RANKING",
            "OBSERVED ACCEPTANCE RATE != UNIVERSAL MODEL QUALITY",
            "MISSING EVENTS != ZERO EVENTS",
        ],
    }
    for lane in sorted(LANES):
        summary["lanes"][lane] = verify_lane(root, lane)
        for _sequence, _path, event in _events(root, lane):
            facts = event.get("facts") or {}
            provider = facts.get("providerId")
            if not provider:
                continue
            slot = summary["providers"].setdefault(provider, {
                "operationalEvents": 0,
                "creativeEvents": 0,
                "completedJobsObserved": 0,
                "definitiveFailuresObserved": 0,
                "timeoutsObserved": 0,
                "candidatesKeptObserved": 0,
                "quotedUsdMicrosObserved": 0,
                "quotedGeneratedSecondsObserved": 0.0,
            })
            if lane == "operational":
                slot["operationalEvents"] += 1
                if event["kind"] == "provider.status":
                    status = facts.get("status")
                    if status == "completed":
                        slot["completedJobsObserved"] += 1
                    elif status in {"definitively_failed", "cancelled"}:
                        slot["definitiveFailuresObserved"] += 1
                    elif status in {"timeout", "unresolved"}:
                        slot["timeoutsObserved"] += 1
                elif event["kind"] == "provider.quote":
                    usd = facts.get("wholeJobUsdMicros")
                    generated = facts.get("generatedDurationSeconds")
                    if isinstance(usd, int):
                        slot["quotedUsdMicrosObserved"] += usd
                    if isinstance(generated, (int, float)):
                        slot["quotedGeneratedSecondsObserved"] += float(generated)
            elif lane == "creative":
                slot["creativeEvents"] += 1
                if event["kind"] == "candidate.keep":
                    slot["candidatesKeptObserved"] += 1
    summary["id"] = f"motion-atlas-summary:{_sha(summary)[:24]}"
    return summary
