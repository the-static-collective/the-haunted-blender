"""Additive, local-only alchemical scene recipes. N0 film schema is untouched."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

from . import catalog
from .project import stable_bytes

SCHEMA = "haunted-blender/alchemy-recipe/v1"
SNAPSHOT_SCHEMA = "haunted-blender/alchemy-snapshot/v1"
RELATIONS = {"shape-echo": ("source", "target"),
             "triadic-bridge": ("source", "bridge", "target")}
SEGMENT_MS = 1800
FADE_MS = 450
WIDTH, HEIGHT, FPS = 320, 180, 24


def _vault(root: Path) -> Path:
    root = root.expanduser().resolve()
    if not (root / ".haunted-blender" / "library.sqlite3").is_file():
        raise FileNotFoundError("Initialize the N0 pantry first")
    return root


def _recipe_path(root: Path, recipe_id: str) -> Path:
    if not re.fullmatch(r"alchemy-[0-9a-f]{16}", recipe_id):
        raise ValueError("Invalid alchemy recipe ID")
    return _vault(root) / "projects" / "alchemy" / (recipe_id + ".json")


def validate(recipe: dict) -> None:
    if not isinstance(recipe, dict) or recipe.get("schema") != SCHEMA:
        raise ValueError("Unknown alchemy recipe schema")
    if not isinstance(recipe.get("id"), str) or not re.fullmatch(r"alchemy-[0-9a-f]{16}", recipe["id"]):
        raise ValueError("Invalid alchemy recipe ID")
    relation = recipe.get("relation")
    if relation not in RELATIONS:
        raise ValueError("Unknown relation; no inferred meaning is promoted")
    roles = RELATIONS[relation]
    assets = recipe.get("assets")
    if not isinstance(assets, dict) or set(assets) != set(roles):
        raise ValueError("A relation must have exactly its declared participants")
    if any(not isinstance(v, str) or not re.fullmatch(r"asset-[0-9a-f]{24}", v) for v in assets.values()):
        raise ValueError("All participants must refer to cataloged asset IDs")
    if len(set(assets.values())) != len(roles):
        raise ValueError("Participants must be distinct source records")
    order = recipe.get("order")
    if not isinstance(order, list) or len(order) != len(roles) or set(order) != set(roles):
        raise ValueError("Order must contain every participant exactly once")
    statement = recipe.get("statement")
    if not isinstance(statement, str) or not 1 <= len(statement.strip()) <= 500:
        raise ValueError("Artist statement must be 1–500 characters")
    if recipe.get("evidence_class") != "artist_proposed":
        raise ValueError("Creative relationship must remain artist-proposed, not witnessed fact")
    if recipe.get("segment_ms") != SEGMENT_MS or recipe.get("fade_ms") != FADE_MS:
        raise ValueError("Unknown timing contract")


def create(root: Path, source: str, target: str, *, bridge: str | None = None,
           relation: str = "shape-echo", order: list[str] | None = None,
           statement: str = "Artist-proposed visual relationship") -> dict:
    roles = RELATIONS.get(relation)
    if roles is None:
        raise ValueError("Unknown relation")
    assets = {"source": source, "target": target}
    if bridge is not None:
        assets["bridge"] = bridge
    recipe = {
        "schema": SCHEMA, "id": "alchemy-" + uuid.uuid4().hex[:16],
        "relation": relation, "assets": assets,
        "order": list(roles) if order is None else list(order),
        "statement": statement,
        "evidence_class": "artist_proposed",
        "segment_ms": SEGMENT_MS, "fade_ms": FADE_MS,
    }
    validate(recipe)
    con = catalog.connect(_vault(root))
    try:
        for role, asset_id in assets.items():
            original = con.execute("SELECT * FROM assets WHERE id=?", (asset_id,)).fetchone()
            if original is None:
                raise ValueError("Uncataloged " + role + " asset: " + asset_id)
            catalog.source_for_render(con, asset_id)
    finally:
        con.close()
    path = _recipe_path(root, recipe["id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(recipe, handle, sort_keys=True, indent=2)
        handle.write("\n")
    return recipe


def _observed_source(row) -> dict:
    path = Path(row["path"])
    if not path.is_file() or catalog.digest_file(path) != row["sha256"]:
        raise ValueError("Source missing or changed since cataloging: " + str(path))
    return {"id": row["id"], "path": str(path), "sha256": row["sha256"],
            "rights": row["rights"], "kind": row["kind"]}


def freeze(root: Path, recipe_id: str) -> Path:
    """Freeze the resolved derivative as well as the requested source; later reassociation cannot alter this recipe."""
    root = _vault(root)
    recipe = json.loads(_recipe_path(root, recipe_id).read_text(encoding="utf-8"))
    validate(recipe)
    if recipe["id"] != recipe_id:
        raise ValueError("Recipe ID differs from path")
    con = catalog.connect(root)
    try:
        sources = {}
        for role, asset_id in recipe["assets"].items():
            original = con.execute("SELECT * FROM assets WHERE id=?", (asset_id,)).fetchone()
            if original is None:
                raise ValueError("Missing original catalog record: " + asset_id)
            frame = catalog.source_for_render(con, asset_id)
            sources[role] = {"requested": _observed_source(original),
                             "frame": _observed_source(frame)}
    finally:
        con.close()
    bundle = {"schema": SNAPSHOT_SCHEMA, "recipe": recipe, "sources": sources,
              "nonclaims": ["Artist-proposed relation is not a witnessed physical fact",
                            "No visual or semantic continuity has been independently verified",
                            "No model-generated or camera-inferred pixels are asserted as observed"]}
    payload = stable_bytes(bundle) + b"\n"
    digest = hashlib.sha256(stable_bytes(bundle)).hexdigest()
    dest_dir = root / "snapshots" / "alchemy" / recipe_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / (digest + ".json")
    try:
        with dest.open("xb") as handle:
            handle.write(payload)
    except FileExistsError:
        if dest.read_bytes() != payload:
            raise ValueError("Existing alchemy snapshot has changed")
    return dest


def _load_snapshot(root: Path, snapshot: Path) -> tuple[dict, str]:
    root = _vault(root)
    path = snapshot.expanduser().resolve(strict=True)
    base = root / "snapshots" / "alchemy"
    if base not in path.parents:
        raise ValueError("Alchemy snapshot must reside inside its local vault")
    bundle = json.loads(path.read_text(encoding="utf-8"))
    if bundle.get("schema") != SNAPSHOT_SCHEMA:
        raise ValueError("Unknown alchemy snapshot schema")
    recipe = bundle["recipe"]
    validate(recipe)
    digest = hashlib.sha256(stable_bytes(bundle)).hexdigest()
    if path.name != digest + ".json" or path.parent.name != recipe["id"] or path.parent.parent != base:
        raise ValueError("Alchemy snapshot hash or identity mismatch")
    if set(bundle.get("sources", {})) != set(recipe["assets"]):
        raise ValueError("Snapshot source participant mismatch")
    for role, entry in bundle["sources"].items():
        if entry["requested"]["id"] != recipe["assets"][role]:
            raise ValueError("Snapshot requested source differs from recipe")
        if entry["requested"]["kind"] != "raw" and entry["requested"] != entry["frame"]:
            raise ValueError("Only a RAW may resolve to a separate renderable derivative")
        if entry["frame"]["kind"] != "image" or Path(entry["frame"]["path"]).suffix.lower() not in catalog.DISPLAYABLE:
            raise ValueError("Snapshot frame is not a renderable still")
    return bundle, digest


def plan(root: Path, snapshot: Path) -> dict:
    bundle, digest = _load_snapshot(root, snapshot)
    recipe = bundle["recipe"]
    for entry in bundle["sources"].values():
        for source in (entry["requested"], entry["frame"]):
            if not Path(source["path"]).is_file() or catalog.digest_file(Path(source["path"])) != source["sha256"]:
                raise ValueError("Frozen source missing or changed: " + source["path"])
    segments = []
    for index, role in enumerate(recipe["order"]):
        source = bundle["sources"][role]
        segments.append({"index": index, "role": role,
                         "requested_asset_id": source["requested"]["id"],
                         "frame_asset_id": source["frame"]["id"],
                         "path": source["frame"]["path"],
                         "sha256": source["frame"]["sha256"]})
    duration = len(segments) * SEGMENT_MS - (len(segments) - 1) * FADE_MS
    return {
        "schema": "haunted-blender/alchemy-plan/v1",
        "snapshot_sha256": digest, "recipe_id": recipe["id"],
        "relation": recipe["relation"], "evidence_class": recipe["evidence_class"],
        "statement": recipe["statement"], "segments": segments,
        "segment_ms": SEGMENT_MS, "fade_ms": FADE_MS, "duration_ms": duration,
        "width": WIDTH, "height": HEIGHT, "fps": FPS,
        "adapter": "ffmpeg-alchemy-crossfade/v1", "audio": "none",
        "checks": {"participant_presence": "validated",
                   "source_hashes": "validated",
                   "visual_relation": "not_assessed",
                   "semantic_continuity": "not_assessed"},
        "nonclaims": bundle["nonclaims"],
    }


def render(root: Path, snapshot: Path, out: Path) -> dict:
    spec = plan(root, snapshot)
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("FFmpeg is needed to render; alchemy plan works without it")
    out = out.expanduser().resolve()
    receipt_path = out.with_suffix(out.suffix + ".receipt.json")
    if out.exists() or receipt_path.exists():
        raise FileExistsError("Will not overwrite an existing render or receipt")
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="blender-alchemy-") as folder:
        staging = Path(folder) / "result.mp4"
        cmd = [ffmpeg, "-nostdin", "-v", "error", "-y"]
        seconds = SEGMENT_MS / 1000
        for segment in spec["segments"]:
            cmd += ["-loop", "1", "-framerate", str(FPS), "-t", str(seconds),
                    "-i", segment["path"]]
        filters = []
        for i in range(len(spec["segments"])):
            filters.append(
                "[" + str(i) + ":v]scale=" + str(WIDTH) + ":" + str(HEIGHT)
                + ":force_original_aspect_ratio=decrease:flags=lanczos,"
                + "pad=" + str(WIDTH) + ":" + str(HEIGHT)
                + ":(ow-iw)/2:(oh-ih)/2,setsar=1,fps=" + str(FPS)
                + ",settb=AVTB,setpts=PTS-STARTPTS,format=yuv420p[v" + str(i) + "]"
            )
        previous = "v0"
        for i in range(1, len(spec["segments"])):
            next_name = "joined" + str(i)
            offset = i * (SEGMENT_MS - FADE_MS) / 1000
            filters.append("[" + previous + "][v" + str(i)
                           + "]xfade=transition=fade:duration=" + str(FADE_MS / 1000)
                           + ":offset=" + str(offset) + "[" + next_name + "]")
            previous = next_name
        cmd += ["-filter_complex", ";".join(filters), "-map", "[" + previous + "]",
                "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-movflags", "+faststart", str(staging)]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Revalidate the frozen requested original AND derivative before issuing a completion receipt.
        plan(root, snapshot)
        shutil.copyfile(staging, out)
    receipt = {
        "schema": "haunted-blender/alchemy-receipt/v1", "status": "scoped_complete",
        "claim": "Deterministic silent still-image crossfade; not a verified semantic metamorphosis",
        "snapshot_sha256": spec["snapshot_sha256"], "recipe_id": spec["recipe_id"],
        "relation": spec["relation"], "evidence_class": spec["evidence_class"],
        "adapter": spec["adapter"], "segments": [
            {"role": x["role"], "asset_id": x["requested_asset_id"],
             "rendered_sha256": x["sha256"]} for x in spec["segments"]],
        "output_path": str(out), "output_sha256": catalog.digest_file(out),
        "nonclaims": spec["nonclaims"],
    }
    temp = receipt_path.with_suffix(receipt_path.suffix + ".tmp")
    try:
        with temp.open("x", encoding="utf-8") as handle:
            handle.write(stable_bytes(receipt).decode("utf-8") + "\n")
        os.replace(temp, receipt_path)
    except Exception:
        out.unlink(missing_ok=True)
        temp.unlink(missing_ok=True)
        raise
    return receipt
