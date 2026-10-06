"""FRANKEN BLENDER 008d — plugin orchard observations and learning.

The orchard is deliberately split from plugin execution. Connected ChatGPT apps
are external observation/execution surfaces; they are not local SDK credentials.

An external orchestrator may crawl account/model/cost facts and feed a normalized
snapshot here. The orchard turns only compatible, currently-observed rows into
Motion Organ offers and records empirical outcomes after every provider use.
"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

from . import motion_organ, project

OBSERVATION_SCHEMA = "haunted-blender/plugin-orchard-observation/v1"
SNAPSHOT_SCHEMA = "haunted-blender/plugin-orchard-snapshot/v1"
USAGE_SCHEMA = "haunted-blender/plugin-orchard-usage/v1"
USAGE_INDEX_SCHEMA = "haunted-blender/plugin-orchard-usage-index/v1"
LATEST_SCHEMA = "haunted-blender/plugin-orchard-latest/v1"

_SENSITIVE_KEYS = re.compile(
    r"(?:email|token|secret|password|api[_-]?key|access[_-]?key|authorization|cookie|credential)",
    re.I,
)
_ROUTE_INPUT_MODE = {
    "image-to-video": "image-to-video",
    "text-to-video": "text-to-video",
    "element-to-video": "element-to-video",
    "reference-to-video": "element-to-video",
    "motion-control": "image-to-video",
    "replace-object": "image-to-video",
}


def _root(root) -> Path:
    return Path(root).expanduser().resolve()


def _canonical(value: Any) -> bytes:
    return project.stable_bytes(value)


def _sha(value: Any) -> str:
    import hashlib
    return hashlib.sha256(_canonical(value)).hexdigest()


def _save_immutable(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _canonical(value) + b"\n"
    try:
        with path.open("xb") as handle:
            handle.write(payload)
    except FileExistsError:
        if path.read_bytes() != payload:
            raise ValueError("Existing orchard witness changed")


def _assert_no_secrets(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if _SENSITIVE_KEYS.search(str(key)):
                raise ValueError(f"Orchard observations must not persist credentials/PII key {path}.{key}")
            _assert_no_secrets(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_no_secrets(child, f"{path}[{index}]")


def profiles_path() -> Path:
    return Path(__file__).with_name("plugin_provider_profiles.json")


def load_profiles() -> dict:
    body = json.loads(profiles_path().read_text(encoding="utf-8"))
    if body.get("schema") != "haunted-blender/plugin-provider-profiles/v1":
        raise ValueError("Unsupported plugin provider profile catalog")
    return body


def _profile_ids() -> set[str]:
    return {str(p["id"]) for p in load_profiles().get("profiles") or []}


def _normalize_model(raw: dict) -> dict:
    if not isinstance(raw, dict):
        raise ValueError("Provider model observation must be an object")
    model = str(raw.get("model") or "").strip()
    route_kind = str(raw.get("routeKind") or "").strip()
    if not model or not route_kind:
        raise ValueError("Observed model requires model and routeKind")
    spend = str(raw.get("spendClass") or "paid")
    if spend not in {"free", "included", "paid", "unavailable"}:
        raise ValueError("spendClass must be free, included, paid, or unavailable")
    min_s = float(raw.get("minSeconds", 0))
    max_s = float(raw.get("maxSeconds", 0))
    if min_s < 0 or max_s < min_s:
        raise ValueError("Invalid model duration bounds")
    estimated_usd = raw.get("estimatedUsdMicros")
    if estimated_usd is not None:
        estimated_usd = int(estimated_usd)
        if estimated_usd < 0:
            raise ValueError("estimatedUsdMicros must be nonnegative")
    credit_cost = raw.get("creditCost")
    credit_balance = raw.get("creditBalance")
    if credit_cost is not None:
        credit_cost = float(credit_cost)
        if credit_cost < 0:
            raise ValueError("creditCost must be nonnegative")
    if credit_balance is not None:
        credit_balance = float(credit_balance)
        if credit_balance < 0:
            raise ValueError("creditBalance must be nonnegative")

    input_modes = list(raw.get("inputModes") or [])
    inferred = _ROUTE_INPUT_MODE.get(route_kind)
    if inferred and inferred not in input_modes:
        input_modes.append(inferred)

    return {
        "model": model,
        "routeKind": route_kind,
        "available": bool(raw.get("available", spend != "unavailable")),
        "spendClass": spend,
        "estimatedUsdMicros": estimated_usd,
        "creditCost": credit_cost,
        "creditBalance": credit_balance,
        "inputModes": sorted(set(str(v) for v in input_modes if str(v))),
        "aspectRatios": sorted(set(str(v) for v in (raw.get("aspectRatios") or []) if str(v))),
        "minSeconds": min_s,
        "maxSeconds": max_s,
        "freeRunsRemaining": int(raw.get("freeRunsRemaining") or 0),
        "entitlement": str(raw.get("entitlement") or ""),
        "availabilityClass": str(raw.get("availabilityClass") or ""),
        "repeatableFree": bool(raw.get("repeatableFree", False)),
        "regeneratingAllowance": bool(raw.get("regeneratingAllowance", False)),
        "resetSeconds": int(raw["resetSeconds"]) if raw.get("resetSeconds") is not None else None,
        "maxRunsPerWindow": int(raw["maxRunsPerWindow"]) if raw.get("maxRunsPerWindow") is not None else None,
        "secondsPerRun": float(raw.get("secondsPerRun") or raw.get("maxSeconds") or 0),
        "quoteFresh": bool(raw.get("quoteFresh", False)),
        "notes": [str(v) for v in (raw.get("notes") or [])],
    }


def ingest_observation(
    root,
    *,
    observed_at: str,
    providers: list[dict],
    source: str = "external-plugin-crawler",
) -> dict:
    root = _root(root)
    observed_at = str(observed_at or "").strip()
    source = str(source or "").strip()
    if not observed_at or not source:
        raise ValueError("observed_at and source are required")
    if not isinstance(providers, list) or not providers:
        raise ValueError("At least one provider observation is required")

    known = _profile_ids()
    normalized = []
    seen = set()
    for raw in providers:
        if not isinstance(raw, dict):
            raise ValueError("Provider observation must be an object")
        provider_id = str(raw.get("providerId") or "").strip()
        profile_id = str(raw.get("profileId") or provider_id).strip()
        if not provider_id or provider_id in seen:
            raise ValueError("Provider ids must be unique and nonempty")
        if profile_id not in known:
            raise ValueError(f"Unknown plugin profile: {profile_id}")
        seen.add(provider_id)
        models = [_normalize_model(v) for v in (raw.get("models") or [])]
        normalized.append(
            {
                "providerId": provider_id,
                "profileId": profile_id,
                "label": str(raw.get("label") or provider_id),
                "connected": bool(raw.get("connected", True)),
                "accountClass": str(raw.get("accountClass") or "unknown"),
                "models": sorted(models, key=lambda x: (x["routeKind"], x["model"])),
                "notes": [str(v) for v in (raw.get("notes") or [])],
            }
        )

    observation = {
        "schema": OBSERVATION_SCHEMA,
        "observedAt": observed_at,
        "source": source,
        "providers": sorted(normalized, key=lambda x: x["providerId"]),
        "laws": [
            "OBSERVATION != GUARANTEE",
            "BALANCE != SPEND AUTHORITY",
            "CATALOG MODEL != ELIGIBLE REQUEST",
            "CONNECTED PLUGIN != LOCAL CREDENTIAL",
            "STALE SNAPSHOT MUST BE REFRESHED BEFORE SUBMIT",
        ],
    }
    _assert_no_secrets(observation)
    observation_sha = _sha(observation)
    observation_path = root / "snapshots" / "plugin-orchard" / f"{observation_sha}.json"
    _save_immutable(observation_path, observation)

    offers = export_motion_offers(root, observation)
    snapshot = {
        "schema": SNAPSHOT_SCHEMA,
        "observedAt": observed_at,
        "observationSha256": observation_sha,
        "observationPath": str(observation_path.relative_to(root)),
        "motionOffersSha256": offers["offersSha256"],
        "motionOffersPath": str(Path(offers["offers"]).resolve().relative_to(root)),
        "providerCount": len(normalized),
        "offerCount": len(offers["offersBody"]["offers"]),
        "source": source,
    }
    snapshot_sha = _sha(snapshot)
    snapshot_path = root / "snapshots" / "plugin-orchard-snapshots" / f"{snapshot_sha}.json"
    _save_immutable(snapshot_path, snapshot)

    latest = {
        "schema": LATEST_SCHEMA,
        "snapshotSha256": snapshot_sha,
        "snapshotPath": str(snapshot_path.relative_to(root)),
        "observationSha256": observation_sha,
        "observationPath": str(observation_path.relative_to(root)),
        "motionOffersSha256": offers["offersSha256"],
        "motionOffersPath": str(Path(offers["offers"]).resolve().relative_to(root)),
        "observedAt": observed_at,
    }
    (root / "cockpit.orchard.latest.json").write_text(
        json.dumps(latest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {
        "observation": str(observation_path),
        "observationSha256": observation_sha,
        "snapshot": str(snapshot_path),
        "snapshotSha256": snapshot_sha,
        **offers,
    }


def export_motion_offers(root, observation: dict) -> dict:
    root = _root(root)
    if observation.get("schema") != OBSERVATION_SCHEMA:
        raise ValueError("Expected plugin orchard observation")
    offers = []
    for provider in observation.get("providers") or []:
        if not provider.get("connected"):
            continue
        for model in provider.get("models") or []:
            route_kind = model["routeKind"]
            if route_kind not in _ROUTE_INPUT_MODE:
                continue
            spend = model["spendClass"]
            available = bool(model["available"]) and spend != "unavailable"
            if spend == "unavailable":
                continue
            offer_id = f"plugin:{provider['providerId']}:{route_kind}:{model['model']}"
            notes = list(model.get("notes") or [])
            notes.extend(
                [
                    f"profile={provider['profileId']}",
                    f"routeKind={route_kind}",
                    "executionTransport=plugin_bridge",
                ]
            )
            if model.get("freeRunsRemaining"):
                notes.append(f"freeRunsRemaining={model['freeRunsRemaining']}")
            if model.get("entitlement"):
                notes.append(f"entitlement={model['entitlement']}")
            if model.get("availabilityClass"):
                notes.append(f"availabilityClass={model['availabilityClass']}")
            if model.get("repeatableFree"):
                notes.append("repeatableFree=true")
            if model.get("resetSeconds") is not None:
                notes.append(f"resetSeconds={model['resetSeconds']}")
            row = {
                "offerId": offer_id,
                "providerId": provider["providerId"],
                "model": model["model"],
                "available": available,
                "spendClass": spend,
                "inputModes": list(model["inputModes"]),
                "aspectRatios": list(model["aspectRatios"]),
                "minSeconds": model["minSeconds"],
                "maxSeconds": model["maxSeconds"],
                "notes": notes,
            }
            if model.get("estimatedUsdMicros") is not None:
                row["estimatedUsdMicros"] = model["estimatedUsdMicros"]
            if model.get("creditCost") is not None:
                row["creditCost"] = model["creditCost"]
            if model.get("creditBalance") is not None:
                row["creditBalance"] = model["creditBalance"]
            if spend == "paid" and available and row.get("estimatedUsdMicros") is None:
                # Do not lie to the 006 router: an unquoted paid plugin row is not executable yet.
                row["available"] = False
                row["notes"].append("paid-but-no-usd-estimate: refresh/preflight required")
            offers.append(row)

    if not offers:
        raise ValueError("Orchard observation contains no Motion Organ compatible offers")
    raw = {
        "schema": motion_organ.OFFERS_SCHEMA,
        "observedAt": observation["observedAt"],
        "offers": offers,
    }
    return motion_organ.freeze_offers(root, raw)


def latest(root) -> dict | None:
    root = _root(root)
    path = root / "cockpit.orchard.latest.json"
    if not path.is_file():
        return None
    body = json.loads(path.read_text(encoding="utf-8"))
    if body.get("schema") != LATEST_SCHEMA:
        raise ValueError("Unsupported orchard latest pointer")
    return body


def latest_offers_path(root) -> Path | None:
    root = _root(root)
    body = latest(root)
    if body is None:
        return None
    path = (root / body["motionOffersPath"]).resolve(strict=True)
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError("Orchard offers path escaped project root") from exc
    return path


def _usage_index_path(root: Path) -> Path:
    return root / "cockpit.orchard.usage.json"


def _load_usage_index(root: Path) -> dict:
    path = _usage_index_path(root)
    if not path.is_file():
        return {
            "schema": USAGE_INDEX_SCHEMA,
            "events": 0,
            "providers": {},
        }
    body = json.loads(path.read_text(encoding="utf-8"))
    if body.get("schema") != USAGE_INDEX_SCHEMA:
        raise ValueError("Unsupported orchard usage index")
    return body


def record_usage(
    root,
    *,
    observed_at: str,
    provider_id: str,
    model: str,
    phase: str,
    outcome: str,
    latency_ms: int | None = None,
    quoted_credits: float | None = None,
    billed_credits: float | None = None,
    quoted_usd_micros: int | None = None,
    billed_usd_micros: int | None = None,
    candidate_sha256: str | None = None,
    notes: list[str] | None = None,
) -> dict:
    root = _root(root)
    event = {
        "schema": USAGE_SCHEMA,
        "observedAt": str(observed_at or "unspecified"),
        "providerId": str(provider_id),
        "model": str(model),
        "phase": str(phase),
        "outcome": str(outcome),
        "latencyMs": int(latency_ms) if latency_ms is not None else None,
        "quotedCredits": float(quoted_credits) if quoted_credits is not None else None,
        "billedCredits": float(billed_credits) if billed_credits is not None else None,
        "quotedUsdMicros": int(quoted_usd_micros) if quoted_usd_micros is not None else None,
        "billedUsdMicros": int(billed_usd_micros) if billed_usd_micros is not None else None,
        "candidateSha256": candidate_sha256,
        "notes": [str(v) for v in (notes or [])],
    }
    _assert_no_secrets(event)
    digest = _sha(event)
    path = root / "snapshots" / "plugin-orchard-usage" / f"{digest}.json"
    _save_immutable(path, event)

    index = _load_usage_index(root)
    index["events"] = int(index.get("events") or 0) + 1
    provider = index.setdefault("providers", {}).setdefault(
        str(provider_id),
        {
            "events": 0,
            "successes": 0,
            "failures": 0,
            "candidateReady": 0,
            "latencyMsTotal": 0,
            "latencySamples": 0,
            "lastObservedAt": None,
            "models": {},
        },
    )
    provider["events"] += 1
    provider["lastObservedAt"] = event["observedAt"]
    if outcome in {"success", "completed", "candidate_ready", "accepted"}:
        provider["successes"] += 1
    if outcome in {"failed", "error", "definitively_failed"}:
        provider["failures"] += 1
    if outcome == "candidate_ready":
        provider["candidateReady"] += 1
    if latency_ms is not None:
        provider["latencyMsTotal"] += int(latency_ms)
        provider["latencySamples"] += 1
    model_row = provider.setdefault("models", {}).setdefault(
        str(model), {"events": 0, "candidateReady": 0, "accepted": 0, "declined": 0}
    )
    model_row["events"] += 1
    if outcome == "candidate_ready":
        model_row["candidateReady"] += 1
    if outcome == "accepted":
        model_row["accepted"] += 1
    if outcome == "declined":
        model_row["declined"] += 1

    _usage_index_path(root).write_text(
        json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {
        "event": str(path),
        "eventSha256": digest,
        "usage": copy.deepcopy(index),
    }


def usage_summary(root) -> dict:
    root = _root(root)
    body = _load_usage_index(root)
    result = copy.deepcopy(body)
    for provider in result.get("providers", {}).values():
        samples = int(provider.get("latencySamples") or 0)
        provider["meanLatencyMs"] = (
            round(provider.get("latencyMsTotal", 0) / samples, 2) if samples else None
        )
    return result
