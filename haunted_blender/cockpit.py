from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from . import atlas_black_box

SCHEMA = "haunted-blender/cockpit-project/v1"
SECTION_SCHEMA = "haunted-blender/cockpit-section/v1"
STATUS = {"sleeping","dreaming","kept","moving","awakening","witnessed","alive","haunted"}

def _canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")

def _sha(value):
    return hashlib.sha256(_canonical(value)).hexdigest()

def _project_path(root):
    return root / "cockpit.project.json"

def _save(root,value):
    path=_project_path(root)
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return {"path":str(path),"projectSha256":_sha(value),"project":value}

def create_project(root,*,project_id,title,track_id=None,local_only=True):
    root=Path(root).expanduser().resolve()
    root.mkdir(parents=True,exist_ok=True)
    if not project_id or not title:
        raise ValueError("project_id and title are required")
    if _project_path(root).exists():
        raise FileExistsError("Cockpit project already exists")
    body={
        "schema":SCHEMA,
        "projectId":project_id,
        "title":title,
        "trackId":track_id,
        "localOnly":bool(local_only),
        "sections":[],
        "resume":{"unresolvedProviderJobs":0,"unbornSixups":0,"keptScenesAwaitingRender":0},
        "currentCut":[],
        "laws":[
            "COMPLEXITY UNDERNEATH, FOUR VERBS ON TOP",
            "LOCAL ONLY MEANS NO REMOTE EXECUTION",
            "WATCHING != KEEP",
            "KEEP != RELEASE",
            "AWAKEN != ACCEPT",
        ],
    }
    return _save(root,body)

def load_project(root):
    path=_project_path(Path(root).expanduser().resolve())
    if not path.is_file():
        raise FileNotFoundError("Cockpit project does not exist")
    body=json.loads(path.read_text(encoding="utf-8"))
    if body.get("schema")!=SCHEMA:
        raise ValueError("Unsupported Cockpit project")
    return body

def add_section(root,*,section_id,kind,start,end,label=None):
    root=Path(root).expanduser().resolve()
    project=load_project(root)
    if any(s["id"]==section_id for s in project["sections"]):
        raise ValueError("Section already exists")
    start=float(start);end=float(end)
    if start<0 or end<=start:
        raise ValueError("Invalid section timing")
    section={
        "schema":SECTION_SCHEMA,
        "id":section_id,
        "kind":kind,
        "label":label or kind,
        "start":start,
        "end":end,
        "temperature":"sleeping",
        "dreamEcologyId":None,
        "keptProposalId":None,
        "sceneId":None,
        "awakeningWindows":[],
        "acceptedVideoAddresses":[],
        "hauntIds":[],
        "witnessed":False,
    }
    project["sections"].append(section)
    project["sections"].sort(key=lambda s:(s["start"],s["id"]))
    return _save(root,project)

def _section(project,section_id):
    item=next((s for s in project["sections"] if s["id"]==section_id),None)
    if item is None:
        raise ValueError("Unknown section")
    return item

def action_grow(root,section_id,*,ecology_id):
    root=Path(root).expanduser().resolve();project=load_project(root);section=_section(project,section_id)
    if section["temperature"] not in {"sleeping","haunted"}:
        raise ValueError("GROW requires a sleeping or haunted section")
    section["temperature"]="dreaming";section["dreamEcologyId"]=ecology_id
    project["resume"]["unbornSixups"]+=1
    return _save(root,project)

def action_keep(root,section_id,*,proposal_id,scene_id=None):
    root=Path(root).expanduser().resolve();project=load_project(root);section=_section(project,section_id)
    if section["temperature"]!="dreaming":
        raise ValueError("KEEP requires a dreaming section")
    section["temperature"]="kept";section["keptProposalId"]=proposal_id;section["sceneId"]=scene_id
    project["resume"]["unbornSixups"]=max(0,project["resume"]["unbornSixups"]-1)
    project["resume"]["keptScenesAwaitingRender"]+=1
    return _save(root,project)

def action_scene_rendered(root,section_id,*,scene_id):
    root=Path(root).expanduser().resolve();project=load_project(root);section=_section(project,section_id)
    if section["temperature"]!="kept":
        raise ValueError("Scene render requires a kept section")
    section["temperature"]="moving";section["sceneId"]=scene_id
    project["resume"]["keptScenesAwaitingRender"]=max(0,project["resume"]["keptScenesAwaitingRender"]-1)
    return _save(root,project)

def action_awaken(root,section_id,*,window_id):
    root=Path(root).expanduser().resolve();project=load_project(root)
    if project["localOnly"]:
        raise ValueError("Cockpit is LOCAL ONLY; remote awakening is disabled")
    section=_section(project,section_id)
    if section["temperature"] not in {"moving","witnessed","alive"}:
        raise ValueError("AWAKEN requires an existing moving scene")
    section["temperature"]="awakening"
    if window_id not in section["awakeningWindows"]:
        section["awakeningWindows"].append(window_id)
    project["resume"]["unresolvedProviderJobs"]+=1
    return _save(root,project)

def action_witness(root,section_id,*,video_address):
    root=Path(root).expanduser().resolve();project=load_project(root);section=_section(project,section_id)
    if section["temperature"]!="awakening":
        raise ValueError("Witness requires an awakening section")
    section["temperature"]="witnessed";section["witnessed"]=True
    if video_address not in section["acceptedVideoAddresses"]:
        section["acceptedVideoAddresses"].append(video_address)
    project["resume"]["unresolvedProviderJobs"]=max(0,project["resume"]["unresolvedProviderJobs"]-1)
    return _save(root,project)

def action_alive(root,section_id):
    root=Path(root).expanduser().resolve();project=load_project(root);section=_section(project,section_id)
    if section["temperature"] not in {"moving","witnessed"}:
        raise ValueError("ALIVE requires a moving or witnessed section")
    section["temperature"]="alive"
    if section_id not in project["currentCut"]:
        project["currentCut"].append(section_id)
    return _save(root,project)

def action_haunt(root,section_id,*,haunt_id):
    root=Path(root).expanduser().resolve();project=load_project(root);section=_section(project,section_id)
    if haunt_id not in section["hauntIds"]:
        section["hauntIds"].append(haunt_id)
    if section["temperature"]=="sleeping":
        section["temperature"]="haunted"
    return _save(root,project)

def set_local_only(root,enabled):
    root=Path(root).expanduser().resolve();project=load_project(root)
    project["localOnly"]=bool(enabled)
    return _save(root,project)

def cockpit_view(root):
    project=load_project(root)
    return {
        "projectId":project["projectId"],
        "title":project["title"],
        "verbs":["GROW","KEEP","AWAKEN","PLAY"],
        "localOnly":project["localOnly"],
        "costLight":{"deterministic":"green","included":"yellow","paid":"red"},
        "sections":[
            {
                "id":s["id"],"label":s["label"],"kind":s["kind"],"start":s["start"],"end":s["end"],
                "temperature":s["temperature"],"hasDreams":s["dreamEcologyId"] is not None,
                "hasScene":s["sceneId"] is not None,"awakeningCount":len(s["awakeningWindows"]),
                "acceptedMotionCount":len(s["acceptedVideoAddresses"]),"hauntCount":len(s["hauntIds"]),
                "witnessed":s["witnessed"],
            } for s in project["sections"]
        ],
        "resume":copy.deepcopy(project["resume"]),
    }

def resume_summary(root):
    project=load_project(root)
    try:
        black_box=atlas_black_box.summarize(root)
    except Exception:
        black_box=None
    return {
        "projectId":project["projectId"],"title":project["title"],"localOnly":project["localOnly"],
        "resume":copy.deepcopy(project["resume"]),
        "sections":[{"id":s["id"],"label":s["label"],"temperature":s["temperature"],
                     "start":s["start"],"end":s["end"]} for s in project["sections"]],
        "currentCut":list(project["currentCut"]),"blackBox":black_box,
    }
