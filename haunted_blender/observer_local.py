"""Observer-local cinematic projection.

The camera is treated as an explicit observer: it never changes the authored
world, only which already-authored facts are available, focused, withheld, or
remembered from this point of view. Receipts record the observation and memory
state so later visual adapters can respond without claiming that presentation
changed occurrence.
"""
from __future__ import annotations

import hashlib
import json

PROJECTION_SCHEMA = "haunted-blender/observer-local-projection/v0"
RECEIPT_SCHEMA = "haunted-blender/observer-memory-receipt/v0"
MATRIX_SCHEMA = "haunted-blender/observer-door-matrix/v0"


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _stable_bytes(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def _sha(value):
    return hashlib.sha256(_stable_bytes(value)).hexdigest()


def _world_facts(world):
    _require(isinstance(world, dict), "World must be an object")
    facts = world.get("facts")
    beats = world.get("beats")
    _require(isinstance(facts, list) and isinstance(beats, list) and beats,
             "World requires facts and one or more beats")
    indexed = {}
    for fact in facts:
        _require(isinstance(fact, dict) and isinstance(fact.get("id"), str),
                 "Malformed fact")
        _require(type(fact.get("since_beat")) is int,
                 "Fact requires integer since_beat")
        _require(fact["id"] not in indexed, "Duplicate fact id")
        indexed[fact["id"]] = fact
    return indexed, len(beats)


def _observer(observer, facts):
    _require(isinstance(observer, dict), "Observer must be an object")
    required = {"id", "position", "access_fact_ids", "focus_fact_ids",
                "threshold_rules"}
    _require(set(observer) == required, "Observer fields do not match contract")
    _require(isinstance(observer["id"], str) and observer["id"],
             "Observer needs an id")
    _require(isinstance(observer["position"], str) and observer["position"],
             "Observer needs a position")
    access = observer["access_fact_ids"]
    focus = observer["focus_fact_ids"]
    rules = observer["threshold_rules"]
    _require(isinstance(access, list) and isinstance(focus, list)
             and isinstance(rules, list), "Observer collections must be lists")
    _require(len(access) == len(set(access)) and len(focus) == len(set(focus)),
             "Observer fact ids must be unique")
    _require(all(x in facts for x in access + focus),
             "Observer references an unknown fact")
    normalized_rules = []
    seen = set()
    for rule in rules:
        _require(isinstance(rule, dict)
                 and set(rule) == {"threshold_id", "fact_id", "min_open"},
                 "Malformed threshold rule")
        _require(isinstance(rule["threshold_id"], str) and rule["threshold_id"],
                 "Threshold rule needs an id")
        _require(rule["fact_id"] in facts, "Threshold rule references unknown fact")
        _require(type(rule["min_open"]) in (int, float)
                 and not isinstance(rule["min_open"], bool)
                 and 0.0 <= float(rule["min_open"]) <= 1.0,
                 "min_open must be between 0 and 1")
        key = (rule["threshold_id"], rule["fact_id"])
        _require(key not in seen, "Duplicate threshold rule")
        seen.add(key)
        normalized_rules.append({**rule, "min_open": float(rule["min_open"])})
    available = set(access) | {r["fact_id"] for r in normalized_rules}
    _require(set(focus).issubset(available),
             "Focused facts must be inside the observer's authored field")
    return access, focus, normalized_rules


def _thresholds(threshold_state):
    _require(isinstance(threshold_state, dict), "Threshold state must be an object")
    clean = {}
    for key, value in threshold_state.items():
        _require(isinstance(key, str) and key, "Threshold id must be a string")
        _require(type(value) in (int, float) and not isinstance(value, bool)
                 and 0.0 <= float(value) <= 1.0,
                 "Threshold openness must be between 0 and 1")
        clean[key] = float(value)
    return clean


def _prior(prior_receipt, observer_id, world_sha, beat, occurred):
    if prior_receipt is None:
        return set()
    _require(isinstance(prior_receipt, dict)
             and prior_receipt.get("schema") == RECEIPT_SCHEMA,
             "Unknown prior memory receipt")
    _require(prior_receipt.get("observer_id") == observer_id,
             "Memory receipt belongs to another observer")
    _require(prior_receipt.get("world_sha256") == world_sha,
             "Memory receipt belongs to another world state")
    previous_beat = prior_receipt.get("beat")
    _require(type(previous_beat) is int and previous_beat <= beat,
             "Memory receipt cannot come from the future")
    memory = prior_receipt.get("memory_fact_ids")
    _require(isinstance(memory, list) and all(x in occurred for x in memory),
             "Memory receipt contains unavailable facts")
    return set(memory)


def project(world, beat, observer, threshold_state, prior_receipt=None):
    """Project one authored world through one camera/I-eye.

    The returned environment response is render guidance only. It does not
    mutate the world or claim that visibility changed what actually occurred.
    """
    facts, beat_count = _world_facts(world)
    _require(type(beat) is int and 0 <= beat < beat_count, "Unknown beat")
    access, focus, rules = _observer(observer, facts)
    thresholds = _thresholds(threshold_state)
    required_thresholds = {rule["threshold_id"] for rule in rules}
    _require(required_thresholds.issubset(thresholds),
             "Threshold state is missing a rule input")

    world_sha = _sha(world)
    occurred = {fid for fid, fact in facts.items() if fact["since_beat"] <= beat}
    authored_field = (set(access) | {r["fact_id"] for r in rules}) & occurred
    visible = set(access) & occurred
    for rule in rules:
        if rule["fact_id"] in occurred and thresholds[rule["threshold_id"]] >= rule["min_open"]:
            visible.add(rule["fact_id"])
    withheld = authored_field - visible
    outside_field = occurred - authored_field
    prior_memory = _prior(prior_receipt, observer["id"], world_sha, beat, occurred)
    memory = prior_memory | visible
    residue = memory - visible

    response = []
    for fid in sorted(visible):
        response.append({"fact_id": fid, "mode": "present_to_eye"})
    for fid in sorted(withheld):
        response.append({"fact_id": fid, "mode": "threshold_withheld"})
    for fid in sorted(residue):
        response.append({"fact_id": fid, "mode": "memory_residue"})

    receipt = {
        "schema": RECEIPT_SCHEMA,
        "observer_id": observer["id"],
        "observer_position": observer["position"],
        "world_sha256": world_sha,
        "beat": beat,
        "threshold_state": {k: thresholds[k] for k in sorted(thresholds)},
        "visible_fact_ids": sorted(visible),
        "memory_fact_ids": sorted(memory),
        "residual_memory_fact_ids": sorted(residue),
        "nonclaims": [
            "A camera projection does not change authored occurrence",
            "Visibility does not establish that a human audience learned a fact",
            "Memory residue is render guidance, not evidence of a new event",
        ],
    }
    receipt["receipt_sha256"] = _sha(receipt)

    result = {
        "schema": PROJECTION_SCHEMA,
        "observer_id": observer["id"],
        "observer_position": observer["position"],
        "world_sha256": world_sha,
        "beat": beat,
        "authored_field_fact_ids": sorted(authored_field),
        "visible_fact_ids": sorted(visible),
        "withheld_fact_ids": sorted(withheld),
        "outside_field_fact_ids": sorted(outside_field),
        "focus_visible_fact_ids": sorted(set(focus) & visible),
        "environment_response": response,
        "memory_receipt": receipt,
        "nonclaims": [
            "Environment response changes presentation only, not canonical world facts",
            "Facts outside the authored field are unobserved here, not false",
        ],
    }
    result["projection_sha256"] = _sha(result)
    return result


def door_matrix(world, beat, observers, threshold_id, openness_values):
    """Evaluate independent camera/door combinations without carrying memory across cells."""
    _require(isinstance(observers, list) and observers, "Provide one or more observers")
    _require(isinstance(threshold_id, str) and threshold_id, "Door threshold id required")
    _require(isinstance(openness_values, list) and openness_values,
             "Provide one or more door openness values")
    rows = []
    for observer in observers:
        for openness in openness_values:
            projection = project(world, beat, observer, {threshold_id: openness})
            rows.append({
                "observer_id": projection["observer_id"],
                "position": projection["observer_position"],
                "openness": float(openness),
                "visible_fact_ids": projection["visible_fact_ids"],
                "withheld_fact_ids": projection["withheld_fact_ids"],
                "focus_visible_fact_ids": projection["focus_visible_fact_ids"],
                "projection_sha256": projection["projection_sha256"],
            })
    result = {
        "schema": MATRIX_SCHEMA,
        "world_sha256": _sha(world),
        "beat": beat,
        "threshold_id": threshold_id,
        "rows": rows,
        "nonclaims": ["Matrix cells are independent viewpoint tests; memory does not cross cells"],
    }
    result["matrix_sha256"] = _sha(result)
    return result
