"""ART × I × FACT / CONSTRUCTOR-001: typed, attributable creative recipes.

This is an additive research cartridge over an accepted Scene Artifact. A recipe,
an execution and the generated media are distinct artifacts. No existing
Alchemy, SceneWorld, film/v1, or N0 render contracts are changed.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path

from . import catalog, project, render, scene_artifact, scene_weave

SCHEMA = "haunted-blender/constructor-recipe/v0"
PLAN = "haunted-blender/construction-plan/v0"
RECEIPT = "haunted-blender/construction-receipt/v0"

# This is an intentionally closed, auditable executable registry, not a plugin
# loader and not a claim that a text prompt can implement arbitrary operators.
REGISTRY = {
    "editorial.reverse/v0": {
        "input": "accepted-scene-artifact/v0", "output": "film/v1",
        "preserves": ["film source assets", "fictional world facts", "observer knowledge",
                      "individual shot durations", "prior construction history"],
        "changes": ["presentation order of unchanged shots"],
        "execution": "local deterministic data transformation",
    },
    "editorial.hold-first/v0": {
        "input": "accepted-scene-artifact/v0", "output": "film/v1",
        "preserves": ["film source assets", "fictional world facts", "observer knowledge",
                      "presentation order", "prior construction history"],
        "changes": ["duration of the current first shot"],
        "execution": "local deterministic data transformation",
    },
}


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _root(root):
    return Path(root).expanduser().resolve()


def _digest(value):
    return hashlib.sha256(project.stable_bytes(value)).hexdigest()


def _path(root, digest):
    _require(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest),
             "Invalid recipe digest")
    return _root(root) / "snapshots" / "constructors" / (digest + ".json")


def _validate_steps(steps):
    _require(isinstance(steps, list) and 1 <= len(steps) <= 8,
             "A recipe needs one to eight typed constructor steps")
    for step in steps:
        _require(isinstance(step, dict) and set(step) == {"constructor", "params"},
                 "A step requires constructor and params only")
        name, params = step["constructor"], step["params"]
        _require(isinstance(name, str) and name in REGISTRY,
                 "Unknown or unavailable constructor")
        _require(isinstance(params, dict), "Constructor parameters must be a map")
        if name == "editorial.reverse/v0":
            _require(params == {}, "Reverse accepts no additional parameters")
        elif name == "editorial.hold-first/v0":
            _require(set(params) == {"duration_ms"}
                     and type(params["duration_ms"]) is int
                     and 250 <= params["duration_ms"] <= 600000,
                     "Hold requires a valid duration_ms")


def _fact_scopes(root, source):
    world = scene_weave.load_snapshot(root, source["world_snapshot"])
    _require(scene_weave.sha(world) == source["world_sha256"],
             "Frozen fictional world changed")
    return {
        "fictional_world_sha256": source["world_sha256"],
        "filmmaker_established_fact_ids": sorted(x["id"] for x in world["facts"]),
        "fictional_facts_sha256": _digest(world["facts"]),
        "fictional_observer_knowledge_sha256": _digest(world["knowledge"]),
        "photographic_source_digest_set": sorted({
            (x["requested_asset_id"], x["frame_asset_id"], x["frame_sha256"])
            for x in source["shots"]
        }),
        "source_alchemy_sha256": source["alchemy_snapshot_sha256"],
        "claim_boundary": "fictional assertions are not facts about photographed people",
    }


def _prepare(root, artifact_snapshot, intent, steps):
    _validate_steps(steps)
    _require(isinstance(intent, str) and 1 <= len(intent.strip()) <= 500,
             "ART requires a 1–500 character filmmaker intention")
    path = Path(artifact_snapshot).expanduser().resolve(strict=True)
    source, source_digest = scene_artifact.load(root, path)
    _require(len(source["shots"]) >= 2, "Constructor comparisons need at least two shots")
    return {
        "schema": SCHEMA, "status": "accepted_local_private_preview",
        "art": {"filmmaker_intention": intent.strip(),
                "accepted_scene_artifact": str(path),
                "accepted_scene_artifact_sha256": source_digest},
        "i": {"steps": copy.deepcopy(steps),
              "registry": {name: REGISTRY[name] for name in sorted({
                  x["constructor"] for x in steps})},
              "selected_by": "filmmaker"},
        "fact": _fact_scopes(root, source),
        "distribution_authorized": False,
        "nonclaims": [
            "Creative intention is not measured artistic quality",
            "Film events and authored knowledge are not claims about real photographed people",
            "A recipe does not claim that a render succeeded",
            "A silent static preview cannot certify a viewer's understanding",
            "Accepted local private preview does not authorize distribution",
        ],
    }


def accept(root, artifact_snapshot, intent, steps, *, filmmaker_approval=False):
    _require(filmmaker_approval is True, "Explicit filmmaker approval required")
    root = _root(root)
    recipe = _prepare(root, artifact_snapshot, intent, steps)
    digest = _digest(recipe)
    destination = _path(root, digest)
    destination.parent.mkdir(parents=True, exist_ok=True)
    expected = project.stable_bytes(recipe) + b"\n"
    try:
        with destination.open("xb") as writer:
            writer.write(expected)
    except FileExistsError:
        _require(destination.read_bytes() == expected, "Previously accepted recipe changed")
    return {"recipe": str(destination), "recipe_sha256": digest,
            "constructor_ids": [x["constructor"] for x in steps]}


def load(root, recipe_snapshot):
    path = Path(recipe_snapshot).expanduser().resolve(strict=True)
    _require(path.parent == _root(root) / "snapshots" / "constructors",
             "Recipe is outside its private vault")
    recipe = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(recipe, dict) and recipe.get("schema") == SCHEMA
             and recipe.get("status") == "accepted_local_private_preview"
             and recipe.get("distribution_authorized") is False,
             "Unknown recipe or publication scope")
    digest = _digest(recipe)
    _require(path == _path(root, digest), "Recipe hash mismatch")
    expected = _prepare(root, recipe["art"]["accepted_scene_artifact"],
                        recipe["art"]["filmmaker_intention"], recipe["i"]["steps"])
    _require(expected == recipe, "Recipe source, facts or constructor contract changed")
    return recipe, digest


def _shots(film):
    return [{
        "scene_id": scene["id"],
        "shot_id": shot["id"],
        "frame_asset_id": shot["source_asset_id"],
        "duration_ms": shot["duration_ms"],
    } for scene in film["scenes"] for shot in scene["shots"]]


def _execute(root, recipe, digest):
    source, source_digest = scene_artifact.load(root, recipe["art"]["accepted_scene_artifact"])
    _require(source_digest == recipe["art"]["accepted_scene_artifact_sha256"],
             "Source Scene Artifact digest changed")
    film = copy.deepcopy(scene_artifact._film(source, source_digest))
    history = []
    for step in recipe["i"]["steps"]:
        before = _digest(_shots(film))
        if step["constructor"] == "editorial.reverse/v0":
            film["scenes"].reverse()
        elif step["constructor"] == "editorial.hold-first/v0":
            film["scenes"][0]["shots"][0]["duration_ms"] = step["params"]["duration_ms"]
        after = _digest(_shots(film))
        history.append({"constructor": step["constructor"], "params": copy.deepcopy(step["params"]),
                        "before_sha256": before, "after_sha256": after,
                        "change_scope": REGISTRY[step["constructor"]]["changes"],
                        "status": "recipe_step_compiled"})
    _require(len(film["scenes"]) == len(source["shots"]), "Shot count changed")
    # Existing N0 film schema/renderer remain untouched. New film identity
    # distinguishes the current construction from its accepted source.
    film["id"] = "film-" + _digest({
        "recipe_sha256": digest, "film_after": _shots(film)})[:16]
    film["creative_intent"] = recipe["art"]["filmmaker_intention"]
    film["provenance_policy"] = (
        "Private local constructor preview; fictional facts unchanged; "
        "recipe_sha256=" + digest)
    project.validate(film)
    return film, history


def plan(root, recipe_snapshot):
    recipe, digest = load(root, recipe_snapshot)
    film, history = _execute(root, recipe, digest)
    return {
        "schema": PLAN, "recipe_sha256": digest,
        "source_artifact_sha256": recipe["art"]["accepted_scene_artifact_sha256"],
        "fictional_world_sha256": recipe["fact"]["fictional_world_sha256"],
        "source_facts_sha256": recipe["fact"]["fictional_facts_sha256"],
        "film_sha256": _digest(film), "film_id": film["id"],
        "shot_sequence": _shots(film), "construction_history": history,
        "render_adapter": "ffmpeg-static-storyboard/v1",
        "status": "not_rendered",
        "distribution_authorized": False, "nonclaims": recipe["nonclaims"],
    }


def render_recipe(root, recipe_snapshot, out):
    root = _root(root)
    recipe, digest = load(root, recipe_snapshot)
    film, history = _execute(root, recipe, digest)
    out = Path(out).expanduser().resolve()
    _require(out.suffix.lower() == ".mp4" and out.parent == root / "renders",
             "Render must be an explicitly named MP4 inside the private renders folder")
    witness = out.with_suffix(out.suffix + ".construction.json")
    n0_receipt = out.with_suffix(out.suffix + ".receipt.json")
    if any(p.exists() for p in (out, witness, n0_receipt)):
        raise FileExistsError("Refusing to overwrite an existing video or receipt")
    payload = project.stable_bytes(film)
    film_digest = hashlib.sha256(payload).hexdigest()
    folder = root / "snapshots" / film["id"]
    folder.mkdir(parents=True, exist_ok=True)
    film_snapshot = folder / (film_digest + ".json")
    try:
        with film_snapshot.open("xb") as writer:
            writer.write(payload + b"\n")
    except FileExistsError:
        _require(film_snapshot.read_bytes() == payload + b"\n",
                 "Existing film snapshot has changed")
    # N0 independently verifies that every selected frame still matches its
    # catalog SHA. The accepted scene artifact independently verifies RAWs.
    n0_plan = render.plan(root, film_snapshot)
    _require([x["sha256"] for x in n0_plan["shots"]]
             == [x["frame_sha256"] for x in _source_shots_for_film(root, recipe, film)],
             "N0 renderer disagrees with approved constructor media")
    result = render.render(root, film_snapshot, out)
    _require(result["status"] == "scoped_complete"
             and result["output_sha256"] == catalog.digest_file(out)
             and result["snapshot_sha256"] == film_digest,
             "N0 execution did not complete the accepted recipe")
    receipt = {
        "schema": RECEIPT, "status": "scoped_complete",
        "recipe_sha256": digest, "source_artifact_sha256":
            recipe["art"]["accepted_scene_artifact_sha256"],
        "source_alchemy_sha256": recipe["fact"]["source_alchemy_sha256"],
        "fictional_facts_sha256": recipe["fact"]["fictional_facts_sha256"],
        "fictional_world_sha256": recipe["fact"]["fictional_world_sha256"],
        "constructor_history": history, "film_snapshot_sha256": film_digest,
        "n0_receipt_sha256": catalog.digest_file(n0_receipt),
        "output_sha256": result["output_sha256"],
        "artifact_kind": "silent-static-film-output", "distribution_authorized": False,
        "nonclaims": recipe["nonclaims"],
    }
    with witness.open("xb") as writer:
        writer.write(project.stable_bytes(receipt) + b"\n")
    return {"output": str(out), "receipt": str(witness), "recipe_sha256": digest,
            "output_sha256": result["output_sha256"], "film_snapshot_sha256": film_digest}


def _source_shots_for_film(root, recipe, film):
    source, _ = scene_artifact.load(root, recipe["art"]["accepted_scene_artifact"])
    indexed = {
        "shot-" + hashlib.sha256(
            (recipe["art"]["accepted_scene_artifact_sha256"] + ":" + str(x["beat"])).encode()
        ).hexdigest()[:16]: x
        for x in source["shots"]
    }
    result = []
    for scene in film["scenes"]:
        for shot in scene["shots"]:
            original = indexed.get(shot["id"])
            _require(original is not None and shot["source_asset_id"] == original["frame_asset_id"],
                     "A construction substituted a source frame")
            result.append(original)
    return result
