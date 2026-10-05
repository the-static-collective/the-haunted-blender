"""DREAMBREEDER 003 — deterministic possibility families, explicit ghosts,
and multi-parent cinematic descendants without collapsed ancestry.

Nothing in this module renders or publishes a film. It models proposal ecology and
lineage around already-addressed material.
"""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Iterable

ECOLOGY_SCHEMA = "haunted-blender/dream-ecology/v1"
DESCENDANT_SCHEMA = "haunted-blender/dream-descendant/v1"
GHOST_SCHEMA = "haunted-blender/ghost-influence/v1"
RECOMBINATION_SCHEMA = "haunted-blender/dream-recombination/v1"

_RECIPES = (
    {
        "label": "Late Bloom",
        "invitation": "late-bloom",
        "worldPatch": {"surface": "darkroom", "transition": "slow-assembly", "awakening": "portal"},
        "motionGrammar": ["hold", "drift-up", "open-late"],
        "traits": ["late-bloom", "restraint"],
    },
    {
        "label": "Hinge Weather",
        "invitation": "hinge-weather",
        "worldPatch": {"physical": "postcard", "transition": "hinge-weather"},
        "motionGrammar": ["hinge", "wind", "parallax"],
        "traits": ["threshold", "weather"],
    },
    {
        "label": "Ghost Negative",
        "invitation": "ghost-negative",
        "worldPatch": {"surface": "dossier", "awakening": "doorway"},
        "motionGrammar": ["freeze", "echo", "misregister"],
        "traits": ["ghost", "residue"],
    },
    {
        "label": "Room From Difference",
        "invitation": "room-from-difference",
        "worldPatch": {"physical": "field-notes", "transition": "room-assembly"},
        "motionGrammar": ["separate", "answer", "assemble"],
        "traits": ["relation-diverged", "room"],
    },
    {
        "label": "Stained Memory",
        "invitation": "stained-memory",
        "worldPatch": {"physical": "polaroid", "surface": "stained-glass"},
        "motionGrammar": ["layer", "backlight", "return"],
        "traits": ["memory", "relation-shared"],
    },
    {
        "label": "Cardboard Ascension",
        "invitation": "cardboard-ascension",
        "worldPatch": {"physical": "cutout-theater", "transition": "vertical-stage"},
        "motionGrammar": ["step", "raise-world", "reveal-sky"],
        "traits": ["cutout", "ascent"],
    },
)


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _hash(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _require_id(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string.")
    return value


def _unique_strings(values: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen = set()
    for value in values:
        value = _require_id(value, "identity")
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def create_ecology(
    *,
    relation_id: str,
    common_checkpoint_id: str,
    source_receipt_ids: list[str],
    generation: int = 1,
    donor_ids: list[str] | None = None,
) -> dict:
    relation_id = _require_id(relation_id, "relation_id")
    common_checkpoint_id = _require_id(common_checkpoint_id, "common_checkpoint_id")
    receipts = _unique_strings(source_receipt_ids)
    if len(receipts) < 1:
        raise ValueError("At least one source receipt is required.")
    if not isinstance(generation, int) or generation < 1:
        raise ValueError("generation must be a positive integer.")
    donors = _unique_strings(donor_ids or [])

    seed_body = {
        "relationId": relation_id,
        "commonCheckpointId": common_checkpoint_id,
        "sourceReceiptIds": sorted(receipts),
        "generation": generation,
        "donorIds": sorted(donors),
    }
    seed = _hash(seed_body)
    offset = int(seed[:8], 16) % len(_RECIPES)

    proposals = []
    for slot in range(6):
        recipe = copy.deepcopy(_RECIPES[(offset + slot) % len(_RECIPES)])
        donor = donors[(int(seed[8 + slot * 2: 10 + slot * 2], 16) % len(donors))] if donors else None
        core = {
            "slot": slot + 1,
            "invitation": recipe["invitation"],
            "seed": seed,
            "donorId": donor,
        }
        proposals.append(
            {
                "id": f"dream-proposal:{_hash(core)[:24]}",
                "slot": slot + 1,
                "authorityClass": "proposal",
                "label": recipe["label"],
                "invitation": recipe["invitation"],
                "worldPatch": recipe["worldPatch"],
                "motionGrammar": recipe["motionGrammar"],
                "traits": recipe["traits"],
                "donorId": donor,
            }
        )

    capsule = {
        "id": f"dream-haunt-capsule:{seed[:24]}",
        "kind": "static-collective/causal-capsule/v1",
        "authorityClass": "influence-only",
        "originRelationId": relation_id,
        "sourceReceiptIds": sorted(receipts),
        "sourceCheckpointId": common_checkpoint_id,
        "surface": "possibility-search",
        "invitation": "difference-without-collapse",
    }

    body = {
        "schema": ECOLOGY_SCHEMA,
        "relationId": relation_id,
        "commonCheckpointId": common_checkpoint_id,
        "generation": generation,
        "capsule": capsule,
        "proposals": proposals,
        "disposition": None,
        "ghostCandidates": [],
    }
    return {**body, "id": f"dream-ecology:{_hash(body)[:24]}"}


def _validate_ecology(ecology: dict) -> dict:
    if not isinstance(ecology, dict) or ecology.get("schema") != ECOLOGY_SCHEMA:
        raise ValueError("Unsupported dream ecology.")
    if ecology.get("disposition") is not None:
        raise ValueError("Dream ecology is already resolved.")
    proposals = ecology.get("proposals")
    if not isinstance(proposals, list) or len(proposals) != 6:
        raise ValueError("Dream ecology must contain exactly six proposals.")
    return ecology


def scrape_ecology(ecology: dict) -> dict:
    ecology = copy.deepcopy(_validate_ecology(ecology))
    ecology["disposition"] = {
        "kind": "SCRAPE",
        "authorityClass": "search-resolution",
        "negativePreferenceModel": False,
        "createsHistory": False,
        "createsGhostInfluence": False,
    }
    ecology["ghostCandidates"] = []
    return ecology


def keep_proposal(ecology: dict, proposal_id: str) -> dict:
    ecology = copy.deepcopy(_validate_ecology(ecology))
    proposal = next((p for p in ecology["proposals"] if p["id"] == proposal_id), None)
    if proposal is None:
        raise ValueError("Proposal does not belong to this ecology.")

    descendant_core = {
        "schema": DESCENDANT_SCHEMA,
        "parentCheckpointId": ecology["commonCheckpointId"],
        "sourceEcologyId": ecology["id"],
        "keptProposalId": proposal["id"],
        "relationId": ecology["relationId"],
        "worldPatch": proposal["worldPatch"],
        "motionGrammar": proposal["motionGrammar"],
        "traits": proposal["traits"],
        "donorId": proposal["donorId"],
        "authorityClass": "continuation-permission",
        "status": "unrendered-descendant",
    }
    descendant = {**descendant_core, "id": f"dream-descendant:{_hash(descendant_core)[:24]}"}

    ghost_candidates = [
        {
            "proposalId": p["id"],
            "label": p["label"],
            "invitation": p["invitation"],
            "sourceEcologyId": ecology["id"],
            "state": "inert-unselected-possibility",
        }
        for p in ecology["proposals"]
        if p["id"] != proposal["id"]
    ]

    ecology["disposition"] = {
        "kind": "KEEP",
        "proposalId": proposal["id"],
        "authorityClass": "continuation-permission",
        "resultDescendantId": descendant["id"],
        "createsHistory": False,
    }
    ecology["ghostCandidates"] = ghost_candidates
    return {"ecology": ecology, "descendant": descendant}


def admit_ghost(ecology: dict, proposal_id: str, *, local_note: str = "") -> dict:
    if not isinstance(ecology, dict) or ecology.get("schema") != ECOLOGY_SCHEMA:
        raise ValueError("Unsupported dream ecology.")
    disposition = ecology.get("disposition") or {}
    if disposition.get("kind") != "KEEP":
        raise ValueError("Ghosts may only be admitted from an explicitly resolved KEEP family.")
    candidate = next(
        (g for g in ecology.get("ghostCandidates", []) if g.get("proposalId") == proposal_id),
        None,
    )
    if candidate is None:
        raise ValueError("Proposal is not an inert ghost candidate in this ecology.")

    proposal = next(p for p in ecology["proposals"] if p["id"] == proposal_id)
    core = {
        "schema": GHOST_SCHEMA,
        "sourceEcologyId": ecology["id"],
        "sourceProposalId": proposal["id"],
        "authorityClass": "influence-only",
        "historicalAncestry": False,
        "worldPatch": proposal["worldPatch"],
        "motionGrammar": proposal["motionGrammar"],
        "traits": proposal["traits"],
        "donorId": proposal["donorId"],
        "localNote": str(local_note),
    }
    return {**core, "id": f"dream-ghost:{_hash(core)[:24]}"}


def resolve_descendant(descendant: dict, *, receipt_id: str, performance_id: str) -> dict:
    if not isinstance(descendant, dict) or descendant.get("schema") != DESCENDANT_SCHEMA:
        raise ValueError("Unsupported dream descendant.")
    if descendant.get("status") != "unrendered-descendant":
        raise ValueError("Descendant is not awaiting resolution.")
    result = copy.deepcopy(descendant)
    result["receiptId"] = _require_id(receipt_id, "receipt_id")
    result["performanceId"] = _require_id(performance_id, "performance_id")
    result["status"] = "resolved-execution"
    result["authorityClass"] = "resolved-execution"
    result["resolvedIdentity"] = _hash(
        {
            "descendantId": result["id"],
            "receiptId": result["receiptId"],
            "performanceId": result["performanceId"],
        }
    )
    return result


def recombine(
    left: dict,
    right: dict,
    *,
    local_label: str,
    ghost_influences: list[dict] | None = None,
) -> dict:
    for side, label in ((left, "left"), (right, "right")):
        if not isinstance(side, dict) or side.get("schema") != DESCENDANT_SCHEMA:
            raise ValueError(f"{label} parent is not a dream descendant.")
        if side.get("status") != "resolved-execution":
            raise ValueError("Recombination requires two resolved descendants.")
    if left["id"] == right["id"]:
        raise ValueError("Recombination requires two distinct parents.")

    ghosts = ghost_influences or []
    ghost_ids = []
    for ghost in ghosts:
        if not isinstance(ghost, dict) or ghost.get("schema") != GHOST_SCHEMA:
            raise ValueError("Recombination ghost influence has an unsupported schema.")
        if ghost.get("authorityClass") != "influence-only" or ghost.get("historicalAncestry") is not False:
            raise ValueError("Ghost influence cannot become historical ancestry.")
        ghost_ids.append(ghost["id"])

    parent_ids = sorted([left["id"], right["id"]])
    receipt_ids = sorted([left["receiptId"], right["receiptId"]])
    core = {
        "schema": RECOMBINATION_SCHEMA,
        "label": _require_id(local_label, "local_label"),
        "parents": [
            {"descendantId": parent_ids[0], "role": "co-parent"},
            {"descendantId": parent_ids[1], "role": "co-parent"},
        ],
        "observedReceiptIds": receipt_ids,
        "ghostInfluenceIds": sorted(ghost_ids),
        "authorityClass": "proposal",
        "canonicalParent": None,
        "inheritsParentAuthority": False,
        "status": "fresh-child-proposal",
        "laws": [
            "FORK != CONFLICT",
            "RECOMBINATION != CANONIZATION",
            "MULTIPLE CAUSES != ONE COLLAPSED HISTORY",
            "GHOST INFLUENCE != HISTORICAL ANCESTRY",
        ],
    }
    return {**core, "id": f"dream-child:{_hash(core)[:24]}"}
