"""MANGALIZE-003: explicit static composition custody, never pixel execution.

Factories do not authenticate humans. Admission declarations must be issued only
under an independently recorded authority; proposals and material grants cannot
supply it. CLI execution consumes declarations, never manufactures them.
"""
from __future__ import annotations

import copy
import shutil
import tempfile
from pathlib import Path

from . import mangalize as m, manga_atlas as atlas, manga_quarantine as q, parts_harvester as parts

SCHEMAS = {k: "static-collective/manga-" + name + "/v0" for k, name in {
    "role": "role-proposal", "placement": "placement-proposal", "admission": "performed-use-admission",
    "use": "performed-use", "layout": "performance-layout"}.items()}
HASH_KEYS = {k: k + "Hash" for k in SCHEMAS}
ROLES = ("poster", "texture", "cutaway", "prop", "mask", "insert")
CLOSED = {k: False for k in ("performedUse", "render", "motion", "sound", "publication", "externalGeneration", "characterCasting")}
ADMITTED = {**CLOSED, "performedUse": True}
NONCLAIMS = {k: None for k in ("semanticIdentity", "characterIdentity", "objectIdentity", "sourceFact", "semanticSegmentation")}
LAWS = ["ROLE PROPOSAL != ROLE ADMISSION", "ROLE != SEMANTIC IDENTITY", "ROLE != PLACEMENT",
    "PLACEMENT != SOURCE FACT", "TRANSFORM != SEMANTIC CLAIM", "POSSIBLE ROLE != PERFORMED ROLE",
    "MATERIAL AUTHORITY != PERFORMED-USE AUTHORITY", "PROPOSAL != ADMISSION", "PIXEL IDENTITY != USE IDENTITY",
    "PERFORMED USE != RENDER", "PLACEMENT ADMISSION != PIXEL EXECUTION", "LAYOUT != RENDER",
    "COMPOSITION EXISTS BEFORE PIXEL EXECUTION", "USE AUTHORITY != RENDER AUTHORITY",
    "USE AUTHORITY != PUBLICATION AUTHORITY", "USE AUTHORITY != MOTION AUTHORITY", "USE AUTHORITY != SOUND AUTHORITY",
    "PERFORMANCE != RETROACTIVE SOURCE TRUTH", "ANCESTRY SURVIVES PERFORMANCE"]


def seal(kind, body):
    body = copy.deepcopy(body)
    body.pop("id", None)
    body.pop(HASH_KEYS[kind], None)
    body.update(schema=SCHEMAS[kind], verb="MANGALIZE", experiment="MANGALIZE-003")
    digest = atlas._hash(body)
    return {**body, "id": "manga-" + kind + ":" + digest[:24], HASH_KEYS[kind]: digest}


def verify_event(kind, record):
    m.require(record.get("schema") == SCHEMAS[kind] and record.get("experiment") == "MANGALIZE-003" and record.get("verb") == "MANGALIZE", "wrong performed-use event family")
    m.require(record == seal(kind, record), f"{kind} identity/hash mismatch")


def verified_drawer(source_root, ancestor_root, release_root):
    """Independent full 001/002 replay, including exact historical pixel bytes."""
    root = Path(release_root)
    record, selection, grant = (m.read(root / (name + ".json")) for name in ("quarantine-set", "selection", "asset-grant"))
    q.verify(source_root, ancestor_root, record, selection, grant, root)
    return m.read(root / "parts-drawer.json")


def material(drawer, asset_id):
    m.require(drawer.get("schema") == parts.DRAWER_SCHEMA, "expected Parts Drawer")
    body = {k: v for k, v in drawer.items() if k != "id"}
    m.require(drawer["id"] == "parts-drawer:" + atlas._hash(body)[:24], "drawer identity mismatch")
    rows = [row for row in drawer["artifacts"] if row["id"] == asset_id]
    m.require(len(rows) == 1, "exact unique promoted asset required")
    row = rows[0]
    provenance = parts.material_provenance(row)
    m.require(provenance is not None and row.get("admittedUseId") == provenance.get("admittedUseId") and bool(row.get("admittedUseId")), "promoted admittedUseId required")
    m.grants(row["rights"])
    m.require(row["rights"] == provenance["effectivePermissions"] and row["rights"]["pixelReuse"] and row["rights"]["derivativeReuse"], "material requires exact reuse/derivative permission ceiling")
    return {"assetId": row["id"], "sha256": row["sha256"], "admittedUseId": row["admittedUseId"],
        "drawerId": drawer["id"], "drawerSha256": atlas._hash(drawer), "artifact": {"path": row["path"], "sha256": row["sha256"]},
        "artifactKind": row["kind"], "provenance": provenance, "permissionCeiling": copy.deepcopy(row["rights"])}


def role_proposal(drawer, *, asset_id, role, rationale, authority_ref):
    m.require(role in ROLES, "unsupported structural role")
    m.nonempty(rationale)
    m.nonempty(authority_ref)
    return seal("role", {"material": material(drawer, asset_id), "proposedRole": role, "rationale": rationale,
        "proposingAuthority": authority_ref, "authority": CLOSED, "semanticNonclaims": NONCLAIMS, "laws": LAWS})


def verify_role(drawer, record):
    verify_event("role", record)
    expected = role_proposal(drawer, asset_id=record["material"]["assetId"], role=record["proposedRole"],
        rationale=record["rationale"], authority_ref=record["proposingAuthority"])
    m.require(record == expected, "role differs from exact promoted material/provenance")


def integer(value, low, high, name):
    m.require(type(value) is int and low <= value <= high, "invalid canonical integer " + name)


def validate_placement(value):
    """Fixed-point integers, explicit units/anchors; no float replay ambiguity.

    Positions are millipixels, scale/opacity millionths, angle millidegrees.
    Crop and time are explicitly absent in this static founding grammar.
    Canvas clipping is explicit; no vendor, camera or semantic inference.
    """
    m.require(set(value) == {"canvas", "xMilliPixels", "yMilliPixels", "z", "scaleMillionths", "rotationMilliDegrees",
        "opacityMillionths", "anchor", "fit", "crop", "overflow", "timeRange"}, "complete explicit static placement required")
    canvas = value["canvas"]
    m.require(set(canvas) == {"widthPixels", "heightPixels", "origin"} and canvas["origin"] == "top-left", "explicit canvas required")
    for key in ("widthPixels", "heightPixels"):
        integer(canvas[key], 64, 16384, key)
    for key, limit in (("xMilliPixels", canvas["widthPixels"] * 1000), ("yMilliPixels", canvas["heightPixels"] * 1000)):
        integer(value[key], 0, limit, key)
    integer(value["z"], -10000, 10000, "z")
    integer(value["scaleMillionths"], 1, 16000000, "scaleMillionths")
    integer(value["rotationMilliDegrees"], -360000, 360000, "rotationMilliDegrees")
    integer(value["opacityMillionths"], 0, 1000000, "opacityMillionths")
    m.require(value["anchor"] == "top-left" and value["fit"] == "native-scale" and value["overflow"] == "clip-to-canvas", "unsupported explicit fit/anchor/overflow")
    m.require(value["crop"] is None and value["timeRange"] is None, "003 supports static uncropped placement only")


def placement_proposal(drawer, role, *, placement, rationale, authority_ref):
    verify_role(drawer, role)
    validate_placement(placement)
    m.nonempty(rationale)
    m.nonempty(authority_ref)
    return seal("placement", {"material": role["material"], "roleProposalHash": role["roleHash"], "proposedPlacement": placement,
        "rationale": rationale, "proposingAuthority": authority_ref, "authority": CLOSED, "semanticNonclaims": NONCLAIMS, "laws": LAWS})


def verify_placement(drawer, role, record):
    verify_event("placement", record)
    expected = placement_proposal(drawer, role, placement=record["proposedPlacement"], rationale=record["rationale"], authority_ref=record["proposingAuthority"])
    m.require(record == expected, "placement differs from exact role/material/transform")


def admit(drawer, role, placement, *, authority_ref):
    """External declaration factory, never invoked by proposal/perform/layout.

    Real declarations require separately recorded exact performed-use approval.
    A reference is an accountable declaration, not a cryptographic identity.
    """
    verify_placement(drawer, role, placement)
    m.nonempty(authority_ref)
    excluded = {role["proposingAuthority"], placement["proposingAuthority"], role["roleHash"], placement["placementHash"]}
    # Do not accept the material-grant event itself as performed-use authority.
    for event in role["material"]["provenance"].get("eventLineage", []):
        excluded.update(str(event[k]) for k in ("grantHash", "grantId") if k in event)
    m.require(authority_ref not in excluded, "proposal/material authority cannot self-admit performed use")
    return seal("admission", {"material": role["material"], "roleProposalHash": role["roleHash"],
        "placementProposalHash": placement["placementHash"], "admittedRole": role["proposedRole"],
        "admittedPlacement": placement["proposedPlacement"], "permissionCeiling": role["material"]["permissionCeiling"],
        "externalAuthority": authority_ref, "authority": ADMITTED,
        "nonAuthorities": sorted(k for k, v in ADMITTED.items() if not v), "semanticNonclaims": NONCLAIMS, "laws": LAWS})


def verify_admission(drawer, role, placement, admission):
    verify_event("admission", admission)
    expected = admit(drawer, role, placement, authority_ref=admission["externalAuthority"])
    m.require(admission == expected, "admission exceeds exact proposed role/placement/permission ceiling")


def perform(drawer, artifact_root, role, placement, admission):
    verify_admission(drawer, role, placement, admission)
    row = next(row for row in drawer["artifacts"] if row["id"] == role["material"]["assetId"])
    parts.resolve_drawer_artifact(drawer, row, artifact_root=artifact_root)
    provenance = copy.deepcopy(role["material"]["provenance"])
    provenance["eventLineage"].append({"verb": "MANGALIZE", "experiment": "MANGALIZE-003", "roleProposalHash": role["roleHash"],
        "placementProposalHash": placement["placementHash"], "admissionHash": admission["admissionHash"]})
    # Historical authority within the original envelope remains untouched.
    return seal("use", {"material": role["material"], "performedRole": role["proposedRole"], "placement": placement["proposedPlacement"],
        "provenance": provenance, "roleProposalHash": role["roleHash"], "placementProposalHash": placement["placementHash"],
        "admissionHash": admission["admissionHash"], "effectivePermissions": role["material"]["permissionCeiling"],
        "authority": ADMITTED, "semanticNonclaims": NONCLAIMS, "artifactChanges": [], "laws": LAWS})


def performance_layout(drawer, artifact_root, bundles):
    """Reconstruct every instruction from its separate admission, never claims."""
    m.require(bool(bundles), "at least one separately admitted use required")
    uses = []
    for bundle in bundles:
        m.require(set(bundle) == {"role", "placement", "admission"}, "exact proposal/placement/admission bundle required")
        uses.append(perform(drawer, artifact_root, bundle["role"], bundle["placement"], bundle["admission"]))
    m.require(len({r["useHash"] for r in uses}) == len(uses), "duplicate performed use")
    canvas = uses[0]["placement"]["canvas"]
    m.require(all(r["placement"]["canvas"] == canvas for r in uses), "layout canvas mismatch")
    uses.sort(key=lambda r: (r["placement"]["z"], r["useHash"]))
    return seal("layout", {"drawerId": drawer["id"], "canvas": canvas, "performedUses": uses, "authority": ADMITTED,
        "renderedArtifacts": [], "publicationStateChange": None, "semanticNonclaims": NONCLAIMS, "laws": LAWS})


def verify_use(drawer, artifact_root, bundle, record):
    verify_event("use", record)
    m.require(record == perform(drawer, artifact_root, bundle["role"], bundle["placement"], bundle["admission"]), "performed use differs from independent admission replay")


def verify_layout(drawer, artifact_root, bundles, record):
    verify_event("layout", record)
    m.require(record == performance_layout(drawer, artifact_root, bundles), "layout differs from independent admitted-use replay")


def execute(source_root, ancestor_root, release_root, bundles, out):
    """Create-only immutable event tree, independently verified before writing."""
    out = Path(out).resolve()
    for protected in (source_root, ancestor_root, release_root):
        m.require(not out.is_relative_to(Path(protected).resolve()), "performed use cannot write inside ancestor evidence")
    drawer = verified_drawer(source_root, ancestor_root, release_root)
    from . import stage_compost
    layout = stage_compost.admitted_plan(drawer, artifact_root=ancestor_root, bundles=bundles)
    with tempfile.TemporaryDirectory(prefix="performed-use-") as td:
        candidate = Path(td) / "event"
        candidate.mkdir()
        # Canonical order independent of caller's file/input ordering.
        by_hash = {bundle["role"]["roleHash"] + bundle["placement"]["placementHash"] + bundle["admission"]["admissionHash"]: bundle for bundle in bundles}
        for index, bundle in enumerate(by_hash[key] for key in sorted(by_hash)):
            for kind, record in bundle.items():
                m.persist(candidate / f"{index:03d}" / (kind + ".json"), record)
            m.persist(candidate / f"{index:03d}" / "use.json", perform(drawer, ancestor_root, **bundle))
        m.persist(candidate / "layout.json", layout)
        m.persist(candidate / "TRACE.md", trace(bundles, layout).encode())
        if out.exists():
            m.require(m.tree_bytes(out) == m.tree_bytes(candidate), "performed-use verification failure: persisted event differs from replay")
        else:
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(candidate, out)
    return layout


def verify(source_root, ancestor_root, release_root, bundles, out):
    m.require(Path(out).is_dir(), "missing performed-use event directory")
    return execute(source_root, ancestor_root, release_root, bundles, out)["layoutHash"]


def trace(bundles, layout=None):
    lines = ["# MANGALIZE EVENT 003", "", "ANCESTOR", "  MANGALIZE-002 promoted material; historical custody unchanged", "", "PROPOSED USES"]
    for bundle in sorted(bundles, key=lambda r: (r["role"]["material"]["assetId"], r["placement"]["placementHash"])):
        role, placement = bundle["role"], bundle["placement"]
        mat = role["material"]
        lines.extend([f"  {mat['assetId']} | SHA {mat['sha256']}", f"  admittedUseId: {mat['admittedUseId']}",
            f"  drawerId: {mat['drawerId']}", f"  role: {role['proposedRole']} (structural use; semantic claim: none)",
            f"  roleHash: {role['roleHash']}", f"  placementHash: {placement['placementHash']}", "  placement:"])
        lines.extend(f"    {k}: {atlas._stable(v).decode()}" for k, v in sorted(placement["proposedPlacement"].items()))
        lines.extend(["  ORIGINAL CUSTODY:", *[f"    {atlas._stable(event).decode()}" for event in mat["provenance"]["eventLineage"]]])
        for ancestor in mat["provenance"].get("foreignAncestry", []):
            lines.append(f"    foreign ancestor: {atlas._stable(ancestor).decode()}")
    if layout is None:
        lines.extend(["", "PERFORMED USE READY — ADMISSION REQUIRED", "  Proposed only; no performed-use records or performance layout exist.",
            "  Requested: performedUse=true for these exact roles and placements only."])
    else:
        lines.extend(["", "ADMITTED STATIC COMPOSITION", f"  layoutHash: {layout['layoutHash']}"])
        for use in layout["performedUses"]:
            admission = next(bundle["admission"] for bundle in bundles if bundle["admission"]["admissionHash"] == use["admissionHash"])
            lines.extend([f"  {use['material']['assetId']} → {use['performedRole']} | useHash {use['useHash']}",
                f"  admissionHash: {use['admissionHash']}", f"  externalAuthority: {admission['externalAuthority']}",
                f"  effective material permissions: {atlas._stable(use['effectivePermissions']).decode()}",
                f"  performed-use authority: {atlas._stable(use['authority']).decode()}",
                f"  003 custody: {atlas._stable(use['provenance']['eventLineage'][-1]).decode()}"])
        lines.extend(["  rendered artifacts: 0", "  artifact changes: 0"])
    lines.extend(["", "UNCHANGED", "  original source page and harvested pixels", "  MANGALIZE-001 refusal, harvest-only grant, execution, return",
        "  MANGALIZE-002 quarantine, selection, later grant, promotion, drawer", "  22 unselected siblings remain quarantined",
        "", "RENDER / MOTION / SOUND / PUBLICATION", "  not admitted; no pixel execution", "", "SEMANTIC IDENTITY / CHARACTER CASTING", "  no claims or authority"])
    return "\n".join(lines) + "\n"
