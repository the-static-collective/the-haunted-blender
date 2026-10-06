"""FRANKEN BLENDER 008n — Particular to Performance.

A deterministic boundary between narrative source evidence, staging proposals,
explicit editorial admission, performed shot intent, and return receipts.

The source particular is never rewritten by a later staging decision.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .paper_director import SHOT_TYPES

SOURCE_SCHEMA = "haunted-blender/narrative-particular-source/v1"
PROPOSAL_SCHEMA = "haunted-blender/staging-proposal/v1"
ADMISSION_SCHEMA = "haunted-blender/editorial-admission/v1"
PLAN_SCHEMA = "haunted-blender/particular-performance-plan/v1"
RECEIPT_SCHEMA = "haunted-blender/particular-performance-return/v1"
SPEC_SCHEMA = "haunted-blender/particular-performance-spec/v1"

LAWS = [
    "SOURCE PARTICULAR != STAGING",
    "STAGING PROPOSAL != EDITORIAL ADMISSION",
    "EDITORIAL ADMISSION != SOURCE TRUTH",
    "PERFORMANCE != RETROACTIVE CANON",
    "PARTICULAR MAY ENTER A NEW ARRANGEMENT WITHOUT BEING REWRITTEN",
    "NO CAUSAL AUTHORITY MAY BE SYNTHESIZED BY STAGING",
    "RECEIPT != AUTHORITY",
]


def _stable(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _hash(value: object) -> str:
    return hashlib.sha256(_stable(value)).hexdigest()


def _require_schema(value: dict, schema: str) -> None:
    if value.get("schema") != schema:
        raise ValueError(f"Expected {schema}, got {value.get('schema')!r}")


def particular_source(
    *,
    label: str,
    source_locator: dict,
    particulars: list[dict],
    boundary_claims: list[str] | tuple[str, ...] = (),
) -> dict:
    if not label.strip():
        raise ValueError("label is required")
    if not isinstance(source_locator, dict) or not source_locator:
        raise ValueError("source_locator is required")
    if not particulars:
        raise ValueError("at least one particular is required")

    normalized = []
    seen = set()
    for raw in particulars:
        pid = str(raw.get("id") or "").strip()
        text = str(raw.get("text") or "").strip()
        kind = str(raw.get("kind") or "particular").strip()
        if not pid or not text:
            raise ValueError("each particular requires id and text")
        if pid in seen:
            raise ValueError(f"duplicate particular id: {pid}")
        seen.add(pid)
        body = {
            "id": pid,
            "kind": kind,
            "text": text,
            "observable": bool(raw.get("observable", True)),
        }
        normalized.append({**body, "particularHash": _hash(body)})

    body = {
        "schema": SOURCE_SCHEMA,
        "label": label.strip(),
        "sourceLocator": source_locator,
        "particulars": normalized,
        "boundaryClaims": [
            str(x).strip() for x in boundary_claims if str(x).strip()
        ],
        "authority": "source-witness-only",
        "laws": list(LAWS),
    }
    return {**body, "id": "narrative-source:" + _hash(body)[:24]}


def staging_proposal(source: dict, beats: list[dict]) -> dict:
    _require_schema(source, SOURCE_SCHEMA)
    if not beats:
        raise ValueError("at least one staging beat is required")
    source_by_id = {row["id"]: row for row in source["particulars"]}
    normalized = []
    seen = set()

    for raw in beats:
        beat_id = str(raw.get("id") or "").strip()
        particular_id = str(raw.get("sourceParticularId") or "").strip()
        shot_type = str(raw.get("shotType") or "").strip().upper()
        staging = str(raw.get("staging") or "").strip()
        duration = round(float(raw.get("durationSeconds") or 0), 6)
        authority_claims = [
            str(x).strip()
            for x in (raw.get("authorityClaims") or [])
            if str(x).strip()
        ]

        if not beat_id or beat_id in seen:
            raise ValueError("staging beat ids must be present and unique")
        seen.add(beat_id)
        if particular_id not in source_by_id:
            raise ValueError(f"unknown source particular: {particular_id}")
        if shot_type not in SHOT_TYPES:
            raise ValueError(f"unknown Paper Director shot type: {shot_type}")
        if not staging:
            raise ValueError(f"staging is required for {beat_id}")
        if duration <= 0:
            raise ValueError(f"durationSeconds must be positive for {beat_id}")
        if authority_claims:
            raise ValueError(
                "staging cannot synthesize causal/source authority: "
                + "; ".join(authority_claims)
            )

        source_row = source_by_id[particular_id]
        normalized.append({
            "id": beat_id,
            "sourceParticularId": particular_id,
            "sourceParticularHash": source_row["particularHash"],
            "shotType": shot_type,
            "durationSeconds": duration,
            "staging": staging,
            "interpretation": (
                str(raw.get("interpretation")).strip()
                if raw.get("interpretation") is not None
                else None
            ),
            "authorityClaims": [],
        })

    body = {
        "schema": PROPOSAL_SCHEMA,
        "sourceId": source["id"],
        "beats": normalized,
        "beatCount": len(normalized),
        "authority": "proposal-only",
        "laws": list(LAWS),
    }
    return {**body, "id": "staging-proposal:" + _hash(body)[:24]}


def editorial_admission(
    proposal: dict,
    *,
    admitted_beat_ids: list[str] | tuple[str, ...],
    authority_ref: str,
    decision_note: str = "",
) -> dict:
    _require_schema(proposal, PROPOSAL_SCHEMA)
    authority_ref = str(authority_ref).strip()
    if not authority_ref:
        raise ValueError("authority_ref is required for editorial admission")

    available = {row["id"] for row in proposal["beats"]}
    admitted = []
    seen = set()
    for raw in admitted_beat_ids:
        beat_id = str(raw).strip()
        if beat_id in seen:
            continue
        if beat_id not in available:
            raise ValueError(f"cannot admit unknown beat: {beat_id}")
        seen.add(beat_id)
        admitted.append(beat_id)
    if not admitted:
        raise ValueError("at least one beat must be explicitly admitted")

    body = {
        "schema": ADMISSION_SCHEMA,
        "proposalId": proposal["id"],
        "admittedBeatIds": admitted,
        "rejectedBeatIds": [
            row["id"] for row in proposal["beats"] if row["id"] not in seen
        ],
        "authorityRef": authority_ref,
        "decisionNote": str(decision_note).strip(),
        "authority": "external-editorial-decision",
        "laws": [
            "PROPOSAL DOES NOT ADMIT ITSELF",
            "OMITTED BEAT != REJECTED SOURCE PARTICULAR",
            "EDITORIAL ADMISSION GOVERNS STAGING ONLY",
        ],
    }
    return {**body, "id": "editorial-admission:" + _hash(body)[:24]}


def performance_plan(source: dict, proposal: dict, admission: dict) -> dict:
    _require_schema(source, SOURCE_SCHEMA)
    _require_schema(proposal, PROPOSAL_SCHEMA)
    _require_schema(admission, ADMISSION_SCHEMA)
    if proposal.get("sourceId") != source.get("id"):
        raise ValueError("proposal does not belong to source")
    if admission.get("proposalId") != proposal.get("id"):
        raise ValueError("admission does not belong to proposal")

    admitted = set(admission["admittedBeatIds"])
    source_by_id = {row["id"]: row for row in source["particulars"]}
    clock = 0.0
    performed = []

    for row in proposal["beats"]:
        if row["id"] not in admitted:
            continue
        source_row = source_by_id[row["sourceParticularId"]]
        if row["sourceParticularHash"] != source_row["particularHash"]:
            raise ValueError("source particular changed after proposal")
        start = round(clock, 6)
        end = round(start + float(row["durationSeconds"]), 6)
        performed.append({
            "id": row["id"],
            "sourceParticularId": source_row["id"],
            "sourceParticularHash": source_row["particularHash"],
            "sourceText": source_row["text"],
            "type": row["shotType"],
            "start": start,
            "end": end,
            "durationSeconds": row["durationSeconds"],
            "staging": row["staging"],
            "interpretation": row["interpretation"],
            "sourceAuthority": "preserved",
            "stagingAuthority": "externally-admitted",
        })
        clock = end

    body = {
        "schema": PLAN_SCHEMA,
        "sourceId": source["id"],
        "proposalId": proposal["id"],
        "admissionId": admission["id"],
        "authorityRef": admission["authorityRef"],
        "beats": performed,
        "beatCount": len(performed),
        "durationSeconds": round(clock, 6),
        "sourceAuthority": "source-witness-only",
        "stagingAuthority": "externally-admitted",
        "receiptAuthority": "none",
        "directorVocabulary": "haunted-blender/paper-director-plan/v1::SHOT_TYPES",
        "laws": list(LAWS),
    }
    return {**body, "id": "particular-performance-plan:" + _hash(body)[:24]}


def return_receipt(plan: dict) -> dict:
    _require_schema(plan, PLAN_SCHEMA)
    body = {
        "schema": RECEIPT_SCHEMA,
        "planId": plan["id"],
        "sourceId": plan["sourceId"],
        "proposalId": plan["proposalId"],
        "admissionId": plan["admissionId"],
        "performedBeatCount": plan["beatCount"],
        "durationSeconds": plan["durationSeconds"],
        "performedParticulars": [
            {
                "beatId": row["id"],
                "sourceParticularId": row["sourceParticularId"],
                "sourceParticularHash": row["sourceParticularHash"],
            }
            for row in plan["beats"]
        ],
        "receiptAuthority": "none",
        "claims": [
            "This receipt records the admitted staging plan.",
            "It does not rewrite the narrative source.",
            "It does not assert causality beyond the source witness.",
        ],
        "laws": list(LAWS),
    }
    return {**body, "id": "particular-performance-return:" + _hash(body)[:24]}


def compile_spec(spec: dict) -> dict:
    _require_schema(spec, SPEC_SCHEMA)
    source = particular_source(
        label=spec["label"],
        source_locator=spec["sourceLocator"],
        particulars=spec["particulars"],
        boundary_claims=spec.get("boundaryClaims") or [],
    )
    proposal = staging_proposal(source, spec["beats"])
    admission = editorial_admission(
        proposal,
        admitted_beat_ids=spec["admittedBeatIds"],
        authority_ref=spec["authorityRef"],
        decision_note=spec.get("decisionNote") or "",
    )
    plan = performance_plan(source, proposal, admission)
    receipt = return_receipt(plan)
    return {
        "source": source,
        "proposal": proposal,
        "admission": admission,
        "plan": plan,
        "receipt": receipt,
    }


def read_spec(path: str | Path) -> dict:
    return json.loads(
        Path(path).expanduser().resolve(strict=True).read_text(encoding="utf-8")
    )
