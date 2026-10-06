"""External ChatGPT-plugin bridge for FRANKEN BLENDER 008d.

The local Blender cannot impersonate ChatGPT connector authentication. Instead it
emits a deterministic call packet and waits. An external orchestrator may execute
the named installed plugin tools, normalize their result to the 008c receipt
shape, and resolve the exact call. The 007 state does not advance until that
normalized result is present.
"""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import urllib.request
from pathlib import Path
from typing import Any

from . import plugin_orchard, project

CALL_SCHEMA = "haunted-blender/plugin-bridge-call/v1"
RESULT_SCHEMA = "haunted-blender/plugin-bridge-result/v1"
CLAIM_SCHEMA = "haunted-blender/plugin-bridge-claim/v1"
MAX_DOWNLOAD_BYTES = 512 * 1024 * 1024


class PluginBridgeRequired(RuntimeError):
    def __init__(self, packet: dict):
        super().__init__("External plugin bridge action required")
        self.packet = packet


class PluginBridgeReconcileRequired(RuntimeError):
    def __init__(self, packet: dict):
        super().__init__("Claimed plugin SUBMIT is unresolved; do not replay it")
        self.packet = packet


def _root(root) -> Path:
    return Path(root).expanduser().resolve()


def _sha(value: Any) -> str:
    return hashlib.sha256(project.stable_bytes(value)).hexdigest()


def _safe(root: Path, path: str | Path, *, must_exist: bool = False) -> Path:
    value = Path(path)
    if not value.is_absolute():
        value = root / value
    value = value.expanduser().resolve(strict=must_exist)
    try:
        value.relative_to(root)
    except ValueError as exc:
        raise ValueError("Plugin bridge path escaped project root") from exc
    return value


def _folders(root: Path) -> tuple[Path, Path, Path]:
    base = root / "cockpit-plugin-bridge"
    outbox = base / "outbox"
    inbox = base / "inbox"
    claims = base / "claims"
    for folder in (outbox, inbox, claims):
        folder.mkdir(parents=True, exist_ok=True)
    return outbox, inbox, claims


def _profile(profile_id: str) -> dict:
    catalog = plugin_orchard.load_profiles()
    profile = next((p for p in catalog.get("profiles") or [] if p.get("id") == profile_id), None)
    if profile is None:
        raise ValueError(f"Unknown plugin profile: {profile_id}")
    return profile


def _phase_recipe(profile: dict, phase: str) -> dict:
    tools = copy.deepcopy(profile.get("tools") or {})
    if phase == "CAPABILITIES":
        wanted = [tools.get("account"), tools.get("catalog"), tools.get("schema")]
        purpose = "Refresh live account/model capability facts for the exact frozen request."
    elif phase == "QUOTE":
        wanted = [tools.get("quote"), tools.get("catalog"), tools.get("schema")]
        purpose = "Return an exact request-shaped quote without generation."
    elif phase == "SUBMIT":
        wanted = [tools.get("submit")]
        purpose = "Submit exactly one generation for this frozen request and return its vendor job identity."
    elif phase == "STATUS":
        wanted = [tools.get("status")]
        purpose = "Poll the already-recorded vendor job; never create a replacement job."
    elif phase == "FETCH":
        wanted = [tools.get("fetch"), tools.get("status")]
        purpose = "Return the completed video URL for the already-recorded vendor job."
    else:
        raise ValueError(f"Unsupported plugin bridge phase: {phase}")
    return {
        "purpose": purpose,
        "suggestedTools": [v for v in wanted if v],
        "allProfileTools": tools,
    }


def prepare_call(
    root,
    *,
    provider_id: str,
    profile_id: str,
    phase: str,
    payload: dict,
) -> dict:
    root = _root(root)
    outbox, inbox, claims = _folders(root)
    profile = _profile(profile_id)
    packet = {
        "schema": CALL_SCHEMA,
        "providerId": str(provider_id),
        "profileId": profile_id,
        "profileLabel": profile.get("label"),
        "phase": str(phase),
        "payload": copy.deepcopy(payload),
        "recipe": _phase_recipe(profile, phase),
        "normalizationContract": normalization_contract(phase),
        "laws": [
            "PLUGIN AUTH LIVES OUTSIDE THE REPO",
            "CALL PACKET != EXECUTION",
            "NORMALIZED RESULT != EDITORIAL DECISION",
            "SUBMIT PHASE MUST CREATE AT MOST ONE VENDOR JOB",
            "STATUS/FETCH MUST REUSE THE RECORDED VENDOR JOB",
        ],
    }
    call_sha = _sha(packet)
    path = outbox / f"{call_sha}.json"
    body = json.dumps(packet, indent=2, sort_keys=True) + "\n"
    if path.exists():
        if json.loads(path.read_text(encoding="utf-8")) != packet:
            raise ValueError("Plugin bridge call identity collision")
    else:
        path.write_text(body, encoding="utf-8")
    return {
        "callSha256": call_sha,
        "callPath": str(path.relative_to(root)),
        "resultPath": str((inbox / f"{call_sha}.json").relative_to(root)),
        "claimPath": str((claims / f"{call_sha}.json").relative_to(root)),
        "packet": packet,
    }


def normalization_contract(phase: str) -> dict:
    contracts = {
        "CAPABILITIES": {
            "required": ["observedAt", "available", "inputModes", "aspectRatios", "minSeconds", "maxSeconds"],
            "example": {
                "observedAt": "2026-10-06T00:00:00Z",
                "available": True,
                "inputModes": ["image-to-video"],
                "aspectRatios": ["16:9"],
                "minSeconds": 1,
                "maxSeconds": 10,
            },
        },
        "QUOTE": {
            "required": ["observedAt", "exactConfiguration", "generatedDurationSeconds", "denomination"],
            "example": {
                "observedAt": "2026-10-06T00:00:00Z",
                "exactConfiguration": True,
                "generatedDurationSeconds": 5,
                "denomination": "provider-credits",
                "amount": 5,
                "wholeJobUsdMicros": None,
            },
        },
        "SUBMIT": {
            "required": ["observedAt", "vendorRequestId", "submittedParameterSha256"],
            "example": {
                "observedAt": "2026-10-06T00:00:00Z",
                "vendorRequestId": "provider-job-id",
                "submittedParameterSha256": "0" * 64,
            },
        },
        "STATUS": {
            "required": ["observedAt", "status"],
            "example": {
                "observedAt": "2026-10-06T00:00:00Z",
                "status": "running",
                "queueSeconds": 1.2,
                "runtimeSeconds": 3.4,
            },
        },
        "FETCH": {
            "required": ["observedAt", "outputUrl"],
            "example": {
                "observedAt": "2026-10-06T00:00:00Z",
                "outputUrl": "https://provider.example/result.mp4",
                "container": "mp4",
                "codec": "h264",
            },
        },
    }
    if phase not in contracts:
        raise ValueError(f"Unsupported bridge phase: {phase}")
    return copy.deepcopy(contracts[phase])


def claim(root, call_sha256: str, *, claimed_at: str, actor: str = "external-plugin-orchestrator") -> dict:
    root = _root(root)
    outbox, _, claims = _folders(root)
    call_path = outbox / f"{call_sha256}.json"
    if not call_path.is_file():
        raise FileNotFoundError("Unknown plugin bridge call")
    claimed_at = str(claimed_at or "").strip()
    if not claimed_at:
        raise ValueError("claimed_at is required")
    witness = {
        "schema": CLAIM_SCHEMA,
        "callSha256": call_sha256,
        "claimedAt": claimed_at,
        "actor": str(actor or "external-plugin-orchestrator"),
        "law": "CLAIM BEFORE EXTERNAL SUBMIT; UNRESOLVED CLAIM MUST NOT BE REPLAYED BLINDLY",
    }
    digest = _sha(witness)
    path = claims / f"{call_sha256}.json"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != witness:
            raise ValueError("Plugin bridge call already has a different claim witness")
    else:
        path.write_text(json.dumps(witness, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"claim": str(path.relative_to(root)), "claimSha256": digest, "witness": witness}


def resolve(
    root,
    call_sha256: str,
    *,
    result: dict,
    resolved_at: str,
    raw_reference: str | None = None,
) -> dict:
    root = _root(root)
    outbox, inbox, _ = _folders(root)
    call_path = outbox / f"{call_sha256}.json"
    if not call_path.is_file():
        raise FileNotFoundError("Unknown plugin bridge call")
    call = json.loads(call_path.read_text(encoding="utf-8"))
    if _sha(call) != call_sha256:
        raise ValueError("Plugin bridge call bytes changed")
    if not isinstance(result, dict):
        raise ValueError("Normalized plugin result must be an object")
    required = normalization_contract(call["phase"])["required"]
    missing = [name for name in required if name not in result]
    if missing:
        raise ValueError("Plugin result missing: " + ", ".join(missing))
    body = {
        "schema": RESULT_SCHEMA,
        "callSha256": call_sha256,
        "providerId": call["providerId"],
        "profileId": call["profileId"],
        "phase": call["phase"],
        "resolvedAt": str(resolved_at or "").strip(),
        "rawReference": str(raw_reference) if raw_reference else None,
        "result": copy.deepcopy(result),
        "laws": [
            "BRIDGE RESULT != PROVIDER AUTHORITY",
            "NORMALIZATION MUST PRESERVE JOB IDENTITY",
            "FETCH URL != ACCEPTED CANDIDATE",
        ],
    }
    if not body["resolvedAt"]:
        raise ValueError("resolved_at is required")
    path = inbox / f"{call_sha256}.json"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != body:
            raise ValueError("Plugin bridge call already resolved differently")
    else:
        path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"result": str(path.relative_to(root)), "resultSha256": _sha(body), "body": body}


def _download_https(url: str, output: Path) -> None:
    if not str(url).startswith("https://"):
        raise ValueError("Plugin bridge FETCH accepts HTTPS result URLs only")
    request = urllib.request.Request(str(url), headers={"User-Agent": "haunted-blender-plugin-bridge/1"})
    with urllib.request.urlopen(request, timeout=120) as response:
        length = response.headers.get("Content-Length")
        if length and int(length) > MAX_DOWNLOAD_BYTES:
            raise ValueError("Plugin result exceeds bridge download limit")
        output.parent.mkdir(parents=True, exist_ok=True)
        total = 0
        with output.open("xb") as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_DOWNLOAD_BYTES:
                    handle.close()
                    output.unlink(missing_ok=True)
                    raise ValueError("Plugin result exceeds bridge download limit")
                handle.write(chunk)


def consume_or_require(
    root,
    *,
    provider_id: str,
    profile_id: str,
    phase: str,
    payload: dict,
) -> dict:
    root = _root(root)
    prepared = prepare_call(
        root,
        provider_id=provider_id,
        profile_id=profile_id,
        phase=phase,
        payload=payload,
    )
    result_path = root / prepared["resultPath"]
    if not result_path.is_file():
        claim_path = root / prepared["claimPath"]
        if phase == "SUBMIT" and claim_path.is_file():
            raise PluginBridgeReconcileRequired(prepared)
        raise PluginBridgeRequired(prepared)
    body = json.loads(result_path.read_text(encoding="utf-8"))
    if (
        body.get("schema") != RESULT_SCHEMA
        or body.get("callSha256") != prepared["callSha256"]
        or body.get("providerId") != provider_id
        or body.get("profileId") != profile_id
        or body.get("phase") != phase
    ):
        raise ValueError("Plugin bridge result does not bind the pending call")
    result = copy.deepcopy(body.get("result") or {})
    if phase == "FETCH":
        output_value = payload.get("outputPath")
        if not output_value:
            raise ValueError("FETCH bridge packet lacks outputPath")
        output = _safe(root, output_value)
        if not output.exists():
            local_value = result.get("localPath")
            if local_value:
                source = _safe(root, local_value, must_exist=True)
                output.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, output)
            else:
                _download_https(str(result.get("outputUrl") or ""), output)
        result["materializedOutputPath"] = str(output)
    return result


def pending(root) -> list[dict]:
    root = _root(root)
    outbox, inbox, claims = _folders(root)
    rows = []
    for path in sorted(outbox.glob("*.json")):
        call_sha = path.stem
        if (inbox / f"{call_sha}.json").is_file():
            continue
        call = json.loads(path.read_text(encoding="utf-8"))
        rows.append(
            {
                "callSha256": call_sha,
                "callPath": str(path.relative_to(root)),
                "claimed": (claims / f"{call_sha}.json").is_file(),
                "providerId": call.get("providerId"),
                "profileId": call.get("profileId"),
                "phase": call.get("phase"),
                "recipe": call.get("recipe"),
            }
        )
    return rows
