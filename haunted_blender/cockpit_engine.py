"""FRANKEN BLENDER 008b — automatic Cockpit engine crossings.

The artist-facing verbs stop asking for internal engine identities:

GROW    -> DREAMBREEDER ecology + deterministic six-up
KEEP    -> explicit proposal slot -> KEEP -> deterministic section scene
AWAKEN  -> bounded Motion Organ request + offer route + 007 execution plan
PLAY    -> derived current-cut preview

The module does not submit a remote provider job. AWAKEN prepares the already
bounded and budgeted 006/007 execution state; provider adapters remain separate.
"""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from . import cockpit, cockpit_media, dreambreeder, motion_executor, motion_organ, plugin_orchard, scene_growth
from .dream_cutout_compiler import KIT_SCHEMA, render_sixup

CONFIG_SCHEMA = "haunted-blender/cockpit-engine-config/v1"
ENGINE_STATE_SCHEMA = "haunted-blender/cockpit-engine-state/v1"


def _root(root) -> Path:
    return Path(root).expanduser().resolve()


def _digest_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _config_path(root: Path) -> Path:
    return root / "cockpit.engine.json"


def _safe_path(root: Path, value: str | Path, *, must_exist: bool = True) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    path = path.expanduser().resolve(strict=must_exist)
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError("Cockpit engine paths must stay inside the project root") from exc
    return path


def _section(project: dict, section_id: str) -> dict:
    item = next((s for s in project.get("sections", []) if s.get("id") == section_id), None)
    if item is None:
        raise ValueError("Unknown Cockpit section")
    return item


def _derived(root: Path, section_id: str) -> Path:
    path = root / "cockpit-derived" / section_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def _engine_state(section: dict) -> dict:
    state = section.get("engine")
    if not isinstance(state, dict):
        state = {
            "schema": ENGINE_STATE_SCHEMA,
            "ecologyPath": None,
            "sixupIndexPath": None,
            "keepPath": None,
            "timingPath": None,
            "scenePath": None,
            "sceneReceiptPath": None,
            "motionRequestPath": None,
            "motionOffersPath": None,
            "motionRoutePath": None,
            "motionPlanPath": None,
            "motionStatePath": None,
            "motionWindowId": None,
        }
        section["engine"] = state
    return state


def configure_project(
    root,
    *,
    source_receipt_ids: list[str],
    kit_path: str,
    motion_offers_path: str | None = None,
    lyrics_path: str | None = None,
    audio_path: str | None = None,
    common_checkpoint_id: str | None = None,
    fps: int = 12,
    preview_seconds: float = 2.0,
    occurrence_budget_usd_micros: int = 100_000,
    per_job_budget_usd_micros: int = 50_000,
) -> dict:
    root = _root(root)
    project = cockpit.load_project(root)
    receipts = [str(v).strip() for v in source_receipt_ids if str(v).strip()]
    if not receipts:
        raise ValueError("At least one real source receipt id is required")
    if int(fps) < 1:
        raise ValueError("fps must be positive")
    if float(preview_seconds) <= 0:
        raise ValueError("preview_seconds must be positive")
    if int(occurrence_budget_usd_micros) < 0 or int(per_job_budget_usd_micros) < 0:
        raise ValueError("budgets must be nonnegative")
    if int(per_job_budget_usd_micros) > int(occurrence_budget_usd_micros):
        raise ValueError("per-job budget cannot exceed occurrence budget")

    kit = _safe_path(root, kit_path)
    if json.loads(kit.read_text(encoding="utf-8")).get("schema") != KIT_SCHEMA:
        raise ValueError("kit_path must point to a haunted-blender/cutout-kit/v1 JSON file")

    offers = None
    if motion_offers_path:
        offers = _safe_path(root, motion_offers_path)
        if json.loads(offers.read_text(encoding="utf-8")).get("schema") != motion_organ.OFFERS_SCHEMA:
            raise ValueError("motion_offers_path must point to motion-provider-offers/v1 JSON")

    lyrics = _safe_path(root, lyrics_path) if lyrics_path else None
    if lyrics and json.loads(lyrics.read_text(encoding="utf-8")).get("schema") != "full-measure.lyrics.v1":
        raise ValueError("lyrics_path must point to full-measure.lyrics.v1 JSON")

    audio = _safe_path(root, audio_path) if audio_path else None

    body = {
        "schema": CONFIG_SCHEMA,
        "sourceReceiptIds": sorted(set(receipts)),
        "commonCheckpointId": common_checkpoint_id or f"cockpit-checkpoint:{project['projectId']}",
        "kitPath": str(kit.relative_to(root)),
        "motionOffersPath": str(offers.relative_to(root)) if offers else None,
        "lyricsPath": str(lyrics.relative_to(root)) if lyrics else None,
        "audioPath": str(audio.relative_to(root)) if audio else None,
        "fps": int(fps),
        "previewSeconds": float(preview_seconds),
        "occurrenceBudgetUsdMicros": int(occurrence_budget_usd_micros),
        "perJobBudgetUsdMicros": int(per_job_budget_usd_micros),
        "laws": [
            "ENGINE CONFIG != EDITORIAL DECISION",
            "SOURCE RECEIPT ID != SOURCE BYTES",
            "LOCAL ONLY STILL GOVERNS REMOTE AWAKEN",
            "AUTO ROUTE != AUTO SUBMIT",
        ],
    }
    _config_path(root).write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return body


def load_config(root) -> dict:
    root = _root(root)
    path = _config_path(root)
    if not path.is_file():
        raise FileNotFoundError("Cockpit engine is not configured; create cockpit.engine.json first")
    body = json.loads(path.read_text(encoding="utf-8"))
    if body.get("schema") != CONFIG_SCHEMA:
        raise ValueError("Unsupported Cockpit engine config")
    return body


def _load_kit(root: Path, config: dict) -> dict:
    path = _safe_path(root, config["kitPath"])
    kit = json.loads(path.read_text(encoding="utf-8"))
    if kit.get("schema") != KIT_SCHEMA:
        raise ValueError("Configured cutout kit schema changed")
    kit = copy.deepcopy(kit)
    for layer in kit.get("layers") or []:
        source = Path(str(layer.get("source") or ""))
        if not source.is_absolute():
            source = path.parent / source
        source = source.expanduser().resolve(strict=True)
        try:
            source.relative_to(root)
        except ValueError as exc:
            raise ValueError("Cutout kit layer escapes project root") from exc
        layer["source"] = str(source)
    return kit


def _load_global_lyrics(root: Path, config: dict) -> dict | None:
    value = config.get("lyricsPath")
    if not value:
        return None
    return json.loads(_safe_path(root, value).read_text(encoding="utf-8"))


def _local_lyrics(section: dict, lyrics: dict | None) -> dict | None:
    if lyrics is None:
        return None
    start, end = float(section["start"]), float(section["end"])
    cues = []
    for cue in lyrics.get("cues") or []:
        cue_start = float(cue.get("start", -1))
        if start <= cue_start < end:
            cue_end = max(cue_start, min(end, float(cue.get("end", cue_start))))
            cues.append({
                "start": round(cue_start - start, 6),
                "end": round(cue_end - start, 6),
                "text": str(cue.get("text") or ""),
            })
    return {"schema": "full-measure.lyrics.v1", "cues": cues}


def _section_timing(section: dict, lyrics: dict | None) -> dict:
    duration = round(float(section["end"]) - float(section["start"]), 6)
    track = {
        "schemaVersion": "0.1",
        "id": f"cockpit-section:{section['id']}",
        "duration": duration,
        "gates": [{
            "id": section["id"],
            "at": 0.0,
            "kind": section.get("kind") or "section",
            "label": section.get("label") or section.get("kind") or section["id"],
        }],
    }
    return scene_growth.normalize_timing(track, _local_lyrics(section, lyrics))


def _save_json(path: Path, value: dict) -> None:
    payload = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != value:
            raise ValueError(f"Existing derived engine state changed: {path.name}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def grow(root, section_id: str) -> dict:
    root = _root(root)
    config = load_config(root)
    project = cockpit.load_project(root)
    section = _section(project, section_id)
    if section["temperature"] not in {"sleeping", "haunted", "dreaming"}:
        raise ValueError("Automatic GROW requires a sleeping, haunted, or resumable dreaming section")
    state = _engine_state(section)
    folder = _derived(root, section_id)
    ecology_path = folder / "ecology.json"
    sixup_dir = folder / "sixup"
    sixup_index = sixup_dir / "six-up.json"

    ecology = dreambreeder.create_ecology(
        relation_id=f"cockpit:{project['projectId']}:{section_id}",
        common_checkpoint_id=config["commonCheckpointId"],
        source_receipt_ids=list(config["sourceReceiptIds"]),
    )
    _save_json(ecology_path, ecology)

    if sixup_index.is_file():
        sixup = json.loads(sixup_index.read_text(encoding="utf-8"))
        if sixup.get("ecologyId") != ecology["id"]:
            raise ValueError("Existing six-up belongs to another ecology")
    else:
        sixup = render_sixup(
            ecology,
            _load_kit(root, config),
            sixup_dir,
            duration=min(float(config["previewSeconds"]), max(0.5, float(section["end"]) - float(section["start"]))),
            fps=int(config["fps"]),
        )

    if section["temperature"] in {"sleeping", "haunted"}:
        cockpit.action_grow(root, section_id, ecology_id=ecology["id"])
    project = cockpit.load_project(root)
    section = _section(project, section_id)
    state = _engine_state(section)
    state["ecologyPath"] = str(ecology_path.relative_to(root))
    state["sixupIndexPath"] = str(sixup_index.relative_to(root))
    cockpit._save(root, project)

    cockpit_media.bind_media(
        root, section_id, kind="sixup", media_path=sixup["contactSheetVideo"],
        cost_class="deterministic", label="Six unborn futures",
    )
    return {
        "sectionId": section_id,
        "ecologyId": ecology["id"],
        "proposals": [
            {"slot": p["slot"], "label": p["label"], "traits": p["traits"], "proposalId": p["id"]}
            for p in ecology["proposals"]
        ],
        "sixupVideo": sixup["contactSheetVideo"],
        "authority": "proposal-preview-only",
    }


def keep(root, section_id: str, *, slot: int) -> dict:
    root = _root(root)
    config = load_config(root)
    project = cockpit.load_project(root)
    section = _section(project, section_id)
    if section["temperature"] not in {"dreaming", "kept"}:
        raise ValueError("Automatic KEEP requires a dreaming section or resumable kept section")
    state = _engine_state(section)
    folder = _derived(root, section_id)
    ecology_path = _safe_path(root, state.get("ecologyPath") or folder / "ecology.json")
    ecology = json.loads(ecology_path.read_text(encoding="utf-8"))
    proposal = next((p for p in ecology["proposals"] if int(p["slot"]) == int(slot)), None)
    if proposal is None:
        raise ValueError("KEEP slot must be one of the six visible proposals")

    keep_path = folder / "keep.json"
    if keep_path.is_file():
        keep_result = json.loads(keep_path.read_text(encoding="utf-8"))
        if keep_result.get("ecology", {}).get("disposition", {}).get("proposalId") != proposal["id"]:
            raise ValueError("A different proposal is already KEEP'd for this section")
    else:
        keep_result = dreambreeder.keep_proposal(ecology, proposal["id"])
        _save_json(keep_path, keep_result)

    if section["temperature"] == "dreaming":
        cockpit.action_keep(
            root, section_id, proposal_id=proposal["id"],
            scene_id=keep_result["descendant"]["id"],
        )

    project = cockpit.load_project(root)
    section = _section(project, section_id)
    timing = _section_timing(section, _load_global_lyrics(root, config))
    timing_path = folder / "timing.json"
    _save_json(timing_path, timing)

    scene_dir = folder / "scene"
    scene_json = scene_dir / "scene.json"
    if scene_json.is_file():
        grown = {
            "scene": json.loads(scene_json.read_text(encoding="utf-8")),
            "receipt": json.loads((scene_dir / "scene.receipt.json").read_text(encoding="utf-8")),
            "videoPath": str(scene_dir / "kept-scene.mp4"),
            "scenePath": str(scene_json),
            "receiptPath": str(scene_dir / "scene.receipt.json"),
        }
    else:
        grown = scene_growth.grow_kept_scene(
            keep_result,
            timing,
            _load_kit(root, config),
            scene_dir,
            fps=int(config["fps"]),
        )

    project = cockpit.load_project(root)
    section = _section(project, section_id)
    if section["temperature"] == "kept":
        cockpit.action_scene_rendered(root, section_id, scene_id=grown["scene"]["id"])
    cockpit_media.bind_media(
        root, section_id, kind="scene", media_path=grown["videoPath"],
        cost_class="deterministic", label=f"{section.get('label') or section_id} deterministic scene",
    )

    project = cockpit.load_project(root)
    section = _section(project, section_id)
    state = _engine_state(section)
    state["keepPath"] = str(keep_path.relative_to(root))
    state["timingPath"] = str(timing_path.relative_to(root))
    state["scenePath"] = str(Path(grown["scenePath"]).resolve().relative_to(root))
    state["sceneReceiptPath"] = str(Path(grown["receiptPath"]).resolve().relative_to(root))
    cockpit._save(root, project)

    return {
        "sectionId": section_id,
        "keptSlot": int(slot),
        "proposalLabel": proposal["label"],
        "descendantId": keep_result["descendant"]["id"],
        "sceneId": grown["scene"]["id"],
        "sceneVideo": grown["videoPath"],
        "awakeningWindows": list(grown["scene"].get("awakeningWindows") or []),
    }


def _extract_source_frame(scene_video: Path, output: Path, at_seconds: float) -> Path:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("FFmpeg is required for automatic AWAKEN source extraction")
    if output.is_file():
        return output
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-v", "error", "-ss", f"{float(at_seconds):.6f}",
            "-i", str(scene_video), "-frames:v", "1", "-vf", "format=rgb24", str(output),
        ],
        check=True,
    )
    return output


def _extract_source_window(
    scene_video: Path,
    output: Path,
    *,
    start_seconds: float,
    duration_seconds: float,
) -> Path:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("FFmpeg is required for automatic AWAKEN source extraction")
    if output.is_file():
        return output
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-v", "error", "-y",
            "-ss", f"{float(start_seconds):.6f}",
            "-i", str(scene_video),
            "-t", f"{float(duration_seconds):.6f}",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(output),
        ],
        check=True,
    )
    return output


def awaken(root, section_id: str) -> dict:
    root = _root(root)
    config = load_config(root)
    project = cockpit.load_project(root)
    if project.get("localOnly"):
        raise ValueError("LOCAL ONLY is enabled; automatic AWAKEN is locked")
    section = _section(project, section_id)
    if section["temperature"] not in {"moving", "alive", "awakening"}:
        raise ValueError("Automatic AWAKEN requires a moving/alive section or resumable awakening")
    state = _engine_state(section)
    folder = _derived(root, section_id)

    if state.get("motionPlanPath"):
        return engine_view(root, section_id)

    scene_path = _safe_path(root, state.get("scenePath") or folder / "scene" / "scene.json")
    receipt_path = _safe_path(root, state.get("sceneReceiptPath") or folder / "scene" / "scene.receipt.json")
    scene = json.loads(scene_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    windows = list(scene.get("awakeningWindows") or [])
    if not windows:
        raise ValueError("This section has no bounded chorus/bridge awakening window")
    window = windows[0]

    scene_video = _safe_path(root, folder / "scene" / "kept-scene.mp4")
    source_frame = _extract_source_frame(scene_video, folder / "motion-source.png", float(window["start"]))
    source_window = _extract_source_window(
        scene_video,
        folder / "motion-source.mp4",
        start_seconds=float(window["start"]),
        duration_seconds=float(window["duration"]),
    )
    source_sha = _digest_file(source_frame)

    keep_result = json.loads(_safe_path(root, state["keepPath"]).read_text(encoding="utf-8"))
    proposal_id = keep_result["ecology"]["disposition"]["proposalId"]
    proposal = next(p for p in keep_result["ecology"]["proposals"] if p["id"] == proposal_id)
    prompt = (
        f"Animate this bounded {section.get('kind')} moment for {section.get('label')}. "
        f"Motion grammar: {', '.join(proposal.get('motionGrammar') or ['subtle motion'])}. "
        "Preserve the composition and character identity; motion belongs only to this window."
    )

    request = motion_organ.freeze_request(
        root,
        scene_id=scene["id"],
        scene_sha256=receipt["outputSha256"],
        window_id=window["id"],
        start_seconds=float(window["start"]),
        duration_seconds=float(window["duration"]),
        prompt=prompt,
        source_address="sha256:" + source_sha,
        input_mode="image-to-video",
        aspect_ratio="16:9",
        source_assertion="operator_asserted_synthetic",
        remote_disclosure_approved=True,
    )

    orchard_offers = plugin_orchard.latest_offers_path(root)
    if orchard_offers is not None:
        motion_organ.load_offers(root, orchard_offers)
        offers = {"offers": str(orchard_offers)}
        offers_source = "plugin-orchard"
    else:
        offers_config = config.get("motionOffersPath")
        if not offers_config:
            raise ValueError(
                "Automatic AWAKEN needs a plugin-orchard snapshot or motionOffersPath in cockpit.engine.json"
            )
        offers_snapshot = json.loads(_safe_path(root, offers_config).read_text(encoding="utf-8"))
        offers = motion_organ.freeze_offers(root, offers_snapshot)
        offers_source = "engine-config"
    route = motion_organ.route_request(root, request["request"], offers["offers"])
    plan = motion_executor.build_plan(
        root,
        route["route"],
        occurrence_budget_usd_micros=int(config["occurrenceBudgetUsdMicros"]),
        per_job_budget_usd_micros=int(config["perJobBudgetUsdMicros"]),
    )

    if section["temperature"] in {"moving", "alive"}:
        cockpit.action_awaken(root, section_id, window_id=window["id"])

    project = cockpit.load_project(root)
    section = _section(project, section_id)
    state = _engine_state(section)
    state["motionRequestPath"] = str(Path(request["request"]).resolve().relative_to(root))
    state["motionOffersPath"] = str(Path(offers["offers"]).resolve().relative_to(root))
    state["motionOffersSource"] = offers_source
    state["motionRoutePath"] = str(Path(route["route"]).resolve().relative_to(root))
    state["motionPlanPath"] = str(Path(plan["plan"]).resolve().relative_to(root))
    state["motionStatePath"] = str(Path(plan["state"]).resolve().relative_to(root))
    state["motionWindowId"] = window["id"]
    state["motionSourceImagePath"] = str(source_frame.resolve().relative_to(root))
    state["motionSourceVideoPath"] = str(source_window.resolve().relative_to(root))
    cockpit._save(root, project)

    return {
        "sectionId": section_id,
        "window": window,
        "requestSha256": request["requestSha256"],
        "routeSha256": route["routeSha256"],
        "planSha256": plan["planSha256"],
        "sourceFrame": str(source_frame),
        "sourceDrivingClip": str(source_window),
        "next": motion_executor.next_action(root, plan["plan"], plan["state"]),
        "submitted": False,
        "laws": ["AUTO AWAKEN != AUTO SUBMIT", "ROUTE != PROVIDER AUTHORITY"],
    }


def _scene_media_paths(root: Path, project: dict) -> list[Path]:
    paths = []
    for section in project.get("sections") or []:
        media = cockpit_media.media_view(root, section["id"])
        scene = media.get("scene")
        if scene:
            paths.append(cockpit_media.resolve_media(root, scene["path"]))
    return paths


def play(root) -> dict:
    root = _root(root)
    config = load_config(root)
    project = cockpit.load_project(root)
    videos = _scene_media_paths(root, project)
    if not videos:
        raise ValueError("No deterministic/awakened scene media exists to preview")

    kit = _load_kit(root, config)
    width = int(kit["canvas"]["width"])
    height = int(kit["canvas"]["height"])
    fps = int(config["fps"])
    output_dir = root / "cockpit-derived"
    output_dir.mkdir(parents=True, exist_ok=True)
    raw = output_dir / "current-cut.video.mp4"
    final = output_dir / "current-cut.mp4"

    cmd = ["ffmpeg", "-v", "error", "-y"]
    for path in videos:
        cmd += ["-i", str(path)]
    filters = []
    labels = []
    for index in range(len(videos)):
        label = f"v{index}"
        filters.append(
            f"[{index}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,fps={fps},setsar=1[{label}]"
        )
        labels.append(f"[{label}]")
    filters.append("".join(labels) + f"concat=n={len(videos)}:v=1:a=0[outv]")
    cmd += ["-filter_complex", ";".join(filters), "-map", "[outv]", "-an",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(raw)]
    subprocess.run(cmd, check=True)

    audio_value = config.get("audioPath")
    if audio_value:
        audio = _safe_path(root, audio_value)
        subprocess.run(
            [
                "ffmpeg", "-v", "error", "-y", "-i", str(raw), "-i", str(audio),
                "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
                "-shortest", "-movflags", "+faststart", str(final),
            ],
            check=True,
        )
    else:
        shutil.copy2(raw, final)

    return {
        "preview": str(final),
        "relativePath": str(final.relative_to(root)),
        "sha256": _digest_file(final),
        "sectionCount": len(videos),
        "authority": "derived-preview-only",
        "laws": ["PLAY != KEEP", "PREVIEW CUT != RELEASE"],
    }


def engine_view(root, section_id: str) -> dict:
    root = _root(root)
    project = cockpit.load_project(root)
    section = _section(project, section_id)
    state = _engine_state(section)
    proposals = []
    if state.get("ecologyPath"):
        path = _safe_path(root, state["ecologyPath"])
        ecology = json.loads(path.read_text(encoding="utf-8"))
        proposals = [
            {"slot": p["slot"], "label": p["label"], "traits": p["traits"]}
            for p in ecology.get("proposals") or []
        ]
    kept_slot = None
    awakening_windows = []
    if state.get("keepPath"):
        keep_path = _safe_path(root, state["keepPath"])
        keep_result = json.loads(keep_path.read_text(encoding="utf-8"))
        kept_id = keep_result.get("ecology", {}).get("disposition", {}).get("proposalId")
        kept = next((p for p in keep_result.get("ecology", {}).get("proposals", []) if p.get("id") == kept_id), None)
        if kept:
            kept_slot = kept.get("slot")
    if state.get("scenePath"):
        scene_path = _safe_path(root, state["scenePath"])
        scene = json.loads(scene_path.read_text(encoding="utf-8"))
        awakening_windows = list(scene.get("awakeningWindows") or [])

    next_action = None
    if state.get("motionPlanPath") and state.get("motionStatePath"):
        next_action = motion_executor.next_action(
            root,
            _safe_path(root, state["motionPlanPath"]),
            _safe_path(root, state["motionStatePath"]),
        )
    return {
        "sectionId": section_id,
        "temperature": section["temperature"],
        "proposals": proposals,
        "keptSlot": kept_slot,
        "awakeningWindows": awakening_windows,
        "engine": copy.deepcopy(state),
        "nextMotionAction": next_action,
        "configured": _config_path(root).is_file(),
    }
