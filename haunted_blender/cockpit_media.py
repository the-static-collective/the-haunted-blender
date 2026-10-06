from __future__ import annotations

from pathlib import Path

from . import cockpit


MEDIA_KINDS = {"sixup", "scene", "candidate"}


def _root(root) -> Path:
    return Path(root).expanduser().resolve()


def _section(project: dict, section_id: str) -> dict:
    section = next((s for s in project.get("sections", []) if s.get("id") == section_id), None)
    if section is None:
        raise ValueError("Unknown section")
    return section


def _safe_relative_media(root: Path, media_path: str | Path) -> str:
    path = Path(media_path).expanduser().resolve(strict=True)
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise ValueError("Cockpit media must live inside the project root") from exc
    if path.suffix.lower() not in {".mp4", ".webm", ".mov", ".m4v"}:
        raise ValueError("Cockpit visual media must be a supported video file")
    return relative.as_posix()


def _media(section: dict) -> dict:
    value = section.get("media")
    if not isinstance(value, dict):
        value = {"sixup": None, "scene": None, "candidates": []}
        section["media"] = value
    value.setdefault("sixup", None)
    value.setdefault("scene", None)
    value.setdefault("candidates", [])
    return value


def bind_media(
    root,
    section_id: str,
    *,
    kind: str,
    media_path: str | Path,
    provider_id: str | None = None,
    offer_id: str | None = None,
    cost_class: str = "deterministic",
    label: str | None = None,
) -> dict:
    if kind not in MEDIA_KINDS:
        raise ValueError("Unsupported Cockpit media kind")
    if cost_class not in {"deterministic", "free", "included", "paid"}:
        raise ValueError("Unsupported Cockpit media cost class")

    root = _root(root)
    project = cockpit.load_project(root)
    section = _section(project, section_id)
    media = _media(section)
    relative = _safe_relative_media(root, media_path)

    if kind == "sixup":
        media["sixup"] = {"path": relative, "label": label or "Six futures"}
    elif kind == "scene":
        media["scene"] = {"path": relative, "label": label or "Current scene"}
    else:
        item = {
            "path": relative,
            "providerId": provider_id,
            "offerId": offer_id,
            "costClass": cost_class,
            "label": label or provider_id or "Candidate",
        }
        existing = next((x for x in media["candidates"] if x.get("path") == relative), None)
        if existing is None:
            media["candidates"].append(item)
        else:
            existing.update(item)

    return cockpit._save(root, project)


def media_view(root, section_id: str) -> dict:
    root = _root(root)
    project = cockpit.load_project(root)
    section = _section(project, section_id)
    media = _media(section)
    return {
        "sectionId": section_id,
        "sixup": media["sixup"],
        "scene": media["scene"],
        "candidates": list(media["candidates"]),
    }


def resolve_media(root, relative_path: str) -> Path:
    root = _root(root)
    requested = (root / relative_path).resolve(strict=True)
    try:
        requested.relative_to(root)
    except ValueError as exc:
        raise ValueError("Media path escapes Cockpit project root") from exc
    if not requested.is_file():
        raise ValueError("Media path is not a file")
    return requested
