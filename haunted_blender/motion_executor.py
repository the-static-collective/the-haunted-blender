from __future__ import annotations
import copy,hashlib,json
from pathlib import Path
from . import atlas_black_box,motion_organ,project

PLAN_SCHEMA="haunted-blender/motion-execution-plan/v1"
STATE_SCHEMA="haunted-blender/motion-execution-state/v1"
CAP_SCHEMA="haunted-blender/provider-capabilities-receipt/v1"
QUOTE_SCHEMA="haunted-blender/provider-quote-receipt/v1"
SUBMIT_SCHEMA="haunted-blender/provider-submit-receipt/v1"
STATUS_SCHEMA="haunted-blender/provider-status-receipt/v1"
FETCH_SCHEMA="haunted-blender/provider-fetch-receipt/v1"

def _canonical(value): return project.stable_bytes(value)
def _sha(value): return hashlib.sha256(_canonical(value)).hexdigest()
def _root(root): return Path(root).expanduser().resolve()

def _save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    payload=_canonical(value)+b"\n"
    try:
        with path.open("xb") as h: h.write(payload)
    except FileExistsError:
        if path.read_bytes()!=payload: raise ValueError("Existing execution witness changed")

def _plan_path(root,digest): return root/"snapshots"/"motion-execution-plans"/f"{digest}.json"
def _state_path(root,digest): return root/"snapshots"/"motion-execution-state"/f"{digest}.json"
def _read(path): return json.loads(Path(path).read_text(encoding="utf-8"))

def build_plan(root,route_path,*,occurrence_budget_usd_micros,per_job_budget_usd_micros):
    root=_root(root)
    route,route_sha=motion_organ.load_route(root,route_path)
    request,_=motion_organ.load_request(root,motion_organ._request_path(root,route["requestSha256"]))
    occurrence_budget_usd_micros=int(occurrence_budget_usd_micros)
    per_job_budget_usd_micros=int(per_job_budget_usd_micros)
    if occurrence_budget_usd_micros<0 or per_job_budget_usd_micros<0:
        raise ValueError("Budgets must be nonnegative")
    if per_job_budget_usd_micros>occurrence_budget_usd_micros:
        raise ValueError("Per-job budget cannot exceed occurrence budget")
    attempts=[]
    for item in route["attempts"]:
        attempts.append({
            "attempt":int(item["attempt"]),
            "offerId":item["offerId"],"providerId":item["providerId"],"model":item["model"],
            "spendClass":item["spendClass"],"routeEstimatedUsdMicros":item.get("estimatedUsdMicros"),
            "phase":"needs_capabilities","capabilitiesReceiptSha256":None,"quoteReceiptSha256":None,
            "submitReceiptSha256":None,"statusReceiptSha256":None,"fetchReceiptSha256":None,
            "vendorRequestId":None,"candidateVideoSha256":None,
        })
    body={
        "schema":PLAN_SCHEMA,"requestSha256":route["requestSha256"],"routeSha256":route_sha,
        "sceneId":request["sceneId"],"windowId":request["windowId"],
        "windowDurationSeconds":request["durationSeconds"],
        "occurrenceBudgetUsdMicros":occurrence_budget_usd_micros,
        "perJobBudgetUsdMicros":per_job_budget_usd_micros,
        "attempts":attempts,
        "laws":[
            "DETERMINISTIC FILM REMAINS COMPLETE FALLBACK",
            "CAPABILITY BEFORE QUOTE BEFORE SUBMIT",
            "QUOTE GENERATED JOB, NOT EDITED APERTURE",
            "SUBMIT ONCE PER ATTEMPT",
            "AMBIGUOUS SUBMISSION => STOP AND RECONCILE",
            "FALLBACK ONLY AFTER DEFINITIVE FAILURE OR INELIGIBILITY",
            "CANDIDATE != ACCEPTANCE",
        ],
    }
    digest=_sha(body);path=_plan_path(root,digest);_save(path,body)
    state={
        "schema":STATE_SCHEMA,"planSha256":digest,"routeSha256":route_sha,
        "spentAuthorizedUsdMicros":0,"currentAttempt":1,"status":"ready","stopReason":None,
        "attempts":copy.deepcopy(attempts),
    }
    sd=_sha(state);sp=_state_path(root,sd);_save(sp,state)
    return {"plan":str(path),"planSha256":digest,"state":str(sp),"stateSha256":sd}

def load_plan(root,path):
    root=_root(root);p=Path(path).expanduser().resolve(strict=True);body=_read(p)
    if body.get("schema")!=PLAN_SCHEMA: raise ValueError("Unsupported execution plan")
    digest=_sha(body)
    if p!=_plan_path(root,digest): raise ValueError("Execution plan identity changed")
    motion_organ.load_route(root,motion_organ._route_path(root,body["routeSha256"]))
    return body,digest

def load_state(root,path):
    root=_root(root);p=Path(path).expanduser().resolve(strict=True);body=_read(p)
    if body.get("schema")!=STATE_SCHEMA: raise ValueError("Unsupported execution state")
    digest=_sha(body)
    if p!=_state_path(root,digest): raise ValueError("Execution state identity changed")
    return body,digest

def _write_next(root,state):
    root=_root(root);digest=_sha(state);path=_state_path(root,digest);_save(path,state)
    return {"state":str(path),"stateSha256":digest,"stateBody":state}

def next_action(root,plan_path,state_path):
    plan,pd=load_plan(root,plan_path);state,_=load_state(root,state_path)
    if state["planSha256"]!=pd: raise ValueError("State/plan mismatch")
    if state["status"] in {"complete","reconcile_required","exhausted","budget_blocked"}:
        return {"action":"STOP","status":state["status"],"reason":state.get("stopReason")}
    idx=state["currentAttempt"]-1
    if idx<0 or idx>=len(state["attempts"]):
        return {"action":"STOP","status":"exhausted","reason":"no attempts remain"}
    a=state["attempts"][idx]
    mapping={"needs_capabilities":"CAPABILITIES","needs_quote":"QUOTE","ready_to_submit":"SUBMIT",
             "submitted":"STATUS","running":"STATUS","needs_fetch":"FETCH","candidate_ready":"PRESENT"}
    if a["phase"] in mapping: return {"action":mapping[a["phase"]],"attempt":copy.deepcopy(a)}
    if a["phase"] in {"definitively_failed","ineligible"}: return {"action":"ADVANCE","attempt":copy.deepcopy(a)}
    if a["phase"] in {"timeout","unresolved"}:
        return {"action":"STOP","status":"reconcile_required","reason":"submitted job unresolved"}
    raise ValueError("Unknown execution phase")

def record_capabilities(root,plan_path,state_path,receipt):
    plan,_=load_plan(root,plan_path);state,_=load_state(root,state_path)
    a=state["attempts"][state["currentAttempt"]-1]
    if a["phase"]!="needs_capabilities": raise ValueError("Capabilities out of order")
    if receipt.get("schema")!=CAP_SCHEMA or receipt.get("offerId")!=a["offerId"]:
        raise ValueError("Capabilities receipt does not bind current offer")
    if receipt.get("providerId")!=a["providerId"] or receipt.get("model")!=a["model"]:
        raise ValueError("Capabilities provider/model mismatch")
    req,_=motion_organ.load_request(root,motion_organ._request_path(_root(root),plan["requestSha256"]))
    eligible=(receipt.get("available") is True and req["inputMode"] in set(receipt.get("inputModes") or [])
              and req["aspectRatio"] in set(receipt.get("aspectRatios") or [])
              and float(receipt.get("minSeconds",0))<=req["durationSeconds"]<=float(receipt.get("maxSeconds",0)))
    a["capabilitiesReceiptSha256"]=_sha(receipt);a["phase"]="needs_quote" if eligible else "ineligible"
    atlas_black_box.record_operational(
        root, kind="provider.capabilities",
        observed_at=str(receipt.get("observedAt") or "unspecified"),
        plan_sha256=_sha(plan), provider_id=a["providerId"], offer_id=a["offerId"], attempt=a["attempt"],
        facts={"available":bool(receipt.get("available")),"eligibleForRequest":bool(eligible),
               "minSeconds":receipt.get("minSeconds"),"maxSeconds":receipt.get("maxSeconds")}
    )
    return _write_next(root,state)

def record_quote(root,plan_path,state_path,receipt):
    plan,_=load_plan(root,plan_path);state,_=load_state(root,state_path)
    a=state["attempts"][state["currentAttempt"]-1]
    if a["phase"]!="needs_quote": raise ValueError("Quote out of order")
    if receipt.get("schema")!=QUOTE_SCHEMA or receipt.get("offerId")!=a["offerId"]:
        raise ValueError("Quote does not bind current offer")
    generated=float(receipt.get("generatedDurationSeconds",0))
    if generated+1e-9<plan["windowDurationSeconds"]: raise ValueError("Generated duration cannot cover aperture")
    denomination=receipt.get("denomination");usd=receipt.get("wholeJobUsdMicros")
    if denomination=="USD":
        if not isinstance(usd,int) or usd<0: raise ValueError("USD quote requires wholeJobUsdMicros")
    elif denomination not in {"provider-credits","compute-seconds","tokens","units","video"}:
        raise ValueError("Unknown quote denomination")
    if receipt.get("exactConfiguration") is not True: raise ValueError("Execution requires exact-config quote")
    if usd is not None:
        if not isinstance(usd,int) or usd<0: raise ValueError("Invalid whole-job USD amount")
        if usd>plan["perJobBudgetUsdMicros"] or state["spentAuthorizedUsdMicros"]+usd>plan["occurrenceBudgetUsdMicros"]:
            a["quoteReceiptSha256"]=_sha(receipt);a["phase"]="budget_blocked"
            state["status"]="budget_blocked";state["stopReason"]="quote exceeds explicit budget"
            atlas_black_box.record_operational(
                root, kind="provider.quote",
                observed_at=str(receipt.get("observedAt") or "unspecified"),
                plan_sha256=_sha(plan), provider_id=a["providerId"], offer_id=a["offerId"], attempt=a["attempt"],
                facts={"denomination":denomination,"wholeJobUsdMicros":usd,
                       "generatedDurationSeconds":generated,"exactConfiguration":True,
                       "budgetAllowed":False}
            )
            return _write_next(root,state)
    elif a["spendClass"]=="paid":
        raise ValueError("Paid execution requires exact whole-job USD quote")
    a["quoteReceiptSha256"]=_sha(receipt);a["quotedUsdMicros"]=usd
    a["generatedDurationSeconds"]=generated;a["phase"]="ready_to_submit"
    atlas_black_box.record_operational(
        root, kind="provider.quote",
        observed_at=str(receipt.get("observedAt") or "unspecified"),
        plan_sha256=_sha(plan), provider_id=a["providerId"], offer_id=a["offerId"], attempt=a["attempt"],
        facts={"denomination":denomination,"wholeJobUsdMicros":usd,
               "generatedDurationSeconds":generated,"exactConfiguration":True,
               "budgetAllowed":True}
    )
    return _write_next(root,state)

def record_submit(root,plan_path,state_path,receipt):
    plan,_=load_plan(root,plan_path);state,_=load_state(root,state_path)
    a=state["attempts"][state["currentAttempt"]-1]
    if a["phase"]!="ready_to_submit" or a["submitReceiptSha256"] is not None:
        raise ValueError("Submission is not allowed or already recorded")
    if receipt.get("schema")!=SUBMIT_SCHEMA or receipt.get("offerId")!=a["offerId"]:
        raise ValueError("Submit receipt does not bind current offer")
    vendor=str(receipt.get("vendorRequestId") or "")
    if not vendor or not receipt.get("submittedParameterSha256"): raise ValueError("Submission identity required")
    a["submitReceiptSha256"]=_sha(receipt);a["vendorRequestId"]=vendor;a["phase"]="submitted"
    usd=a.get("quotedUsdMicros")
    if isinstance(usd,int): state["spentAuthorizedUsdMicros"]+=usd
    atlas_black_box.record_operational(
        root, kind="provider.submit",
        observed_at=str(receipt.get("observedAt") or "unspecified"),
        plan_sha256=_sha(plan), provider_id=a["providerId"], offer_id=a["offerId"], attempt=a["attempt"],
        facts={"vendorRequestIdSha256":hashlib.sha256(vendor.encode("utf-8")).hexdigest(),
               "submittedParameterSha256":receipt.get("submittedParameterSha256"),
               "authorizedUsdMicros":usd}
    )
    return _write_next(root,state)

def record_status(root,plan_path,state_path,receipt):
    plan,_=load_plan(root,plan_path);state,_=load_state(root,state_path)
    a=state["attempts"][state["currentAttempt"]-1]
    if a["phase"] not in {"submitted","running","timeout","unresolved"}: raise ValueError("Status receipt out of order")
    if receipt.get("schema")!=STATUS_SCHEMA or receipt.get("offerId")!=a["offerId"] or receipt.get("vendorRequestId")!=a["vendorRequestId"]:
        raise ValueError("Status receipt does not bind current job")
    status=receipt.get("status")
    if status not in {"running","completed","definitively_failed","cancelled","timeout","unresolved"}:
        raise ValueError("Unknown provider status")
    a["statusReceiptSha256"]=_sha(receipt)
    if status=="completed": a["phase"]="needs_fetch"
    elif status in {"definitively_failed","cancelled"}: a["phase"]="definitively_failed"
    elif status=="running": a["phase"]="running"
    else:
        a["phase"]=status;state["status"]="reconcile_required";state["stopReason"]="submitted job unresolved"
    atlas_black_box.record_operational(
        root, kind="provider.status",
        observed_at=str(receipt.get("observedAt") or "unspecified"),
        plan_sha256=_sha(plan), provider_id=a["providerId"], offer_id=a["offerId"], attempt=a["attempt"],
        facts={"status":status,"queueSeconds":receipt.get("queueSeconds"),
               "runtimeSeconds":receipt.get("runtimeSeconds")}
    )
    return _write_next(root,state)

def advance(root,plan_path,state_path):
    plan,_=load_plan(root,plan_path);state,_=load_state(root,state_path)
    a=state["attempts"][state["currentAttempt"]-1]
    if a["phase"] not in {"definitively_failed","ineligible"}: raise ValueError("Fallback requires definitive failure or ineligibility")
    nxt=state["currentAttempt"]+1
    if nxt>len(state["attempts"]):
        state["status"]="exhausted";state["stopReason"]="all route attempts exhausted"
    else: state["currentAttempt"]=nxt
    return _write_next(root,state)

def record_fetch(root,plan_path,state_path,receipt):
    plan,_=load_plan(root,plan_path);state,_=load_state(root,state_path)
    a=state["attempts"][state["currentAttempt"]-1]
    if a["phase"]!="needs_fetch": raise ValueError("Fetch receipt out of order")
    if receipt.get("schema")!=FETCH_SCHEMA or receipt.get("offerId")!=a["offerId"] or receipt.get("vendorRequestId")!=a["vendorRequestId"]:
        raise ValueError("Fetch receipt does not bind current job")
    sha=str(receipt.get("outputSha256") or "")
    if len(sha)!=64: raise ValueError("Candidate SHA-256 required")
    if float(receipt.get("durationSeconds",0))+0.05<plan["windowDurationSeconds"]:
        raise ValueError("Fetched candidate too short")
    a["fetchReceiptSha256"]=_sha(receipt);a["candidateVideoSha256"]=sha;a["phase"]="candidate_ready"
    state["status"]="candidate_ready"
    atlas_black_box.record_operational(
        root, kind="provider.fetch",
        observed_at=str(receipt.get("observedAt") or "unspecified"),
        plan_sha256=_sha(plan), provider_id=a["providerId"], offer_id=a["offerId"], attempt=a["attempt"],
        facts={"outputSha256":sha,"durationSeconds":receipt.get("durationSeconds"),
               "width":receipt.get("width"),"height":receipt.get("height"),
               "container":receipt.get("container"),"codec":receipt.get("codec")}
    )
    return _write_next(root,state)
