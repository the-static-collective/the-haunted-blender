from __future__ import annotations
import copy,hashlib,json

ATLAS_PROPOSALS_SCHEMA="haunted-blender/motion-route-proposals/v0"
ATLAS_IMPORT_SCHEMA="haunted-blender/motion-atlas-import/v1"

def _canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")

def _sha(value):
    return hashlib.sha256(_canonical(value)).hexdigest()

def import_route_proposals(value,*,atlas_package_sha256,observed_at):
    if not isinstance(value,dict) or value.get("schema")!=ATLAS_PROPOSALS_SCHEMA:
        raise ValueError("Expected MOTION ATLAS route proposals v0")
    if value.get("generation_submitted") is not False:
        raise ValueError("Atlas import refuses a snapshot claiming generation submission")
    if value.get("editorial_authority")!="human + existing Blender accepted-video-resolver/v0":
        raise ValueError("Atlas editorial boundary changed")
    if value.get("fallback_on_ambiguous_submission")!="STOP_AND_RECONCILE_EXISTING_JOB":
        raise ValueError("Atlas ambiguous-submission law changed")
    if not isinstance(atlas_package_sha256,str) or len(atlas_package_sha256)!=64:
        raise ValueError("Atlas package SHA-256 is required")
    if not isinstance(observed_at,str) or not observed_at:
        raise ValueError("observed_at is required")
    targets=[]
    for proposal in value.get("proposals") or []:
        state=proposal.get("state")
        if state not in {"proposal-only","unresolved","blocked"}:
            raise ValueError("Unknown Atlas proposal state")
        target={
            "endpointId":str(proposal.get("endpoint_id") or ""),
            "atlasState":state,
            "indicativeUsd":proposal.get("indicative_usd"),
            "quoteUnit":proposal.get("quote_unit"),
            "proposedGenerateSeconds":proposal.get("proposed_generate_seconds"),
            "windowSeconds":proposal.get("window_seconds"),
            "exactConfigurationQuote":proposal.get("exact_configuration_quote"),
            "accountAccess":proposal.get("account_access"),
            "reasons":list(proposal.get("reasons") or []),
            "spendAuthorized":bool(proposal.get("spend_authorized")),
            "candidateAccepted":bool(proposal.get("candidate_accepted")),
            "requires":list(proposal.get("requires") or []),
            "refreshRequired":True,
            "executionEligible":False,
        }
        if target["spendAuthorized"] or target["candidateAccepted"]:
            raise ValueError("Atlas proposal cannot arrive with spend or acceptance authority")
        targets.append(target)
    body={
        "schema":ATLAS_IMPORT_SCHEMA,
        "atlasPackageSha256":atlas_package_sha256,
        "observedAt":observed_at,
        "request":copy.deepcopy(value.get("request")),
        "targets":targets,
        "authority":"research-floor-only",
        "laws":[
            "ATLAS LISTING != LIVE OFFER",
            "INDICATIVE QUOTE != SPEND AUTHORITY",
            "ROUTE PROPOSAL != GENERATION",
            "ATLAS TARGET MUST REFRESH BEFORE 006 ROUTING",
            "AMBIGUOUS SUBMISSION != DEFINITIVE FAILURE",
        ],
    }
    return {**body,"id":f"motion-atlas-import:{_sha(body)[:24]}"}
