"""SCENE-WEAVE-001: additive, artist-authorized fictional scene composition.

The Alchemical Compiler is read-only material input. Film/v1, alchemy recipes,
renderers, and indexed photographs are not modified by this module.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import uuid
from pathlib import Path

from .project import stable_bytes

WORLD = "haunted-blender/scene-world/v0"
PROPOSALS = "haunted-blender/cinematic-proposals/v0"
STORY = "haunted-blender/story-branch-proposal/v0"
AUTHOR = "filmmaker_established"


def demand(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(value):
    return hashlib.sha256(stable_bytes(value)).hexdigest()


def validate(world):
    demand(isinstance(world, dict) and world.get("schema") == WORLD, "Unknown world schema")
    demand(re.fullmatch(r"world-[0-9a-f]{16}", world.get("id", "")), "Invalid world ID")
    demand(world.get("mode") == "fiction", "Only explicitly fictional worlds are supported")
    demand(isinstance(world.get("title"), str) and world["title"].strip(), "Missing world title")
    material = world.get("material", {})
    demand(re.fullmatch(r"[0-9a-f]{64}", material.get("alchemy_snapshot_sha256", "")),
           "Missing frozen alchemy source hash")
    roles = material.get("roles")
    demand(isinstance(roles, list) and len(roles) in (2, 3), "Expected two or three alchemy roles")
    demand(len({r.get("role") for r in roles}) == len(roles), "Duplicate material roles")
    for role in roles:
        demand(isinstance(role.get("requested_asset_id"), str), "Missing original asset ID")
        demand(re.fullmatch(r"[0-9a-f]{64}", role.get("frame_sha256", "")), "Missing rendered-frame digest")
    keys = ("entities", "facts", "beats", "knowledge", "relations", "affordances", "questions")
    demand(all(isinstance(world.get(k), list) for k in keys), "Missing authored world collections")
    for kind in keys:
        rows = world[kind]
        demand(all(isinstance(x, dict) and isinstance(x.get("id"), str) for x in rows),
               "Malformed " + kind)
        ids = [x["id"] for x in rows]
        demand(len(ids) == len(set(ids)), "Duplicate " + kind + " IDs")
    entities = {e["id"]: e for e in world["entities"]}
    facts = {f["id"]: f for f in world["facts"]}
    character_ids = {e["id"] for e in world["entities"] if e.get("kind") == "character"}
    for entity in world["entities"]:
        demand(entity.get("kind") in ("character", "prop", "location"), "Unknown entity kind")
        demand(entity.get("basis") == AUTHOR, "Entity requires filmmaker attestation")
        demand(not any(k in entity for k in ("face_embedding", "biometric_id", "inferred_real_identity")),
               "Automated person identification is not part of this scaffold")
    demand([b.get("index") for b in world["beats"]] == list(range(len(world["beats"]))),
           "Beats must be ordered from zero")
    for fact in world["facts"]:
        demand(fact.get("subject") in entities and fact.get("basis") == AUTHOR,
               "Fact needs an established fictional entity")
        demand(isinstance(fact.get("predicate"), str) and isinstance(fact.get("value"), str),
               "Malformed fact")
        time = fact.get("since_beat")
        demand(type(time) is int and 0 <= time <= len(world["beats"]), "Invalid fact beat")
        if "supersedes" in fact:
            previous = facts.get(fact["supersedes"])
            demand(previous is not None and previous["id"] != fact["id"], "Unknown prior fact")
            demand(time > previous["since_beat"], "A new occurrence cannot rewrite the past")
    for item in world["knowledge"]:
        demand(item.get("observer") in character_ids | {"audience"}, "Unknown knowledge observer")
        demand(item.get("fact_id") in facts and item.get("basis") == AUTHOR,
               "Knowledge cannot be inferred or refer to an undeclared fact")
        at = item.get("since_beat")
        demand(type(at) is int and facts[item["fact_id"]]["since_beat"] <= at <= len(world["beats"]),
               "Knowledge precedes its fact or exceeds the story")
    for relation in world["relations"]:
        demand(relation.get("from") in entities and relation.get("to") in entities
               and relation.get("basis") == AUTHOR, "Unestablished or dangling relation")
    for action in world["affordances"]:
        demand(action.get("actor") in character_ids and action.get("object") in entities,
               "Affordance must identify a character and a known entity")
        prereq = action.get("requires_fact_ids")
        demand(isinstance(prereq, list) and all(x in facts for x in prereq),
               "Affordance has an undeclared prerequisite")
        demand(action.get("status") == "proposed", "An affordance is not an occurrence")
    for question in world["questions"]:
        demand(isinstance(question.get("text"), str) and question.get("status") == "open",
               "A question is not automatically answered")


def _path(root, world_id):
    demand(re.fullmatch(r"world-[0-9a-f]{16}", world_id), "Invalid world ID")
    return Path(root).expanduser().resolve() / "projects" / "scene-weave" / (world_id + ".json")


def from_alchemy(root, alchemy_snapshot, authored):
    """The existing alchemy.plan validates its own frozen source/derivative hashes."""
    from . import alchemy
    plan = alchemy.plan(Path(root), Path(alchemy_snapshot))
    demand(plan.get("schema") == "haunted-blender/alchemy-plan/v1", "Unknown alchemy plan")
    demand(isinstance(authored, dict), "Story must be explicitly authored")
    fields = {"title", "entities", "facts", "beats", "knowledge", "relations",
              "affordances", "questions"}
    demand(set(authored) == fields, "Unknown or missing story fields")
    material = {
        "alchemy_snapshot_sha256": plan["snapshot_sha256"],
        "alchemy_recipe_id": plan["recipe_id"],
        "roles": [
            {"role": item["role"], "requested_asset_id": item["requested_asset_id"],
             "frame_sha256": item["sha256"]}
            for item in plan["segments"]
        ],
    }
    world = {"schema": WORLD, "id": "world-" + uuid.uuid4().hex[:16],
             "mode": "fiction", "material": material, **copy.deepcopy(authored)}
    validate(world)
    path = _path(root, world["id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(world, handle, sort_keys=True, indent=2)
        handle.write("\n")
    return {"world_id": world["id"], "path": str(path)}


def freeze(root, world_id):
    path = _path(root, world_id)
    world = json.loads(path.read_text(encoding="utf-8"))
    validate(world)
    demand(world["id"] == world_id, "World identity/path mismatch")
    digest = sha(world)
    folder = Path(root).expanduser().resolve() / "snapshots" / "scene-weave" / world_id
    folder.mkdir(parents=True, exist_ok=True)
    out = folder / (digest + ".json")
    expected = stable_bytes(world) + b"\n"
    try:
        with out.open("xb") as handle:
            handle.write(expected)
    except FileExistsError:
        demand(out.read_bytes() == expected, "Existing snapshot was changed")
    return out


def load_snapshot(root, snapshot):
    path = Path(snapshot).expanduser().resolve(strict=True)
    folder = Path(root).expanduser().resolve() / "snapshots" / "scene-weave"
    demand(path.parent.parent == folder, "Snapshot is outside its declared vault")
    world = json.loads(path.read_text(encoding="utf-8"))
    validate(world)
    demand(path.parent.name == world["id"] and path.name == sha(world) + ".json",
           "Snapshot hash or world identity mismatch")
    return world


def compose(world, beat):
    """Pure proposals: no video, audience disclosure, story admission, or source mutation."""
    validate(world)
    demand(type(beat) is int and 0 <= beat < len(world["beats"]), "Unknown beat")
    occurred = {f["id"] for f in world["facts"] if f["since_beat"] <= beat}
    audience = {k["fact_id"] for k in world["knowledge"]
                if k["observer"] == "audience" and k["since_beat"] <= beat}
    known = sorted(occurred & audience)
    withheld = sorted(occurred - audience)
    choices = []
    for name, framing, focus, possible_reveals in (
        ("wide", "establishing", "space-and-presence", []),
        ("detail", "insert", "object-and-motif", withheld),
        ("absence", "negative-space", "withheld-information", []),
    ):
        item = {"id": name, "framing": framing, "focus": focus,
                "beat": beat, "audience_fact_ids": known,
                "possible_reveals": possible_reveals, "story_patch": [],
                "knowledge_patch": [], "status": "proposal_only",
                "disclosure_gate": "explicit_filmmaker_approval"}
        item["candidate_sha256"] = sha(item)
        choices.append(item)
    actor_known = {
        e["id"]: {k["fact_id"] for k in world["knowledge"]
                  if k["observer"] == e["id"] and k["since_beat"] <= beat}
        for e in world["entities"] if e["kind"] == "character"
    }
    actions = sorted(a["id"] for a in world["affordances"]
                     if set(a["requires_fact_ids"]).issubset(occurred)
                     and set(a["requires_fact_ids"]).issubset(actor_known[a["actor"]]))
    return {"schema": PROPOSALS, "world_sha256": sha(world),
            "material_snapshot_sha256": world["material"]["alchemy_snapshot_sha256"],
            "beat": beat, "candidates": choices,
            "available_proposed_affordance_ids": actions,
            "nonclaims": ["Camera proposals do not establish actual events or audience knowledge",
                          "Fictional persons are not inferred identities of photograph subjects",
                          "No scene quality, causal reality or visual continuity is certified"]}


def propose_branch(world, *, source_fact_id, new_fact, knowledge_additions=None):
    """A proposed later state is an appended fact, not a rewrite of old history."""
    validate(world)
    facts = {f["id"]: f for f in world["facts"]}
    old = facts.get(source_fact_id)
    demand(old is not None, "Unknown branch ancestor")
    demand(new_fact.get("supersedes") == source_fact_id
           and new_fact.get("subject") == old["subject"]
           and new_fact.get("predicate") == old["predicate"]
           and new_fact.get("value") != old["value"], "Branch changes the wrong fact")
    new_world = copy.deepcopy(world)
    new_world["facts"].append(copy.deepcopy(new_fact))
    new_world["knowledge"].extend(copy.deepcopy(knowledge_additions or []))
    validate(new_world)
    proposal = {"schema": STORY, "source_world_sha256": sha(world), "status": "proposed",
                "patch": {"source_fact_id": source_fact_id,
                          "new_fact": copy.deepcopy(new_fact),
                          "knowledge_additions": copy.deepcopy(knowledge_additions or [])}}
    proposal["proposal_sha256"] = sha(proposal)
    return proposal


def approve_branch(world, proposal, *, filmmaker_approval=False):
    validate(world)
    demand(filmmaker_approval is True, "Explicit filmmaker approval required")
    demand(proposal.get("schema") == STORY and proposal.get("status") == "proposed",
           "Unknown branch proposal")
    demand(proposal.get("source_world_sha256") == sha(world), "Stale branch proposal")
    digest = proposal.get("proposal_sha256")
    unsigned = copy.deepcopy(proposal)
    unsigned.pop("proposal_sha256", None)
    demand(digest == sha(unsigned), "Branch proposal was tampered with")
    patch = proposal["patch"]
    demand(propose_branch(world, source_fact_id=patch["source_fact_id"],
                          new_fact=patch["new_fact"],
                          knowledge_additions=patch["knowledge_additions"]) == proposal,
           "Branch operation mismatch")
    child = copy.deepcopy(world)
    child["id"] = "world-" + uuid.uuid4().hex[:16]
    child["parent_sha256"] = sha(world)
    child["facts"].append(copy.deepcopy(patch["new_fact"]))
    child["knowledge"].extend(copy.deepcopy(patch["knowledge_additions"]))
    child["approval"] = {"decision": "approved_by_filmmaker", "proposal_sha256": digest}
    validate(child)
    return child


def save_child(root, child):
    validate(child)
    demand(child.get("approval", {}).get("decision") == "approved_by_filmmaker"
           and re.fullmatch(r"[0-9a-f]{64}", child.get("parent_sha256", "")),
           "A child requires a declared approval and parent")
    path = _path(root, child["id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(child, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return path
