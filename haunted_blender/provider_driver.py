"""FRANKEN BLENDER 008c — receipt-driven provider adapter execution.

This module connects the immutable 007 execution state machine to replaceable
provider adapters without granting adapters editorial or spending authority.

A command adapter receives one JSON packet on stdin and returns one JSON result
on stdout. No shell is involved. Provider secrets remain adapter-local.

CAPABILITIES -> QUOTE -> [APPROVAL IF PAID] -> SUBMIT ONCE -> STATUS -> FETCH
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

from . import (
    cockpit,
    cockpit_engine,
    cockpit_media,
    motion_executor,
    motion_organ,
    project,
    scene_growth,
)

ADAPTER_CONFIG_SCHEMA = "haunted-blender/provider-adapters/v1"
ADAPTER_CALL_SCHEMA = "haunted-blender/provider-adapter-call/v1"
ADAPTER_RESULT_SCHEMA = "haunted-blender/provider-adapter-result/v1"
APPROVAL_SCHEMA = "haunted-blender/provider-spend-approval/v1"
DECLINE_SCHEMA = "haunted-blender/provider-candidate-decline/v1"


def _root(root) -> Path:
    return Path(root).expanduser().resolve()


def _sha(value: object) -> str:
    return hashlib.sha256(project.stable_bytes(value)).hexdigest()


def _safe_relative(root: Path, value: str | Path, *, must_exist: bool = True) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    path = path.expanduser().resolve(strict=must_exist)
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError("Provider-driver paths must stay inside the project root") from exc
    return path


def _config_path(root: Path) -> Path:
    return root / "cockpit.adapters.json"


def configure_adapters(root, adapters: list[dict]) -> dict:
    root = _root(root)
    cockpit.load_project(root)
    if not isinstance(adapters, list) or not adapters:
        raise ValueError("At least one provider adapter is required")

    seen = set()
    normalized = []
    for raw in adapters:
        if not isinstance(raw, dict):
            raise ValueError("Provider adapter must be an object")
        provider_id = str(raw.get("providerId") or "").strip()
        if not provider_id or provider_id in seen:
            raise ValueError("Provider adapter ids must be unique and nonempty")
        seen.add(provider_id)
        transport = raw.get("transport", "command")
        if transport != "command":
            raise ValueError("008c supports only command transport")
        argv = raw.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(v, str) and v for v in argv):
            raise ValueError("Command adapter argv must be a nonempty string list")
        cwd_value = str(raw.get("cwd") or ".")
        cwd = _safe_relative(root, cwd_value)
        if not cwd.is_dir():
            raise ValueError("Adapter cwd must be a directory")
        timeout = int(raw.get("timeoutSeconds", 180))
        if not (1 <= timeout <= 1800):
            raise ValueError("Adapter timeoutSeconds must be between 1 and 1800")
        normalized.append(
            {
                "providerId": provider_id,
                "transport": "command",
                "argv": list(argv),
                "cwd": str(cwd.relative_to(root)),
                "timeoutSeconds": timeout,
                "notes": list(raw.get("notes") or []),
            }
        )

    body = {
        "schema": ADAPTER_CONFIG_SCHEMA,
        "adapters": sorted(normalized, key=lambda a: a["providerId"]),
        "laws": [
            "ADAPTER != AUTHORITY",
            "NO SHELL",
            "QUOTE != SPEND APPROVAL",
            "SUBMIT RECEIPT != EDITORIAL KEEP",
        ],
    }
    _config_path(root).write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return body


def load_adapters(root) -> dict:
    root = _root(root)
    path = _config_path(root)
    if not path.is_file():
        raise FileNotFoundError("No cockpit.adapters.json is configured")
    body = json.loads(path.read_text(encoding="utf-8"))
    if body.get("schema") != ADAPTER_CONFIG_SCHEMA:
        raise ValueError("Unsupported provider adapter config")
    return body


def _adapter_spec(root: Path, provider_id: str) -> dict:
    config = load_adapters(root)
    spec = next((a for a in config["adapters"] if a["providerId"] == provider_id), None)
    if spec is None:
        raise ValueError(f"No adapter configured for provider {provider_id}")
    return spec


def _invoke(root: Path, provider_id: str, phase: str, payload: dict) -> dict:
    spec = _adapter_spec(root, provider_id)
    packet = {
        "schema": ADAPTER_CALL_SCHEMA,
        "phase": phase,
        "providerId": provider_id,
        "payload": payload,
        "laws": [
            "RETURN OBSERVATION, NOT AUTHORITY",
            "DO NOT SUBMIT DURING CAPABILITIES OR QUOTE",
            "SUBMIT EXACTLY ONCE WHEN PHASE == SUBMIT",
        ],
    }
    proc = subprocess.run(
        spec["argv"],
        input=json.dumps(packet, sort_keys=True),
        capture_output=True,
        text=True,
        cwd=_safe_relative(root, spec["cwd"]),
        env=os.environ.copy(),
        timeout=int(spec["timeoutSeconds"]),
        shell=False,
    )
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()[-2000:]
        raise RuntimeError(f"Provider adapter failed ({proc.returncode}): {stderr}")
    stdout = (proc.stdout or "").strip()
    if len(stdout.encode("utf-8")) > 2_000_000:
        raise ValueError("Provider adapter response is too large")
    try:
        response = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("Provider adapter returned invalid JSON") from exc
    if response.get("schema") != ADAPTER_RESULT_SCHEMA:
        raise ValueError("Provider adapter result schema mismatch")
    if response.get("providerId") != provider_id or response.get("phase") != phase:
        raise ValueError("Provider adapter response does not bind the call")
    if response.get("ok") is not True:
        raise RuntimeError(str(response.get("error") or "Provider adapter reported failure"))
    result = response.get("result")
    if not isinstance(result, dict):
        raise ValueError("Provider adapter result must be an object")
    return result


def _project_section(root: Path, section_id: str) -> tuple[dict, dict]:
    project_body = cockpit.load_project(root)
    section = next((s for s in project_body["sections"] if s["id"] == section_id), None)
    if section is None:
        raise ValueError("Unknown Cockpit section")
    return project_body, section


def _engine(section: dict) -> dict:
    value = section.get("engine")
    if not isinstance(value, dict):
        raise ValueError("Section has no automatic engine state")
    return value


def _required_paths(root: Path, section_id: str) -> tuple[dict, dict, dict, Path, Path]:
    project_body, section = _project_section(root, section_id)
    engine = _engine(section)
    plan_value = engine.get("motionPlanPath")
    state_value = engine.get("motionStatePath")
    route_value = engine.get("motionRoutePath")
    if not plan_value or not state_value or not route_value:
        raise ValueError("AWAKEN has not prepared a provider execution plan")
    return (
        project_body,
        section,
        engine,
        _safe_relative(root, plan_value),
        _safe_relative(root, state_value),
    )


def _set_state_path(root: Path, section_id: str, path: str | Path) -> None:
    project_body, section = _project_section(root, section_id)
    engine = _engine(section)
    engine["motionStatePath"] = str(Path(path).resolve().relative_to(root))
    cockpit._save(root, project_body)


def _driver_meta(root: Path, section_id: str) -> dict:
    project_body, section = _project_section(root, section_id)
    value = section.get("providerDriver")
    if not isinstance(value, dict):
        value = {"receipts": {}, "spendApprovals": {}, "declines": []}
        section["providerDriver"] = value
        cockpit._save(root, project_body)
    return value


def _set_meta(root: Path, section_id: str, mutate) -> dict:
    project_body, section = _project_section(root, section_id)
    meta = section.get("providerDriver")
    if not isinstance(meta, dict):
        meta = {"receipts": {}, "spendApprovals": {}, "declines": []}
        section["providerDriver"] = meta
    mutate(meta)
    cockpit._save(root, project_body)
    return copy.deepcopy(meta)


def _store_receipt(root: Path, section_id: str, attempt: int, phase: str, receipt: dict) -> tuple[str, Path]:
    digest = _sha(receipt)
    folder = root / "snapshots" / "provider-driver-receipts"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{digest}.json"
    payload = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if path.exists():
        if json.loads(path.read_text(encoding="utf-8")) != receipt:
            raise ValueError("Provider receipt identity collision")
    else:
        path.write_text(payload, encoding="utf-8")

    def mutate(meta):
        receipts = meta.setdefault("receipts", {})
        bucket = receipts.setdefault(str(int(attempt)), {})
        bucket[phase] = str(path.relative_to(root))

    _set_meta(root, section_id, mutate)
    return digest, path


def _current(root: Path, section_id: str) -> dict:
    _, section, engine, plan_path, state_path = _required_paths(root, section_id)
    plan, plan_sha = motion_executor.load_plan(root, plan_path)
    state, state_sha = motion_executor.load_state(root, state_path)
    nxt = motion_executor.next_action(root, plan_path, state_path)
    request, request_sha = motion_organ.load_request(
        root, motion_organ._request_path(root, plan["requestSha256"])
    )
    route_path = _safe_relative(root, engine["motionRoutePath"])
    route, route_sha = motion_organ.load_route(root, route_path)
    attempt = None
    if 1 <= int(state.get("currentAttempt", 0)) <= len(state.get("attempts") or []):
        attempt = state["attempts"][int(state["currentAttempt"]) - 1]
    return {
        "section": section,
        "engine": engine,
        "plan": plan,
        "planSha256": plan_sha,
        "planPath": plan_path,
        "state": state,
        "stateSha256": state_sha,
        "statePath": state_path,
        "request": request,
        "requestSha256": request_sha,
        "route": route,
        "routeSha256": route_sha,
        "routePath": route_path,
        "attempt": attempt,
        "next": nxt,
    }


def _source_path(root: Path, section_id: str) -> Path:
    path = root / "cockpit-derived" / section_id / "motion-source.png"
    return _safe_relative(root, path)


def _base_payload(root: Path, section_id: str, current: dict) -> dict:
    return {
        "sectionId": section_id,
        "request": copy.deepcopy(current["request"]),
        "attempt": copy.deepcopy(current["attempt"] or {}),
        "sourcePath": str(_source_path(root, section_id)),
        "planSha256": current["planSha256"],
        "routeSha256": current["routeSha256"],
    }


def _approval_needed(attempt: dict | None) -> bool:
    if not attempt:
        return False
    usd = attempt.get("quotedUsdMicros")
    return attempt.get("spendClass") == "paid" or (isinstance(usd, int) and usd > 0)


def _approval_for(root: Path, section_id: str, current: dict) -> dict | None:
    attempt = current["attempt"]
    if not attempt:
        return None
    meta = _driver_meta(root, section_id)
    rel = (meta.get("spendApprovals") or {}).get(str(attempt["attempt"]))
    if not rel:
        return None
    path = _safe_relative(root, rel)
    witness = json.loads(path.read_text(encoding="utf-8"))
    if witness.get("schema") != APPROVAL_SCHEMA:
        raise ValueError("Spend approval schema changed")
    expected = {
        "planSha256": current["planSha256"],
        "attempt": attempt["attempt"],
        "offerId": attempt["offerId"],
        "providerId": attempt["providerId"],
        "quoteReceiptSha256": attempt.get("quoteReceiptSha256"),
        "approvedUsdMicros": attempt.get("quotedUsdMicros"),
    }
    for key, value in expected.items():
        if witness.get(key) != value:
            raise ValueError("Spend approval no longer binds current exact quote")
    if witness.get("decision") != "APPROVE_ONCE":
        raise ValueError("Spend approval is not affirmative")
    return witness


def approve_spend(
    root,
    section_id: str,
    *,
    expected_usd_micros: int | None,
    approved_at: str,
) -> dict:
    root = _root(root)
    current = _current(root, section_id)
    if current["next"].get("action") != "SUBMIT":
        raise ValueError("Spend approval is only valid immediately before SUBMIT")
    attempt = current["attempt"]
    if not _approval_needed(attempt):
        raise ValueError("Current exact quote does not require paid approval")
    quoted = attempt.get("quotedUsdMicros")
    if quoted != expected_usd_micros:
        raise ValueError("Displayed and approved USD amount no longer matches exact quote")
    approved_at = str(approved_at or "").strip()
    if not approved_at:
        raise ValueError("approved_at is required")

    witness = {
        "schema": APPROVAL_SCHEMA,
        "decision": "APPROVE_ONCE",
        "approvedAt": approved_at,
        "planSha256": current["planSha256"],
        "attempt": attempt["attempt"],
        "providerId": attempt["providerId"],
        "offerId": attempt["offerId"],
        "quoteReceiptSha256": attempt["quoteReceiptSha256"],
        "approvedUsdMicros": quoted,
        "laws": [
            "QUOTE != APPROVAL",
            "APPROVAL BINDS ONE EXACT PLAN ATTEMPT AND QUOTE",
            "APPROVAL != SUBMISSION",
            "SUBMIT ONCE PER ATTEMPT",
        ],
    }
    digest = _sha(witness)
    folder = root / "snapshots" / "provider-spend-approvals"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{digest}.json"
    if not path.exists():
        path.write_text(json.dumps(witness, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def mutate(meta):
        meta.setdefault("spendApprovals", {})[str(attempt["attempt"])] = str(path.relative_to(root))

    _set_meta(root, section_id, mutate)
    return {"approval": str(path), "approvalSha256": digest, "witness": witness}


def _record_transition(root: Path, section_id: str, result: dict) -> None:
    _set_state_path(root, section_id, result["state"])


def drive(root, section_id: str, *, max_steps: int = 12) -> dict:
    root = _root(root)
    max_steps = int(max_steps)
    if not (1 <= max_steps <= 32):
        raise ValueError("max_steps must be between 1 and 32")

    trace = []
    for _ in range(max_steps):
        current = _current(root, section_id)
        action = current["next"].get("action")
        trace.append({"action": action, "status": current["next"].get("status")})

        if action == "STOP":
            return {"status": "stopped", "trace": trace, "view": provider_view(root, section_id)}

        if action == "ADVANCE":
            result = motion_executor.advance(
                root, current["planPath"], current["statePath"]
            )
            _record_transition(root, section_id, result)
            continue

        if action == "PRESENT":
            return {"status": "candidate_ready", "trace": trace, "view": provider_view(root, section_id)}

        attempt = current["attempt"]
        if not attempt:
            raise ValueError("Execution action has no current attempt")
        provider_id = attempt["providerId"]
        payload = _base_payload(root, section_id, current)

        if action == "CAPABILITIES":
            raw = _invoke(root, provider_id, "CAPABILITIES", payload)
            receipt = {
                "schema": motion_executor.CAP_SCHEMA,
                "offerId": attempt["offerId"],
                "providerId": provider_id,
                "model": attempt["model"],
                "observedAt": str(raw.get("observedAt") or "unspecified"),
                "available": raw.get("available") is True,
                "inputModes": list(raw.get("inputModes") or []),
                "aspectRatios": list(raw.get("aspectRatios") or []),
                "minSeconds": float(raw.get("minSeconds", 0)),
                "maxSeconds": float(raw.get("maxSeconds", 0)),
            }
            _store_receipt(root, section_id, attempt["attempt"], "capabilities", receipt)
            result = motion_executor.record_capabilities(
                root, current["planPath"], current["statePath"], receipt
            )
            _record_transition(root, section_id, result)
            continue

        if action == "QUOTE":
            raw = _invoke(root, provider_id, "QUOTE", payload)
            receipt = {
                "schema": motion_executor.QUOTE_SCHEMA,
                "offerId": attempt["offerId"],
                "observedAt": str(raw.get("observedAt") or "unspecified"),
                "exactConfiguration": raw.get("exactConfiguration") is True,
                "generatedDurationSeconds": float(raw.get("generatedDurationSeconds", 0)),
                "denomination": str(raw.get("denomination") or ""),
                "amount": raw.get("amount"),
                "wholeJobUsdMicros": raw.get("wholeJobUsdMicros"),
            }
            if receipt["wholeJobUsdMicros"] is not None:
                receipt["wholeJobUsdMicros"] = int(receipt["wholeJobUsdMicros"])
            _store_receipt(root, section_id, attempt["attempt"], "quote", receipt)
            result = motion_executor.record_quote(
                root, current["planPath"], current["statePath"], receipt
            )
            _record_transition(root, section_id, result)
            after = _current(root, section_id)
            if after["next"].get("action") == "SUBMIT" and _approval_needed(after["attempt"]):
                if _approval_for(root, section_id, after) is None:
                    return {
                        "status": "approval_required",
                        "trace": trace,
                        "view": provider_view(root, section_id),
                    }
            continue

        if action == "SUBMIT":
            if _approval_needed(attempt) and _approval_for(root, section_id, current) is None:
                return {
                    "status": "approval_required",
                    "trace": trace,
                    "view": provider_view(root, section_id),
                }
            raw = _invoke(root, provider_id, "SUBMIT", payload)
            receipt = {
                "schema": motion_executor.SUBMIT_SCHEMA,
                "offerId": attempt["offerId"],
                "observedAt": str(raw.get("observedAt") or "unspecified"),
                "vendorRequestId": str(raw.get("vendorRequestId") or ""),
                "submittedParameterSha256": str(raw.get("submittedParameterSha256") or ""),
            }
            _store_receipt(root, section_id, attempt["attempt"], "submit", receipt)
            result = motion_executor.record_submit(
                root, current["planPath"], current["statePath"], receipt
            )
            _record_transition(root, section_id, result)
            continue

        if action == "STATUS":
            raw = _invoke(root, provider_id, "STATUS", payload)
            receipt = {
                "schema": motion_executor.STATUS_SCHEMA,
                "offerId": attempt["offerId"],
                "observedAt": str(raw.get("observedAt") or "unspecified"),
                "vendorRequestId": attempt["vendorRequestId"],
                "status": str(raw.get("status") or ""),
                "queueSeconds": raw.get("queueSeconds"),
                "runtimeSeconds": raw.get("runtimeSeconds"),
            }
            _store_receipt(root, section_id, attempt["attempt"], "status", receipt)
            result = motion_executor.record_status(
                root, current["planPath"], current["statePath"], receipt
            )
            _record_transition(root, section_id, result)
            if receipt["status"] == "running":
                return {"status": "running", "trace": trace, "view": provider_view(root, section_id)}
            if receipt["status"] in {"timeout", "unresolved"}:
                return {"status": "reconcile_required", "trace": trace, "view": provider_view(root, section_id)}
            continue

        if action == "FETCH":
            vendor_id = str(attempt["vendorRequestId"])
            safe_job = hashlib.sha256(vendor_id.encode("utf-8")).hexdigest()[:16]
            output = root / "cockpit-derived" / section_id / "provider-return" / (
                f"{attempt['attempt']:02d}-{re.sub(r'[^A-Za-z0-9._-]+', '_', attempt['offerId'])}-{safe_job}.mp4"
            )
            output.parent.mkdir(parents=True, exist_ok=True)
            if output.exists():
                raise FileExistsError("Provider fetch output already exists; refusing an ambiguous refetch")
            payload["outputPath"] = str(output)
            payload["vendorRequestId"] = vendor_id
            raw = _invoke(root, provider_id, "FETCH", payload)
            if not output.is_file():
                raise ValueError("Provider adapter FETCH did not materialize the requested MP4")
            admitted = motion_organ.admit_candidate(
                root,
                current["routePath"],
                attempt["offerId"],
                output,
                provider_job_id=vendor_id,
            )
            info = motion_organ._probe_video(Path(admitted["video"]))
            receipt = {
                "schema": motion_executor.FETCH_SCHEMA,
                "offerId": attempt["offerId"],
                "observedAt": str(raw.get("observedAt") or "unspecified"),
                "vendorRequestId": vendor_id,
                "outputSha256": admitted["outputSha256"],
                "durationSeconds": info["durationSeconds"],
                "width": info["width"],
                "height": info["height"],
                "container": str(raw.get("container") or "mp4"),
                "codec": str(raw.get("codec") or "unknown"),
            }
            _store_receipt(root, section_id, attempt["attempt"], "fetch", receipt)
            result = motion_executor.record_fetch(
                root, current["planPath"], current["statePath"], receipt
            )
            _record_transition(root, section_id, result)
            cockpit_media.bind_media(
                root,
                section_id,
                kind="candidate",
                media_path=admitted["video"],
                provider_id=provider_id,
                offer_id=attempt["offerId"],
                cost_class=attempt["spendClass"],
                label=f"{provider_id} / {attempt['model']}",
            )
            return {"status": "candidate_ready", "trace": trace, "view": provider_view(root, section_id)}

        raise ValueError(f"Unsupported 007 action: {action}")

    return {"status": "step_limit", "trace": trace, "view": provider_view(root, section_id)}


def decline_current_candidate(root, section_id: str, *, reason: str = "") -> dict:
    root = _root(root)
    current = _current(root, section_id)
    if current["next"].get("action") != "PRESENT":
        raise ValueError("A provider candidate is not currently awaiting editorial disposition")
    attempt = current["attempt"]
    candidate_sha = attempt.get("candidateVideoSha256")
    if not candidate_sha:
        raise ValueError("Current candidate identity is missing")

    witness = {
        "schema": DECLINE_SCHEMA,
        "decision": "DECLINE_CONTINUE_ROUTE",
        "planSha256": current["planSha256"],
        "attempt": attempt["attempt"],
        "providerId": attempt["providerId"],
        "offerId": attempt["offerId"],
        "candidateVideoSha256": candidate_sha,
        "reason": str(reason or ""),
        "laws": [
            "EDITORIAL DECLINE != PROVIDER FAILURE",
            "DECLINED CANDIDATE REMAINS EVIDENCE",
            "DECLINE MAY OPEN THE NEXT PLANNED ATTEMPT",
        ],
    }
    digest = _sha(witness)
    folder = root / "snapshots" / "provider-candidate-declines"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{digest}.json"
    if not path.exists():
        path.write_text(json.dumps(witness, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = motion_executor.record_editorial_decline(
        root,
        current["planPath"],
        current["statePath"],
        {
            "schema": motion_executor.DECLINE_SCHEMA,
            "offerId": attempt["offerId"],
            "candidateVideoSha256": candidate_sha,
            "decision": "DECLINE_CONTINUE_ROUTE",
        },
    )
    _record_transition(root, section_id, result)

    def mutate(meta):
        meta.setdefault("declines", []).append(str(path.relative_to(root)))

    _set_meta(root, section_id, mutate)
    return {"decline": str(path), "declineSha256": digest, "view": provider_view(root, section_id)}


def accept_candidate(root, section_id: str, candidate_path: str) -> dict:
    root = _root(root)
    current = _current(root, section_id)
    section = current["section"]
    if section["temperature"] != "awakening":
        raise ValueError("Candidate KEEP requires an AWAKENING section")
    path = _safe_relative(root, candidate_path)
    accepted = motion_organ.accept_candidate(
        root,
        _safe_relative(root, current["engine"]["motionRequestPath"]),
        path,
        filmmaker_approval=True,
    )
    address = "sha256:" + accepted["videoSha256"]

    scene_path = _safe_relative(root, current["engine"]["scenePath"])
    receipt_path = _safe_relative(root, current["engine"]["sceneReceiptPath"])
    source_video = scene_path.parent / "kept-scene.mp4"
    grown = {
        "scene": json.loads(scene_path.read_text(encoding="utf-8")),
        "receipt": json.loads(receipt_path.read_text(encoding="utf-8")),
        "videoPath": str(source_video),
    }
    window_id = current["engine"].get("motionWindowId")
    if not window_id:
        raise ValueError("Prepared AWAKEN window identity is missing")
    safe_window = re.sub(r"[^A-Za-z0-9._-]+", "_", window_id)
    output = scene_path.parent / f"awakened-{safe_window}-{accepted['videoSha256'][:12]}.mp4"
    if output.is_file():
        raise FileExistsError("Awakened scene output already exists")
    awakened = scene_growth.awaken_kept_scene(
        root,
        grown,
        window_id,
        address,
        output,
    )
    cockpit_media.bind_media(
        root,
        section_id,
        kind="scene",
        media_path=awakened["output"],
        cost_class="deterministic",
        label=f"{section.get('label') or section_id} + accepted motion",
    )
    cockpit.action_witness(root, section_id, video_address=address)

    def update_engine(meta_project):
        pass

    project_body, updated_section = _project_section(root, section_id)
    engine = _engine(updated_section)
    engine["acceptedCandidatePath"] = str(path.relative_to(root))
    engine["acceptedVideoAddress"] = address
    engine["awakenedScenePath"] = str(Path(awakened["output"]).resolve().relative_to(root))
    engine["awakenedSceneReceiptPath"] = str(Path(awakened["receipt"]).resolve().relative_to(root))
    cockpit._save(root, project_body)

    return {
        "status": "witnessed",
        "candidate": str(path),
        "acceptance": accepted["acceptance"],
        "acceptedVideoAddress": address,
        "awakenedScene": awakened["output"],
        "view": provider_view(root, section_id),
    }


def provider_view(root, section_id: str) -> dict:
    root = _root(root)
    try:
        current = _current(root, section_id)
    except Exception as exc:
        return {
            "sectionId": section_id,
            "configured": _config_path(root).is_file(),
            "ready": False,
            "reason": str(exc),
            "nextAction": None,
            "approvalRequired": False,
            "quote": None,
            "candidates": [],
        }

    attempt = current["attempt"]
    next_action = current["next"].get("action")
    quote = None
    approval = None
    if attempt:
        meta = _driver_meta(root, section_id)
        rel = (meta.get("receipts") or {}).get(str(attempt["attempt"]), {}).get("quote")
        if rel:
            quote = json.loads(_safe_relative(root, rel).read_text(encoding="utf-8"))
        try:
            approval = _approval_for(root, section_id, current)
        except Exception:
            approval = None

    board = motion_organ.candidate_board(root, current["engine"]["motionRequestPath"])
    return {
        "sectionId": section_id,
        "configured": _config_path(root).is_file(),
        "ready": True,
        "nextAction": next_action,
        "status": current["state"].get("status"),
        "currentAttempt": current["state"].get("currentAttempt"),
        "attemptCount": len(current["state"].get("attempts") or []),
        "attempt": copy.deepcopy(attempt),
        "approvalRequired": next_action == "SUBMIT" and _approval_needed(attempt) and approval is None,
        "approval": approval,
        "quote": quote,
        "candidates": board.get("candidates") or [],
        "canDeclineAndContinue": next_action == "PRESENT"
        and int(current["state"].get("currentAttempt", 0)) < len(current["state"].get("attempts") or []),
        "laws": [
            "ADAPTER != AUTHORITY",
            "QUOTE != APPROVAL",
            "SUBMIT ONCE PER ATTEMPT",
            "CANDIDATE != ACCEPTANCE",
            "HUMAN KEEP != RELEASE",
        ],
    }
