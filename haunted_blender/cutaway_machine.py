"""FRANKEN BLENDER 008g — deterministic Cutaway Machine.

Consumes Weakest Window Doctor reports and creates abrupt local cutaway cards
before any provider escalation.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from . import weakest_window_doctor as doctor

SCHEMA = "haunted-blender/cutaway-plan/v1"

_KIND_BY_WEAKNESS = {
    "stasis": "reaction",
    "sourceOveruse": "lyric-sign",
    "recentRepetition": "prop-gag",
    "noveltyDeficit": "abrupt-sign",
    "transitionJolt": "establishing",
}


def _stable(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _hash(value: object) -> str:
    return hashlib.sha256(_stable(value)).hexdigest()


def _file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _nearest_lyric(timing: dict, at: float) -> str:
    cues = timing.get("lyricsCues") or []
    if not cues:
        return "..."
    cue = min(cues, key=lambda row: abs(float(row["start"]) - at))
    return str(cue.get("text") or "...").strip() or "..."


def plan_from_doctor(
    report: dict,
    timing: dict,
    *,
    max_cutaways: int = 6,
    duration_seconds: float = 1.25,
) -> dict:
    if report.get("schema") != doctor.REPORT_SCHEMA:
        raise ValueError("Expected Weakest Window Doctor report")
    if max_cutaways < 1 or max_cutaways > 24:
        raise ValueError("max_cutaways must be 1–24")
    duration_seconds = float(duration_seconds)
    if duration_seconds < 0.4 or duration_seconds > 3.0:
        raise ValueError("cutaway duration must be 0.4–3.0 seconds")

    by_id = {row["id"]: row for row in report["windows"]}
    entries = []
    for window_id in report["ranking"][:max_cutaways]:
        window = by_id[window_id]
        center = (float(window["start"]) + float(window["end"])) / 2
        start = max(float(window["start"]), center - duration_seconds / 2)
        end = min(float(window["end"]), start + duration_seconds)
        start = max(float(window["start"]), end - duration_seconds)
        kind = _KIND_BY_WEAKNESS.get(window["dominantWeakness"], "reaction")
        lyric = _nearest_lyric(timing, center)
        entries.append({
            "id": f"cutaway-{len(entries) + 1:03d}",
            "windowId": window_id,
            "weaknessScore": window["weaknessScore"],
            "dominantWeakness": window["dominantWeakness"],
            "kind": kind,
            "start": round(start, 6),
            "end": round(end, 6),
            "durationSeconds": round(max(0.0, end - start), 6),
            "text": lyric,
            "costClass": "local-repeatable-zero",
            "externalGenerations": 0,
            "providerCredits": 0,
            "usdMicros": 0,
        })

    body = {
        "schema": SCHEMA,
        "doctorReportId": report["id"],
        "timingId": timing.get("id"),
        "entries": entries,
        "laws": [
            "CUTAWAY BEFORE PROVIDER ESCALATION",
            "ABRUPTNESS MAY BE STYLE",
            "WEAK WINDOW != DELETED WINDOW",
            "CUTAWAY != NEW EVIDENCE",
        ],
    }
    return {**body, "id": "cutaway-plan:" + _hash(body)[:24]}


def _font(size: int):
    from PIL import ImageFont
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def render_card(
    entry: dict,
    output_path: str | Path,
    *,
    width: int,
    height: int,
) -> dict:
    from PIL import Image, ImageDraw

    out = Path(output_path).expanduser().resolve()
    if out.exists():
        raise FileExistsError("Cutaway card never overwrites")
    out.parent.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGBA", (width, height), (31, 31, 29, 255))
    draw = ImageDraw.Draw(image)
    kind = str(entry["kind"])
    paper = (236, 226, 196, 255)
    ink = (23, 23, 22, 255)
    accent = (181, 72, 66, 255)
    pale = (198, 199, 188, 255)

    if kind == "reaction":
        # Deadpan face built from construction-paper geometry.
        draw.ellipse((width * 0.22, height * 0.10, width * 0.78, height * 0.86), fill=paper, outline=ink, width=max(2, width // 180))
        draw.ellipse((width * 0.36, height * 0.33, width * 0.43, height * 0.43), fill=ink)
        draw.ellipse((width * 0.57, height * 0.33, width * 0.64, height * 0.43), fill=ink)
        draw.line((width * 0.40, height * 0.63, width * 0.60, height * 0.63), fill=ink, width=max(3, height // 80))
    elif kind == "lyric-sign":
        draw.rectangle((width * 0.08, height * 0.16, width * 0.92, height * 0.77), fill=paper, outline=ink, width=max(3, width // 150))
        draw.rectangle((width * 0.46, height * 0.77, width * 0.54, height), fill=(92, 63, 44, 255))
    elif kind == "prop-gag":
        # Deliberately generic weird box/television prop.
        draw.rectangle((width * 0.22, height * 0.20, width * 0.78, height * 0.78), fill=accent, outline=ink, width=max(3, width // 150))
        draw.rectangle((width * 0.29, height * 0.29, width * 0.67, height * 0.61), fill=(19, 21, 24, 255), outline=paper, width=2)
        draw.ellipse((width * 0.70, height * 0.34, width * 0.74, height * 0.38), fill=paper)
        draw.ellipse((width * 0.70, height * 0.43, width * 0.74, height * 0.47), fill=paper)
    elif kind == "establishing":
        draw.rectangle((0, height * 0.62, width, height), fill=(73, 61, 46, 255))
        draw.rectangle((width * 0.28, height * 0.28, width * 0.72, height * 0.65), fill=paper, outline=ink, width=3)
        draw.polygon(((width * 0.23, height * 0.30), (width * 0.50, height * 0.08), (width * 0.77, height * 0.30)), fill=accent, outline=ink)
    else:
        draw.rectangle((width * 0.05, height * 0.12, width * 0.95, height * 0.88), fill=pale, outline=ink, width=max(3, width // 150))
        draw.line((width * 0.05, height * 0.12, width * 0.95, height * 0.88), fill=accent, width=max(4, width // 100))
        draw.line((width * 0.95, height * 0.12, width * 0.05, height * 0.88), fill=accent, width=max(4, width // 100))

    text = str(entry.get("text") or "...")[:90]
    label = kind.replace("-", " ").upper()
    draw.text((12, 10), label, font=_font(max(14, width // 42)), fill=(248, 244, 230, 255))
    draw.multiline_text(
        (round(width * 0.10), round(height * 0.80)),
        text,
        font=_font(max(13, width // 48)),
        fill=(248, 244, 230, 255),
        spacing=3,
    )
    image.save(out)
    return {"path": str(out), "sha256": _file_sha(out), "kind": kind}


def card_layer(entry: dict, card: dict, *, duration: float, z: int) -> dict:
    start = max(0.0, min(duration, float(entry["start"])))
    end = max(start, min(duration, float(entry["end"])))
    epsilon = min(0.03, max(0.005, (end - start) * 0.08))
    return {
        "id": f"cutaway-card-{entry['id']}",
        "source": card["path"],
        "z": int(z),
        "x": 0,
        "y": 0,
        "opacity": 0.0,
        "keyframes": [
            {"time": 0.0, "opacity": 0.0},
            {"time": round(start, 6), "opacity": 0.0},
            {"time": round(min(end, start + epsilon), 6), "opacity": 1.0},
            {"time": round(max(start, end - epsilon), 6), "opacity": 1.0},
            {"time": round(end, 6), "opacity": 0.0},
            {"time": duration, "opacity": 0.0},
        ],
    }
