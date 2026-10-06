"""MANGALIZE-001: immutable verb events around the existing 008m quarry.

Only page-quarry -> optional Parts Drawer executes here. No staging, animation,
sound, publication, or automatic foreign-house write is an implemented operation.
"""
from __future__ import annotations

import copy
import json
import re
import shutil
import tempfile
from pathlib import Path

from . import manga_atlas as atlas

VERB = "MANGALIZE"
VERSION = "mangalize-001/v0"
SCHEMAS = {kind: f"static-collective/mangalize-{kind}/v0" for kind in ("request", "admission", "execution", "return", "source-grant")}
HASH_KEYS = {kind: kind.replace("-", "") + "Hash" for kind in SCHEMAS}
HASH_KEYS["source-grant"] = "sourceGrantHash"
GRANTS = ("pixelReuse", "pixelHarvest", "derivativeReuse", "publicationReuse", "motionAdaptation", "synthesizedSound")
OP_GRANT = {"harvest": "pixelHarvest", "reuse": "pixelReuse", "derive": "derivativeReuse", "publish": "publicationReuse", "animate": "motionAdaptation", "sound": "synthesizedSound"}
OPERATIONS = {"analyze", "harvest", "reuse", "derive", "stage", "render", "publish", "animate", "sound"}
IMPLEMENTED = {"analyze", "harvest", "reuse", "derive"}
TARGETS = {"page-quarry", "parts-drawer", "panel-sequence", "page"}
IDENTITY_KEYS = {"workId", "editionId", "editionHash", "issueId", "pageId", "pageHash", "sourceImageSha256"}
LAWS = [
    "MANGALIZE IS AN EVENT, NOT A PROPERTY", "MANGALIZE IS SOMETHING THAT HAPPENED",
    "MANGALIZED IS NOT AN INHERENT PROPERTY", "MANGALIZE != AUTHORIZE",
    "REQUESTED MANGALIZATION != ADMITTED MANGALIZATION", "ADMISSION != EXECUTION", "EXECUTION != PUBLICATION",
    "HARVEST AUTHORITY != PIXEL REUSE AUTHORITY", "PIXEL REUSE != DERIVATIVE AUTHORITY", "DERIVATIVE AUTHORITY != PUBLICATION AUTHORITY",
    "QUARRY DESCENDANT RETAINS PUBLICATION ANCESTRY", "ADAPTER IDENTITY != SOURCE IDENTITY", "FOREIGN ANCESTRY != LOCAL OWNERSHIP",
    "PAGE != PANEL MAP", "PANEL MAP != SEMANTIC UNDERSTANDING", "HARVESTED ASSET != CHARACTER IDENTITY",
    "EDGE MASK != SEMANTIC SEGMENTATION", "DESCENDANT != REPLACEMENT", "RETURN != HOUSE ADMISSION", "RETURN != PUBLICATION", "MANGALIZE != ANIMATE",
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nonempty(value):
    require(isinstance(value, str) and bool(value.strip()), "explicit identity/authority reference required")


def seal(kind, body):
    body = copy.deepcopy(body)
    body.pop("id", None)
    body.pop(HASH_KEYS[kind], None)
    body.update(schema=SCHEMAS[kind], verb=VERB)
    digest = atlas._hash(body)
    return {**body, "id": f"mangalize-{kind}:" + digest[:24], HASH_KEYS[kind]: digest}


def verify_event(kind, value):
    require(isinstance(value, dict) and value.get("schema") == SCHEMAS[kind] and value.get("verb") == VERB, f"expected {SCHEMAS[kind]} / MANGALIZE")
    require(value == seal(kind, value), f"{kind} event hash/identity mismatch")


def read(path):
    def pairs(items):
        result = {}
        for k, v in items:
            require(k not in result, "duplicate JSON key")
            result[k] = v
        return result
    result = json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=pairs)
    require(isinstance(result, dict), "expected JSON object")
    return result


def frozen_foreign(schema, hash_key, value):
    require(value.get("schema") == schema, f"expected {schema}")
    expected = atlas._hash({k: v for k, v in value.items() if k != hash_key})
    require(value.get(hash_key) == expected, f"foreign {hash_key} mismatch")


def grants(value):
    require(isinstance(value, dict) and set(value) == set(GRANTS) and all(type(x) is bool for x in value.values()), "all six grants must be explicit booleans")


def bound_path(root, binding):
    require(isinstance(binding, dict) and set(binding) == {"path", "sha256"}, "exact path/hash binding required")
    relative = Path(binding["path"])
    require(not relative.is_absolute() and ".." not in relative.parts and "\\" not in binding["path"] and relative.as_posix() == binding["path"], "canonical relative path required")
    root = Path(root).resolve(strict=True)
    path = (root / relative).resolve(strict=True)
    require(path.is_relative_to(root) and path.is_file(), "bound file escapes root or is absent")
    require(atlas._file_sha(path) == binding["sha256"], f"bound bytes changed: {binding['path']}")
    return path


def binding(root, path):
    path = Path(path).resolve(strict=True)
    return {"path": path.relative_to(Path(root).resolve(strict=True)).as_posix(), "sha256": atlas._file_sha(path)}


def source_grant(identity, handoff_hash, *, authority_ref, source_commit,
                 source_repository="the-static-collective/lemonPRESS", experiment="MANGALIZE-001"):
    """Separate explicit declaration. Never created by request/admit/execute."""
    nonempty(authority_ref)
    nonempty(source_repository)
    require(isinstance(source_commit, str) and re.fullmatch(r"[0-9a-f]{40}", source_commit) is not None, "grant requires exact source commit")
    require(experiment == "MANGALIZE-001", "grant is bounded to MANGALIZE-001")
    return seal("source-grant", {"ancestor": identity, "handoffHash": handoff_hash,
        "sourceRepository": source_repository, "sourceCommit": source_commit, "experiment": experiment,
        "grantSemantics": "event-specific permission ceiling; no retroactive source mutation",
        "operationScope": ["harvest"], "grants": {k: k == "pixelHarvest" for k in GRANTS},
        "authorityRef": authority_ref, "basis": "explicit supplemental declaration; not an inherited LemonPRESS grant",
        "laws": LAWS + ["REFUSAL WAS CORRECT", "LATER GRANT != RETROACTIVE AUTHORITY", "HARVEST != REUSE", "GRANT EVENT != SOURCE MUTATION"]})


def validate_foreign(handoff, page, page_id):
    frozen_foreign("lemonpress/manga-performance-handoff/v0", "handoffHash", handoff)
    frozen_foreign("lemonpress/manga-page/v0", "pageHash", page)
    require(handoff.get("authority") == {"render": False, "staging": False, "editorialAdmission": False, "houseRelease": False}, "handoff grants no execution authority")
    selected = [p for p in handoff["pages"] if p["identity"]["pageId"] == page_id]
    require(len(selected) == 1, "one exact page identity required")
    entry = selected[0]
    identity = entry["identity"]
    require(set(identity) == IDENTITY_KEYS, "full publication locator required")
    for key in IDENTITY_KEYS:
        nonempty(identity[key])
    for key in ("editionHash", "pageHash", "sourceImageSha256"):
        require(re.fullmatch(r"[0-9a-f]{64}", identity[key]) is not None, "publication locator requires exact SHA-256")
    for key in ("workId", "editionId", "editionHash", "issueId"):
        require(identity[key] == handoff[key], "handoff publication identity mismatch")
    for key in ("editionId", "issueId", "pageId", "pageHash"):
        require(page[key] == identity[key], "page manifest identity mismatch")
    require(entry["sourceImage"] is not None and entry["sourceImage"] == page["sourceImage"] and
            identity["sourceImageSha256"] == page["sourceImage"]["sha256"], "exact source pixel SHA required")
    require(entry["grants"] == page["grants"] and entry["rightsSource"] == page["rightsSource"], "page rights origin mismatch")
    grants(handoff["grants"])
    grants(entry["grants"])
    return entry


def make_request(root, handoff_path, page_path, *, page_id, target="page-quarry", operations=("harvest", "reuse", "derive"),
                 authority_ref, source_repository="the-static-collective/lemonPRESS", source_commit=None, grant_paths=(), requested_grants=None):
    nonempty(authority_ref)
    nonempty(source_repository)
    require(source_commit is None or (isinstance(source_commit, str) and re.fullmatch(r"[0-9a-f]{40}", source_commit) is not None), "source commit must be exact or explicitly unknown")
    handoff, page = read(handoff_path), read(page_path)
    entry = validate_foreign(handoff, page, page_id)
    require(target in TARGETS, "unknown manga target")
    ops = sorted(set(operations))
    require(bool(ops) and set(ops) <= OPERATIONS, "unknown or empty requested operations")
    supplied = {k: handoff["grants"][k] and page["grants"][k] for k in GRANTS}
    supplemental = []
    for path in grant_paths:
        declaration = read(path)
        verify_event("source-grant", declaration)
        require(declaration == source_grant(entry["identity"], handoff["handoffHash"], authority_ref=declaration["authorityRef"],
            source_commit=source_commit, source_repository=source_repository), "supplemental grant must bind this exact ancestor/handoff and only harvest")
        supplemental.append({"binding": binding(root, path), "declaration": declaration})
        # This later event has its own ceiling. Original reuse permissions do
        # not widen the explicitly bounded harvest-only experiment.
        supplied = declaration["grants"].copy()
    desired = requested_grants if requested_grants is not None else {k: any(OP_GRANT.get(op) == k for op in ops) for k in GRANTS}
    grants(desired)
    return seal("request", {"ancestors": [{"system": "lemonpress", "repository": source_repository, "commit": source_commit,
        "kinds": ["lemonpress/manga-page/v0", "lemonpress/manga-performance-handoff/v0"], "locator": entry["identity"],
        "sourceHash": entry["identity"]["sourceImageSha256"], "handoffHash": handoff["handoffHash"]}],
        "foreignEvidence": {"handoff": handoff, "page": page, "handoffBinding": binding(root, handoff_path), "pageBinding": binding(root, page_path)},
        "supplementalGrants": supplemental, "target": target, "requestedOperations": ops, "suppliedGrants": supplied,
        "requestedGrants": desired, "continuityContext": {"orderingContext": handoff["orderingContext"], "continuityGroupReferences": page["continuityGroupReferences"]},
        "descendantRelationship": "derived-from; source retained; sibling descendants", "requestingAuthority": authority_ref,
        "authority": "request-only", "laws": LAWS})


def verify_request(root, request):
    verify_event("request", request)
    evidence = request["foreignEvidence"]
    handoff_path = bound_path(root, evidence["handoffBinding"])
    page_path = bound_path(root, evidence["pageBinding"])
    ancestor = request["ancestors"][0]
    grant_paths = [bound_path(root, g["binding"]) for g in request["supplementalGrants"]]
    rebuilt = make_request(root, handoff_path, page_path, page_id=ancestor["locator"]["pageId"], target=request["target"],
        operations=request["requestedOperations"], authority_ref=request["requestingAuthority"], source_repository=ancestor["repository"],
        source_commit=ancestor["commit"], grant_paths=grant_paths, requested_grants=request["requestedGrants"])
    require(request == rebuilt, "request differs from independent foreign evidence/grant reconstruction")
    bound_path(root, evidence["page"]["sourceImage"])


def admit(request, *, allow, authority_ref):
    verify_event("request", request)
    evidence = request["foreignEvidence"]
    entry = validate_foreign(evidence["handoff"], evidence["page"], request["ancestors"][0]["locator"]["pageId"])
    require(entry["identity"] == request["ancestors"][0]["locator"], "request ancestry differs from foreign evidence")
    require(len(request["ancestors"]) == 1 and request["ancestors"][0]["sourceHash"] == entry["identity"]["sourceImageSha256"] and
            request["ancestors"][0]["handoffHash"] == evidence["handoff"]["handoffHash"], "request cannot fabricate source or handoff hash")
    supplied = {k: evidence["handoff"]["grants"][k] and evidence["page"]["grants"][k] for k in GRANTS}
    for grant in request["supplementalGrants"]:
        declaration = grant["declaration"]
        require(declaration == source_grant(entry["identity"], evidence["handoff"]["handoffHash"], authority_ref=declaration["authorityRef"],
            source_commit=request["ancestors"][0]["commit"], source_repository=request["ancestors"][0]["repository"]), "request cannot fabricate supplemental grant scope")
        supplied = declaration["grants"].copy()
    require(request["suppliedGrants"] == supplied, "request cannot promote its own supplied permission")
    grants(request["requestedGrants"])
    nonempty(authority_ref)
    require(authority_ref != request["requestingAuthority"], "request cannot self-admit; separate admitting authority reference required")
    require(request["target"] in ("page-quarry", "parts-drawer"), "target is vocabulary only, not implemented")
    allowed = sorted(set(allow))
    require(bool(allowed) and set(allowed) <= set(request["requestedOperations"]) and set(allowed) <= IMPLEMENTED, "admitted subset exceeds requested or implemented operations")
    for op in allowed:
        key = OP_GRANT.get(op)
        require(key is None or (request["suppliedGrants"][key] is True and request["requestedGrants"][key] is True), f"{op} refused: {key} not supplied/requested")
    effective = {k: any(OP_GRANT.get(op) == k for op in allowed) for k in GRANTS}
    return seal("admission", {"requestHash": request["requestHash"], "ancestors": request["ancestors"], "target": request["target"],
        "admittedOperations": allowed, "excludedOperations": sorted(set(request["requestedOperations"]) - set(allowed)),
        "effectiveGrants": effective, "authorityRef": authority_ref, "decision": "explicit-admitted-subset", "laws": LAWS})


def verify_admission(request, admission):
    verify_event("admission", admission)
    if admission["decision"] == "refused":
        expected = decide(request, allow=admission["attemptedOperations"], authority_ref=admission["authorityRef"])
    else:
        expected = admit(request, allow=admission["admittedOperations"], authority_ref=admission["authorityRef"])
    require(admission == expected, "admission differs from independent request/grant reconstruction")


def decide(request, *, allow, authority_ref):
    verify_event("request", request)
    nonempty(authority_ref)
    try:
        return admit(request, allow=allow, authority_ref=authority_ref)
    except ValueError as exc:
        return seal("admission", {"requestHash": request["requestHash"], "ancestors": request["ancestors"], "target": request["target"],
            "admittedOperations": [], "attemptedOperations": sorted(set(allow)), "excludedOperations": request["requestedOperations"],
            "effectiveGrants": {k: False for k in GRANTS}, "authorityRef": authority_ref, "decision": "refused", "reason": str(exc), "laws": LAWS})


def adapt_page(root, request, admission):
    verify_request(root, request)
    verify_admission(request, admission)
    require(admission["decision"] == "explicit-admitted-subset", "refused admission cannot execute")
    page = request["foreignEvidence"]["page"]
    rights = admission["effectiveGrants"]
    manifest = atlas.source_manifest(bound_path(root, page["sourceImage"]), source_class="licensed",
        pixel_reuse=rights["pixelReuse"], pixel_harvest=rights["pixelHarvest"], derivative_reuse=rights["derivativeReuse"],
        publication_reuse=False, rights_note="Foreign-source declarations and exact MANGALIZE admission; no local ownership or publication claim.",
        label=page["pageId"], grammar_families=["panel-rhythm"], source_root=root, foreign_ancestry=request["ancestors"],
        event_lineage=[{"verb": VERB, "requestHash": request["requestHash"], "admissionHash": admission["admissionHash"]}])
    return manifest


def persist(path, data):
    path = Path(path)
    payload = atlas._stable(data) if not isinstance(data, bytes) else data
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(payload)
    except FileExistsError:
        require(path.read_bytes() == payload, f"create-only conflict: {path.name}")


def run(root, request, admission, out):
    """Create a fresh candidate run. Public execute commits it create-only."""
    manifest = adapt_page(root, request, admission)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    persist(out / "mangalize.request.json", request)
    persist(out / "mangalize.admission.json", admission)
    persist(out / "page-source.json", manifest)
    performed, observations, skipped = [], ["geometry analysis"], []
    allowed = admission["admittedOperations"]
    # Harvest admission includes its necessary geometry inspection; analyze-only
    # is separately possible without granting any extraction.
    require("analyze" in allowed or "harvest" in allowed, "execution needs admitted analysis or harvest")
    if "analyze" in allowed:
        performed.append("analyze")
    report = atlas.analyze_page(manifest, source_root=root)
    persist(out / "page-analysis.json", report)
    harvest = drawer = None
    if "harvest" in allowed:
        harvest = atlas.harvest_page(manifest, out / "harvest", source_root=root, artifact_root=out)
        performed.append("harvest")
        observations.extend(["quarry / nonsemantic crop derivation", "nonsemantic edge mask"])
        if "reuse" in allowed and "derive" in allowed:
            drawer = atlas.page_harvest_to_parts_drawer(harvest, out / "parts-drawer.combined.json")
            performed.extend(["reuse", "derive"])
            observations.append("Parts Drawer admission as reusable candidates, not staged material")
        else:
            skipped.append({"operation": "parts-drawer", "reason": "requires separately admitted reuse and derive; harvest remains quarantined"})
    else:
        skipped.append({"operation": "harvest", "reason": "not admitted"})
    # Every produced node has its own local identity, exact hash, foreign parent,
    # event lineage and recipe. No source replacement or opaque value score.
    ancestor = request["ancestors"][0]
    nodes = [{"id": manifest["id"], "kind": manifest["schema"], "parents": [ancestor], "artifact": {"path": "page-source.json", "sha256": atlas._file_sha(out / "page-source.json")}, "foreignAncestry": request["ancestors"]},
             {"id": report["id"], "kind": report["schema"], "parents": [manifest["id"]], "artifact": {"path": "page-analysis.json", "sha256": atlas._file_sha(out / "page-analysis.json")}, "foreignAncestry": request["ancestors"]}]
    if harvest:
        nodes.append({"id": harvest["id"], "kind": harvest["schema"], "parents": [manifest["id"], report["id"]], "artifact": {"path": "harvest/page-harvest.json", "sha256": atlas._file_sha(out / "harvest/page-harvest.json")}, "foreignAncestry": request["ancestors"]})
        for row in harvest["assets"]:
            panel_parent = next((p["id"] for p in harvest["assets"] if p["kind"] == "panel" and p["panelId"] == row["panelId"]), None)
            parents = [panel_parent, harvest["id"]] if row["kind"] in ("region-candidate", "edge-mask") else [manifest["id"], harvest["id"]]
            node_body = {"kind": row["kind"], "parents": parents, "panelId": row["panelId"], "artifact": {"path": row["path"], "sha256": row["sha256"]},
                         "recipe": row["recipe"], "foreignAncestry": row["foreignAncestry"], "materialAuthority": row["materialAuthority"]}
            nodes.append({"id": row["id"], **node_body})
    if drawer:
        nodes.append({"id": drawer["id"], "kind": drawer["schema"], "parents": [n["id"] for n in nodes if n["kind"] in ("panel", "region-candidate", "edge-mask", "quarry-candidate")],
                      "artifact": {"path": "parts-drawer.combined.json", "sha256": atlas._file_sha(out / "parts-drawer.combined.json")}, "foreignAncestry": request["ancestors"]})
    for node in nodes:
        node["eventLineage"] = manifest["eventLineage"]
    carried = {**admission["effectiveGrants"], "pixelHarvest": False}
    artifacts = [binding(out, p) for p in sorted(out.rglob("*")) if p.is_file()]
    for op in sorted(OPERATIONS - set(performed)):
        skipped.append({"operation": op, "reason": "not requested" if op not in request["requestedOperations"] else "not admitted/performed"})
    execution = seal("execution", {"requestHash": request["requestHash"], "admissionHash": admission["admissionHash"],
        "executor": {"system": "haunted-blender", "version": VERSION, "engine": "008m geometry/quarry + 008h drawer"},
        "ancestors": request["ancestors"], "performedOperations": sorted(set(performed)), "observations": observations, "refusedOrSkipped": skipped,
        "descendants": nodes, "artifacts": artifacts, "effectiveGrants": admission["effectiveGrants"], "grantsCarried": carried, "grantsNotCarried": sorted(k for k in GRANTS if not carried[k]),
        "structure": {"source": {"form": "publication-page", "pixelDimensions": [manifest["width"], manifest["height"]], "internalSemantics": "unknown"},
                      "target": {"form": "geometry report and candidate graph", "panelMapStatus": report["panelMapStatus"], "quarryCandidates": 0 if harvest is None else harvest["quarryCandidateCount"]},
                      "newParts": 0 if harvest is None else harvest["assetCount"],
                      "roleChanges": [{"ancestorRole": "whole-publication-page", "descendantRole": n["kind"], "descendantId": n["id"], "materialAuthority": n["materialAuthority"]} for n in nodes if "materialAuthority" in n]},
        "publicationStateChange": None, "laws": LAWS})
    returned = seal("return", {"ancestors": request["ancestors"], "eventLineage": {"requestHash": request["requestHash"], "admissionHash": admission["admissionHash"], "executionHash": execution["executionHash"]},
        "performedTransformation": execution["observations"], "descendants": nodes, "omissions": ["semantic identities", "staging", "animation", "sound", "publication"],
        "refusals": skipped, "grantsCarried": execution["grantsCarried"], "grantsNotCarried": execution["grantsNotCarried"], "artifacts": artifacts,
        "foreignReturnBasis": {"handoffHash": ancestor["handoffHash"], "consumedPages": [ancestor["locator"]], "preservedPages": [ancestor["locator"]],
            "descendantId": drawer["id"] if drawer else (harvest["id"] if harvest else report["id"]), "renderer": VERSION,
            "artifacts": artifacts, "omittedMaterial": ["unselected issue pages; narrative performance"], "mutations": execution["observations"]},
        "verification": "independent byte/recipe replay required; this receipt grants no authority", "publicationStateChange": None,
        "authority": {"houseAdmission": False, "publication": False, "staging": False, "render": False, "animate": False}, "laws": LAWS})
    persist(out / "mangalize.execution.json", execution)
    persist(out / "mangalize.return.json", returned)
    persist(out / "TRACE.md", trace(request, admission, execution, returned).encode("utf-8"))
    return returned


def tree_bytes(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def execute(root, request, admission, out):
    out = Path(out).resolve()
    # Regenerate independently, including all PNGs and recipes; compare complete
    # contents before trusting or reusing a persisted receipt. Local paths never
    # enter canonical identity, so fresh-directory replay has the same bytes.
    with tempfile.TemporaryDirectory(prefix="mangalize-replay-") as td:
        candidate = Path(td) / "event"
        returned = run(root, request, admission, candidate)
        if out.exists():
            require(tree_bytes(out) == tree_bytes(candidate), "MANGALIZE verification failure: existing event differs from independent replay")
        else:
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(candidate, out)
    return returned


def verify(root, request, admission, out):
    require(Path(out).is_dir(), "missing execution directory")
    returned = execute(root, request, admission, out)
    return returned["returnHash"]


def trace(request, admission, execution, returned):
    identity = request["ancestors"][0]["locator"]
    lines = ["# MANGALIZE EVENT 001", "", "SOURCE"]
    lines.extend(f"  {k}: {identity[k]}" for k in ("workId", "editionId", "editionHash", "issueId", "pageId", "pageHash", "sourceImageSha256"))
    ancestor = request["ancestors"][0]
    lines.extend([f"  repository: {ancestor['repository']}", f"  commit: {ancestor['commit']}", f"  handoffHash: {ancestor['handoffHash']}"])
    for grant in request["supplementalGrants"]:
        declaration = grant["declaration"]
        lines.extend(["", "SEPARATE GRANT", f"  sourceGrantHash: {declaration['sourceGrantHash']}",
                      f"  authority: {declaration['authorityRef']}", f"  experiment: {declaration['experiment']}",
                      "  scope: harvest only; later event; original refusal remains valid"])
        lines.extend(f"  {k}: {str(declaration['grants'][k]).lower()}" for k in GRANTS)
    for label, values in (("REQUESTED", request["requestedOperations"]), ("ADMITTED", admission["admittedOperations"]), ("PERFORMED", execution["observations"])):
        lines.extend(["", label, *["  " + v for v in values]])
    lines.extend(["", "REFUSED / SKIPPED"])
    lines.extend(f"  {row['operation']}: {row['reason']}" for row in execution["refusedOrSkipped"])
    lines.extend(["", "DESCENDANT PERMISSIONS"])
    lines.extend(f"  {k}: {str(returned['grantsCarried'][k]).lower()}" for k in GRANTS)
    lines.extend(["  No recursive harvest grant; no source replacement.", "", "DESCENDANTS"])
    lines.extend(f"  {row['kind']}: {row['id']} | {row['artifact']['path']} | SHA {row['artifact']['sha256']}" for row in execution["descendants"])
    lines.extend(["", "ANCESTRY", "  PRESERVED: every node retains exact foreign locator and local event custody", "", "PUBLICATION STATE", "  UNCHANGED", "", "EVENT HASHES"])
    lines.extend("  " + value for value in (request["requestHash"], admission["admissionHash"], execution["executionHash"], returned["returnHash"]))
    return "\n".join(lines) + "\n"
