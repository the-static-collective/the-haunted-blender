"""MANGALIZE-002: later authority for exact quarantined artifacts.

No pixels are copied or transformed. Quarantine/selection never grant use.
An external later grant can admit only its named exact artifacts to 008h.
"""
from __future__ import annotations

import copy
import shutil
import tempfile
from pathlib import Path

from . import mangalize as m, manga_atlas as atlas, parts_harvester as parts

VERSION = "mangalize-002/v0"
SCHEMAS = {
    "set": "static-collective/manga-quarantine-set/v0",
    "selection": "static-collective/manga-quarantine-selection/v0",
    "grant": "static-collective/quarantined-asset-grant/v0",
    "promotion": "static-collective/manga-quarantine-promotion/v0",
}
HASH_KEYS = {"set": "quarantineSetHash", "selection": "selectionHash", "grant": "grantHash", "promotion": "promotionHash"}
KIND_MAP = {"panel": "still", "region-candidate": "crop", "quarry-candidate": "crop", "edge-mask": "mask"}
NO_AUTHORITY = {k: False for k in ("staging", "render", "publication", "animation", "sound", "externalGeneration", "finalPageAdmission")}
LAWS = [
    "ARTIFACT EXISTS != ARTIFACT MAY BE USED", "HARVESTED != REUSABLE", "QUARANTINED != REJECTED", "QUARANTINE != DELETION",
    "SELECTION != AUTHORIZATION", "USEFUL CROP != IDENTIFIED CHARACTER", "NEW GRANT != EDIT TO OLD GRANT", "NEW AUTHORITY != NEW PAST",
    "LATER AUTHORITY DOES NOT REWRITE EARLIER CUSTODY", "REUSE != DERIVATION", "DERIVATION != PUBLICATION", "DERIVATION != MOTION",
    "DERIVATION != SOUND", "SHARED SOURCE != SHARED AUTHORITY", "SHARED EVENT != SHARED LATER GRANT",
    "ANCESTRY CARRIAGE != STAGING AUTHORITY", "PROMOTED DESCENDANT RETAINS FOREIGN ANCESTRY", "PROMOTION != PUBLICATION",
    "PROMOTION != STAGING", "PROMOTION != ANIMATION", "PAGE != PANEL MAP", "PANEL MAP != SEMANTIC UNDERSTANDING",
    "HARVESTED ASSET != CHARACTER IDENTITY", "MANGALIZE != ANIMATE",
]


def seal(kind, body):
    body = copy.deepcopy(body)
    body.pop("id", None)
    body.pop(HASH_KEYS[kind], None)
    body.update(schema=SCHEMAS[kind], verb="MANGALIZE", experiment="MANGALIZE-002")
    digest = atlas._hash(body)
    return {**body, "id": "manga-quarantine-" + kind + ":" + digest[:24], HASH_KEYS[kind]: digest}


def verify_event(kind, record):
    m.require(record.get("schema") == SCHEMAS[kind] and record.get("verb") == "MANGALIZE" and record.get("experiment") == "MANGALIZE-002", "wrong quarantine event family")
    m.require(record == seal(kind, record), f"{kind} identity/hash mismatch")


def quarantine_set(source_root, ancestor_root):
    """Independently replay 001 and freeze its exact closed candidates."""
    ancestor_root = Path(ancestor_root)
    request = m.read(ancestor_root / "mangalize.request.json")
    admission = m.read(ancestor_root / "mangalize.admission.json")
    returned = m.read(ancestor_root / "mangalize.return.json")
    execution = m.read(ancestor_root / "mangalize.execution.json")
    m.require(m.verify(source_root, request, admission, ancestor_root) == returned["returnHash"], "ancestor return differs from replay")
    m.require(not any(returned["grantsCarried"].values()), "ancestor event is not closed quarantine")
    harvest = m.read(ancestor_root / "harvest/page-harvest.json")
    by_id = {n["id"]: n for n in returned["descendants"]}
    members = []
    for row in harvest["assets"]:
        m.require(row["materialAuthority"] == "quarantined-inspection-only" and
                  all(row["rights"].get(k, False) is False for k in m.GRANTS), "candidate is not quarantined")
        node = by_id[row["id"]]
        artifact = {"path": row["path"], "sha256": row["sha256"]}
        m.bound_path(ancestor_root, artifact)
        m.require(node["artifact"] == artifact and node["recipe"] == row["recipe"] and node["foreignAncestry"] == row["foreignAncestry"], "candidate differs from exact returned descendant")
        members.append({"assetId": row["id"], "sha256": row["sha256"], "kind": row["kind"], "artifact": artifact,
            "transformRecipe": row["recipe"], "foreignAncestry": row["foreignAncestry"], "eventLineage": row["eventLineage"],
            "sourceId": row["sourceId"], "sourceSha256": row["sourceSha256"], "harvestId": harvest["id"], "panelId": row["panelId"],
            "effectivePermissions": {k: False for k in m.GRANTS}, "state": "quarantined-inspection-only",
            "reason": "harvest-only arrival; no creative reuse or derivative admission"})
    members.sort(key=lambda row: row["assetId"])
    m.require(bool(members) and len({x["assetId"] for x in members}) == len(members), "exact unique quarantine members required")
    return seal("set", {"ancestorEvent": {**returned["eventLineage"], "returnHash": returned["returnHash"]},
        "foreignAncestry": returned["ancestors"], "members": members, "memberCount": len(members),
        "ancestorArtifacts": [m.binding(ancestor_root, p) for p in sorted(ancestor_root.rglob("*")) if p.is_file()],
        "authority": NO_AUTHORITY, "effectivePermissions": {k: False for k in m.GRANTS}, "laws": LAWS})


def verify_quarantine(source_root, ancestor_root, record):
    verify_event("set", record)
    m.require(record == quarantine_set(source_root, ancestor_root), "quarantine differs from independent ancestor replay")


def candidates(record, asset_ids):
    ids = list(asset_ids)
    m.require(bool(ids) and len(set(ids)) == len(ids), "explicit nonempty unique candidate identities required")
    by_id = {row["assetId"]: row for row in record["members"]}
    m.require(set(ids) <= set(by_id), "candidate outside exact quarantine set")
    return [{"assetId": asset_id, "sha256": by_id[asset_id]["sha256"]} for asset_id in sorted(ids)]


def select(record, *, asset_ids, authority_ref, reason):
    verify_event("set", record)
    m.nonempty(authority_ref)
    m.nonempty(reason)
    return seal("selection", {"quarantineSetHash": record["quarantineSetHash"], "quarantineId": record["id"],
        "ancestorEvent": record["ancestorEvent"], "foreignAncestry": record["foreignAncestry"],
        "selected": candidates(record, asset_ids), "selectingAuthority": authority_ref, "reason": reason,
        "authority": "selection-only", "effectivePermissions": {k: False for k in m.GRANTS}, "laws": LAWS})


def verify_selection(record, selection):
    verify_event("selection", selection)
    expected = select(record, asset_ids=[r["assetId"] for r in selection["selected"]],
                      authority_ref=selection["selectingAuthority"], reason=selection["reason"])
    m.require(selection == expected, "selection differs from exact quarantine identities/SHAs")


def asset_grant(record, selection, *, asset_ids, permissions, authority_ref):
    """External declaration factory; never called by select/promote/verify.

    Human/source authorization must exist before issuing a real declaration.
    Tests use explicitly fictional authorities and independent synthetic pages.
    """
    verify_selection(record, selection)
    m.grants(permissions)
    m.require(permissions["pixelHarvest"] is False, "002 cannot re-grant harvest")
    m.nonempty(authority_ref)
    m.require(authority_ref != selection["selectingAuthority"], "selection cannot authorize itself")
    bound = candidates(record, asset_ids)
    m.require({r["assetId"] for r in bound} <= {r["assetId"] for r in selection["selected"]}, "grant exceeds exact selection")
    return seal("grant", {"quarantineSetHash": record["quarantineSetHash"], "quarantineId": record["id"],
        "selectionHash": selection["selectionHash"], "ancestorEvent": record["ancestorEvent"],
        "foreignAncestry": record["foreignAncestry"], "assets": bound, "grantingAuthority": authority_ref,
        "permissions": permissions, "grantedOperations": sorted(op for op, key in m.OP_GRANT.items() if permissions[key]),
        "nonGrants": sorted(k for k in m.GRANTS if not permissions[k]),
        "basis": "later exact-asset external declaration; no inherited source or sibling permission", "laws": LAWS})


def verify_grant(record, selection, grant):
    verify_event("grant", grant)
    expected = asset_grant(record, selection, asset_ids=[r["assetId"] for r in grant["assets"]],
                           permissions=grant["permissions"], authority_ref=grant["grantingAuthority"])
    m.require(grant == expected, "grant differs from bound source/event/selection/assets")


def require_operation(grant, operation):
    verify_event("grant", grant)
    key = m.OP_GRANT.get(operation)
    m.require(key is not None and grant["permissions"][key] is True, f"{operation} is not granted")


def promote(record, selection, grant):
    verify_selection(record, selection)
    verify_grant(record, selection, grant)
    require_operation(grant, "reuse")
    require_operation(grant, "derive")
    by_id = {r["assetId"]: r for r in record["members"]}
    promoted = []
    for bound in grant["assets"]:
        row = by_id[bound["assetId"]]
        m.require(row["kind"] in KIND_MAP, "candidate kind cannot enter 008h drawer")
        body = {"assetId": row["assetId"], "sha256": row["sha256"], "artifact": row["artifact"], "kind": row["kind"],
            "transformRecipe": row["transformRecipe"], "foreignAncestry": row["foreignAncestry"],
            "mangalize001": record["ancestorEvent"], "quarantineSetHash": record["quarantineSetHash"],
            "selectionHash": selection["selectionHash"], "grantHash": grant["grantHash"],
            "effectivePermissions": grant["permissions"], "state": "reusable-derivative-candidate"}
        promoted.append({**body, "promotedLocalId": "material-authority-use:" + atlas._hash(body)[:24]})
    selected = {r["assetId"] for r in selection["selected"]}
    promoted_ids = {r["assetId"] for r in promoted}
    remaining = [{"assetId": r["assetId"], "sha256": r["sha256"], "state": r["state"],
                  "reason": "selected but not granted" if r["assetId"] in selected else "unselected sibling; no shared later authority"}
                 for r in record["members"] if r["assetId"] not in promoted_ids]
    return seal("promotion", {"quarantineSetHash": record["quarantineSetHash"], "selectionHash": selection["selectionHash"],
        "grantHash": grant["grantHash"], "ancestorEvent": record["ancestorEvent"], "foreignAncestry": record["foreignAncestry"],
        "executor": VERSION, "performedOperations": ["reuse", "derive"], "promotedAssets": promoted, "stillQuarantined": remaining,
        "artifactChanges": [], "authority": NO_AUTHORITY, "publicationStateChange": None, "laws": LAWS})


def verify_promotion(record, selection, grant, promotion):
    verify_event("promotion", promotion)
    m.require(promotion == promote(record, selection, grant), "promotion differs from independent authority reconstruction")


def promoted_drawer(record, selection, grant, promotion):
    verify_promotion(record, selection, grant, promotion)
    by_id = {r["assetId"]: r for r in record["members"]}
    rows = []
    for admitted in promotion["promotedAssets"]:
        original = by_id[admitted["assetId"]]
        event_lineage = [{"verb": "MANGALIZE", "experiment": "MANGALIZE-001", **record["ancestorEvent"]},
            {"verb": "MANGALIZE", "experiment": "MANGALIZE-002", "quarantineId": record["id"],
             "quarantineSetHash": record["quarantineSetHash"], "selectionId": selection["id"], "selectionHash": selection["selectionHash"],
             "grantId": grant["id"], "grantHash": grant["grantHash"], "promotionId": promotion["id"], "promotionHash": promotion["promotionHash"]}]
        row = {"id": original["assetId"], "admittedUseId": admitted["promotedLocalId"], "kind": KIND_MAP[original["kind"]],
            "path": original["artifact"]["path"], "sha256": original["sha256"], "sourceSha256": original["sourceSha256"],
            "harvestId": original["harvestId"], "pageAssetKind": original["kind"], "recipe": original["transformRecipe"],
            "foreignAncestry": original["foreignAncestry"], "eventLineage": event_lineage, "rights": admitted["effectivePermissions"],
            "materialAuthority": "reusable-candidate", "authority": NO_AUTHORITY}
        row["provenance"] = {"schema": "haunted-blender/material-provenance/v1",
            "artifact": {"id": row["id"], "sha256": row["sha256"], "sourceSha256": row["sourceSha256"]},
            "admittedUseId": row["admittedUseId"], "foreignAncestry": original["foreignAncestry"],
            "eventLineage": event_lineage, "originalEventLineage": original["eventLineage"],
            "transformRecipe": original["transformRecipe"], "effectivePermissions": admitted["effectivePermissions"],
            "authority": NO_AUTHORITY}
        rows.append(row)
    return parts.index_materials(rows, source_count=len({r["sourceSha256"] for r in rows}),
        harvest_ids=sorted({r["harvestId"] for r in rows}), laws=LAWS,
        metadata={"pathBase": "material-root", "artifactRootRole": "unchanged MANGALIZE-001 ancestor event",
                  "promotionHash": promotion["promotionHash"], "authority": NO_AUTHORITY})


def run(source_root, ancestor_root, record, selection, grant, out):
    verify_quarantine(source_root, ancestor_root, record)
    promotion = promote(record, selection, grant)
    drawer = promoted_drawer(record, selection, grant, promotion)
    for row in drawer["artifacts"]:
        parts.resolve_drawer_artifact(drawer, row, artifact_root=ancestor_root)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for name, value in (("quarantine-set", record), ("selection", selection), ("asset-grant", grant),
                        ("promotion", promotion), ("parts-drawer", drawer)):
        m.persist(out / (name + ".json"), value)
    m.persist(out / "TRACE.md", trace(record, selection, grant, promotion, drawer).encode())
    return promotion


def execute(source_root, ancestor_root, record, selection, grant, out):
    out = Path(out).resolve()
    for protected in (source_root, ancestor_root):
        m.require(not out.is_relative_to(Path(protected).resolve()), "promotion cannot write inside ancestor evidence")
    with tempfile.TemporaryDirectory(prefix="quarantine-release-") as td:
        candidate = Path(td) / "event"
        promotion = run(source_root, ancestor_root, record, selection, grant, candidate)
        if out.exists():
            m.require(m.tree_bytes(out) == m.tree_bytes(candidate), "quarantine promotion verification failure: persisted event differs from replay")
        else:
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(candidate, out)
    return promotion


def verify(source_root, ancestor_root, record, selection, grant, out):
    m.require(Path(out).is_dir(), "missing promotion directory")
    return execute(source_root, ancestor_root, record, selection, grant, out)["promotionHash"]


def trace(record, selection, grant=None, promotion=None, drawer=None):
    lines = ["# MANGALIZE EVENT 002", "", "ANCESTOR EVENT", "  MANGALIZE-001"]
    lines.extend(f"  {k}: {v}" for k, v in record["ancestorEvent"].items())
    lines.extend(["", "SOURCE ANCESTRY"])
    for ancestor in record["foreignAncestry"]:
        lines.extend(f"  {k}: {v}" for k, v in ancestor["locator"].items())
    lines.extend(["", "QUARANTINE", f"  {record['memberCount']} descendants", f"  {record['quarantineSetHash']}", "", "SELECTED"])
    lines.extend(f"  {r['assetId']} | SHA {r['sha256']}" for r in selection["selected"])
    lines.extend([f"  selectionHash: {selection['selectionHash']}", "  Selection grants no authority."])
    if grant is None:
        lines.extend(["", "SELECTION READY", "  GRANT REQUIRED: exact selected descendants; pixelReuse + derivativeReuse only", "  No promotion or creative Parts Drawer exists."])
        lines.extend(["", "STILL QUARANTINED", f"  All {record['memberCount']} descendants, including the selected subset."])
    else:
        lines.extend(["", "LATER GRANT", f"  {grant['grantHash']}", f"  authority: {grant['grantingAuthority']}"])
        lines.extend(f"  {k}: {str(v).lower()}" for k, v in grant["permissions"].items())
        lines.extend(["", "PROMOTED"])
        lines.extend(f"  {r['assetId']} → {r['promotedLocalId']} → Parts Drawer | SHA {r['sha256']}" for r in promotion["promotedAssets"])
        lines.extend([f"  promotionHash: {promotion['promotionHash']}", f"  drawerId: {drawer['id']}", "", "STILL QUARANTINED"])
        lines.extend(f"  {r['assetId']} | SHA {r['sha256']} | {r['reason']}" for r in promotion["stillQuarantined"])
    lines.extend(["", "UNCHANGED", "  original LemonPRESS source", "  original MANGALIZE request/admission", "  original refusal",
                  "  original harvest-only grant", "  original 001 execution and return", "  original quarantine identities and artifact bytes",
                  "", "PUBLICATION", "  unchanged", "", "STAGING", "  not admitted", "", "ANIMATION / SOUND", "  not admitted"])
    return "\n".join(lines) + "\n"
