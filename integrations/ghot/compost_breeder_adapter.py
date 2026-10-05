#!/usr/bin/env python3
"""Bounded GHoT adapter for DREAMBREEDER 004.

Consumes one ghot.compost-breeder-request/v0 over stdin JSON, creates a real
DREAMBREEDER ecology, renders the six real deterministic cutout previews through
FRANKEN BLENDER 004, and returns donor-owned JSON evidence on stdout.

The adapter selects no proposal and performs no KEEP.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw  # noqa: E402
from haunted_blender.dream_cutout_compiler import KIT_SCHEMA, render_sixup  # noqa: E402
from haunted_blender.dreambreeder import create_ecology  # noqa: E402

REQUEST_SCHEMA = "ghot.compost-breeder-request/v0"
RESULT_SCHEMA = "haunted-blender/ghot-compost-breeder-result/v1"
CAPABILITY = "creative.blender.dreambreed.sixup"


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def require_text(value: Any, code: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(code)
    return value.strip()


def validate_request(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("schema") != REQUEST_SCHEMA:
        raise ValueError("UNSUPPORTED_COMPOST_BREEDER_REQUEST")
    if value.get("authority") != "proposal-request-only":
        raise ValueError("COMPOST_BREEDER_REQUEST_AUTHORITY_MISMATCH")
    if value.get("requestedEffect") != "GROW_SIX_UNBORN_FILM_PREVIEWS":
        raise ValueError("COMPOST_BREEDER_REQUEST_EFFECT_MISMATCH")

    parent = value.get("parentHistoryRef")
    if not isinstance(parent, dict) or parent.get("authority") != "provenance-only":
        raise ValueError("COMPOST_BREEDER_PARENT_HISTORY_REQUIRED")
    capsule_hash = require_text(
        parent.get("capsuleHash"), "COMPOST_BREEDER_PARENT_HASH_REQUIRED"
    )
    generation = parent.get("generation")
    if not isinstance(generation, int) or generation < 1:
        raise ValueError("COMPOST_BREEDER_PARENT_GENERATION_INVALID")

    relation_id = require_text(value.get("relationId"), "COMPOST_BREEDER_RELATION_REQUIRED")
    receipts = value.get("sourceReceiptIds")
    if (
        not isinstance(receipts, list)
        or not receipts
        or any(not isinstance(item, str) or not item.strip() for item in receipts)
    ):
        raise ValueError("COMPOST_BREEDER_RECEIPTS_REQUIRED")

    return {
        "schema": REQUEST_SCHEMA,
        "authority": "proposal-request-only",
        "parentHistoryRef": {
            "capsuleHash": capsule_hash,
            "generation": generation,
            "authority": "provenance-only",
        },
        "relationId": relation_id,
        "sourceReceiptIds": sorted(set(item.strip() for item in receipts)),
        "requestedEffect": "GROW_SIX_UNBORN_FILM_PREVIEWS",
    }


def palette(seed: str, offset: int) -> tuple[int, int, int, int]:
    start = (offset * 6) % (len(seed) - 6)
    raw = seed[start : start + 6]
    return (
        32 + int(raw[0:2], 16) % 180,
        32 + int(raw[2:4], 16) % 180,
        32 + int(raw[4:6], 16) % 180,
        255,
    )


def make_kit(root: Path, seed: str) -> dict[str, Any]:
    assets = root / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    width, height = 160, 90

    bg = Image.new("RGBA", (width, height), palette(seed, 0))
    draw = ImageDraw.Draw(bg)
    draw.rectangle((0, 63, width, height), fill=palette(seed, 1))
    draw.polygon([(0, 64), (48, 36), (86, 64)], fill=palette(seed, 2))
    draw.polygon([(66, 64), (124, 28), (160, 56), (160, 76)], fill=palette(seed, 3))
    bg.save(assets / "background.png")

    actor = Image.new("RGBA", (34, 54), (0, 0, 0, 0))
    ad = ImageDraw.Draw(actor)
    ad.ellipse((10, 1, 24, 15), fill=palette(seed, 4))
    ad.rectangle((8, 14, 26, 40), fill=palette(seed, 5))
    ad.polygon([(8, 38), (16, 53), (3, 53)], fill=palette(seed, 6))
    ad.polygon([(26, 38), (31, 53), (18, 53)], fill=palette(seed, 7))
    actor.save(assets / "actor.png")

    arm = Image.new("RGBA", (30, 12), (0, 0, 0, 0))
    ImageDraw.Draw(arm).rounded_rectangle(
        (0, 3, 29, 9), radius=3, fill=palette(seed, 8)
    )
    arm.save(assets / "arm.png")

    prop = Image.new("RGBA", (28, 38), (0, 0, 0, 0))
    pd = ImageDraw.Draw(prop)
    pd.rectangle((2, 3, 26, 36), fill=palette(seed, 9))
    pd.rectangle((6, 7, 22, 32), outline=palette(seed, 10), width=2)
    prop.save(assets / "door.png")

    light = Image.new("RGBA", (52, 52), (0, 0, 0, 0))
    ld = ImageDraw.Draw(light)
    light_color = palette(seed, 11)
    for radius in range(24, 3, -4):
        alpha = max(12, int(120 * (1 - radius / 28)))
        ld.ellipse(
            (26 - radius, 26 - radius, 26 + radius, 26 + radius),
            fill=(*light_color[:3], alpha),
        )
    light.save(assets / "light.png")

    kit = {
        "schema": KIT_SCHEMA,
        "canvas": {"width": width, "height": height},
        "layers": [
            {
                "id": "background",
                "role": "background",
                "source": str((assets / "background.png").resolve()),
                "z": 0,
                "x": 0,
                "y": 0,
            },
            {
                "id": "light",
                "role": "light",
                "source": str((assets / "light.png").resolve()),
                "z": 1,
                "x": 102,
                "y": 4,
                "opacity": 0.28,
            },
            {
                "id": "door",
                "role": "prop",
                "source": str((assets / "door.png").resolve()),
                "z": 2,
                "x": 124,
                "y": 45,
            },
            {
                "id": "actor",
                "role": "actor",
                "source": str((assets / "actor.png").resolve()),
                "z": 3,
                "x": 38,
                "y": 32,
            },
            {
                "id": "arm",
                "role": "arm-right",
                "source": str((assets / "arm.png").resolve()),
                "z": 4,
                "x": 57,
                "y": 54,
                "rotation": -8,
            },
        ],
    }
    return kit


def inline_artifact(name: str, value: Any) -> dict[str, str]:
    text = json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
    return {
        f"{name}_text": text,
        f"{name}_sha256": sha_text(text),
    }


def build_result(request: dict[str, Any]) -> dict[str, Any]:
    normalized = validate_request(request)
    request_hash = digest(normalized)
    out = ROOT / "output" / "ghot-compost-breeder" / request_hash[:24]
    result_path = out / "adapter-result.json"

    if result_path.is_file():
        cached = json.loads(result_path.read_text(encoding="utf-8"))
        if cached.get("requestSha256") != request_hash:
            raise RuntimeError("CACHED_COMPOST_BREEDER_REQUEST_MISMATCH")
        contact = Path(cached["sixup"]["contactSheetVideo"])
        if not contact.is_file():
            raise RuntimeError("CACHED_COMPOST_BREEDER_PREVIEW_MISSING")
        return cached

    out.mkdir(parents=True, exist_ok=False)
    kit = make_kit(out, request_hash)

    ecology = create_ecology(
        relation_id=normalized["relationId"],
        common_checkpoint_id=normalized["parentHistoryRef"]["capsuleHash"],
        source_receipt_ids=normalized["sourceReceiptIds"],
        generation=normalized["parentHistoryRef"]["generation"] + 1,
        donor_ids=[],
    )

    sixup = render_sixup(
        ecology,
        kit,
        out / "previews",
        duration=0.75,
        fps=8,
        donor_video_by_id=None,
    )

    artifact = {}
    artifact.update(inline_artifact("ecology", ecology))
    artifact.update(inline_artifact("sixup", sixup))

    result = {
        "schema": RESULT_SCHEMA,
        "capability": CAPABILITY,
        "authority": "donor-result-evidence",
        "requestSha256": request_hash,
        "ecology": ecology,
        "sixup": sixup,
        "artifact": artifact,
        "laws": [
            "PREVIEW != KEEP",
            "WATCHING != KEEP",
            "PREVIEW != HISTORY",
            "DONOR RESULT != GHOT SEMANTICS",
        ],
    }
    result_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        raise ValueError("COMPOST_BREEDER_REQUEST_REQUIRED")
    result = build_result(json.loads(raw))
    sys.stdout.write(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        sys.stderr.write(json.dumps({"error": f"{type(exc).__name__}: {exc}"}) + "\n")
        raise SystemExit(1)
