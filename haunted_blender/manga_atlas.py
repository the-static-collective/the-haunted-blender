"""FRANKEN BLENDER 008m — Manga / Anime Grammar Atlas.

Turns comic pages into provenance-aware panel maps, harvestable page parts, and
geometry-derived directing grammar.

Rights are explicit. Geometry analysis may run on a reference source, but pixel
extraction is refused unless the source manifest grants it.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from statistics import mean

SOURCE_SCHEMA = "haunted-blender/page-source/v1"
REPORT_SCHEMA = "haunted-blender/page-grammar-report/v1"
ATLAS_SCHEMA = "haunted-blender/manga-anime-grammar-atlas/v1"

SOURCE_CLASSES = {"owned", "licensed", "reference"}
GRAMMAR_FAMILIES = {
    "cozy-ensemble",
    "anime-action",
    "reaction",
    "panel-rhythm",
    "room-ecology",
    "fx",
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


def source_manifest(
    source_path: str | Path,
    *,
    source_class: str,
    pixel_reuse: bool,
    derivative_reuse: bool,
    publication_reuse: bool,
    grammar_families: list[str] | tuple[str, ...] = (),
    rights_note: str = "",
    label: str = "",
) -> dict:
    from PIL import Image

    source = Path(source_path).expanduser().resolve(strict=True)
    source_class = str(source_class).strip().lower()
    if source_class not in SOURCE_CLASSES:
        raise ValueError(f"source_class must be one of {sorted(SOURCE_CLASSES)}")
    families = sorted({str(x).strip() for x in grammar_families if str(x).strip()})
    unknown = [x for x in families if x not in GRAMMAR_FAMILIES]
    if unknown:
        raise ValueError(f"Unknown grammar families: {unknown}")

    if source_class == "reference" and (pixel_reuse or derivative_reuse or publication_reuse):
        raise ValueError("Reference-only source cannot grant pixel/derivative/publication reuse")
    if source_class in {"owned", "licensed"} and not rights_note.strip():
        raise ValueError("Owned/licensed sources require an explicit rights_note")

    with Image.open(source) as image:
        width, height = image.size

    body = {
        "schema": SOURCE_SCHEMA,
        "label": label or source.stem,
        "sourcePath": str(source),
        "sourceSha256": _file_sha(source),
        "width": int(width),
        "height": int(height),
        "sourceClass": source_class,
        "rights": {
            "pixelReuse": bool(pixel_reuse),
            "derivativeReuse": bool(derivative_reuse),
            "publicationReuse": bool(publication_reuse),
            "note": rights_note.strip(),
        },
        "grammarFamilies": families,
        "laws": [
            "SOURCE OWNERSHIP DETERMINES HARVEST AUTHORITY",
            "GRAMMAR ANALYSIS != PIXEL REUSE AUTHORITY",
            "REFERENCE SOURCE MAY INFORM GRAMMAR WITHOUT EXPORTING PIXELS",
        ],
    }
    return {**body, "id": "page-source:" + _hash(body)[:24]}


def _blank_ratio_rows(gray, box: tuple[int, int, int, int], *, threshold: int = 244) -> list[float]:
    x1, y1, x2, y2 = box
    px = gray.load()
    width = max(1, x2 - x1)
    values = []
    for y in range(y1, y2):
        blank = sum(1 for x in range(x1, x2) if px[x, y] >= threshold)
        values.append(blank / width)
    return values


def _blank_ratio_cols(gray, box: tuple[int, int, int, int], *, threshold: int = 244) -> list[float]:
    x1, y1, x2, y2 = box
    px = gray.load()
    height = max(1, y2 - y1)
    values = []
    for x in range(x1, x2):
        blank = sum(1 for y in range(y1, y2) if px[x, y] >= threshold)
        values.append(blank / height)
    return values


def _runs(values: list[float], *, min_ratio: float = 0.965, min_width: int = 3) -> list[tuple[int, int, float]]:
    runs = []
    start = None
    for i, value in enumerate(values + [0.0]):
        if value >= min_ratio and start is None:
            start = i
        elif value < min_ratio and start is not None:
            if i - start >= min_width:
                runs.append((start, i, mean(values[start:i])))
            start = None
    return runs


def _best_internal_gap(
    gray,
    box: tuple[int, int, int, int],
    *,
    min_panel_size: int,
) -> tuple[str, int, int, float] | None:
    x1, y1, x2, y2 = box
    w = x2 - x1
    h = y2 - y1
    candidates = []

    for start, end, score in _runs(
        _blank_ratio_cols(gray, box),
        min_width=max(3, round(w * 0.008)),
    ):
        absolute_start = x1 + start
        absolute_end = x1 + end
        if absolute_start - x1 >= min_panel_size and x2 - absolute_end >= min_panel_size:
            candidates.append(("vertical", absolute_start, absolute_end, score * (end - start)))

    for start, end, score in _runs(
        _blank_ratio_rows(gray, box),
        min_width=max(3, round(h * 0.008)),
    ):
        absolute_start = y1 + start
        absolute_end = y1 + end
        if absolute_start - y1 >= min_panel_size and y2 - absolute_end >= min_panel_size:
            candidates.append(("horizontal", absolute_start, absolute_end, score * (end - start)))

    if not candidates:
        return None
    candidates.sort(key=lambda row: row[3], reverse=True)
    return candidates[0]


def _trim_white(gray, box: tuple[int, int, int, int], *, threshold: int = 248) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = box
    px = gray.load()

    def row_has_ink(y):
        return any(px[x, y] < threshold for x in range(x1, x2))

    def col_has_ink(x):
        return any(px[x, y] < threshold for y in range(y1, y2))

    while y1 < y2 and not row_has_ink(y1):
        y1 += 1
    while y2 > y1 and not row_has_ink(y2 - 1):
        y2 -= 1
    while x1 < x2 and not col_has_ink(x1):
        x1 += 1
    while x2 > x1 and not col_has_ink(x2 - 1):
        x2 -= 1
    return x1, y1, x2, y2


def _longest_dark_run(values: list[bool]) -> int:
    best = 0
    current = 0
    for value in values:
        if value:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def _line_runs(
    values: list[float],
    *,
    threshold: float,
    bridge: int = 5,
) -> list[tuple[int, int, float]]:
    indexes = [i for i, value in enumerate(values) if value >= threshold]
    if not indexes:
        return []
    result = []
    start = previous = indexes[0]
    peak = values[start]
    for index in indexes[1:]:
        if index - previous <= bridge + 1:
            previous = index
            peak = max(peak, values[index])
        else:
            result.append((start, previous + 1, peak))
            start = previous = index
            peak = values[index]
    result.append((start, previous + 1, peak))
    return result


def _border_split_panels(
    gray,
    *,
    max_panels: int,
    min_panel_size: int,
    dark_threshold: int = 55,
    line_ratio: float = 0.40,
) -> list[tuple[int, int, int, int]]:
    """Fallback splitter for dark-bordered / low-gutter comic layouts.

    A candidate separator must contain a long *continuous* dark run rather than
    merely many dark pixels. This strongly prefers panel borders over text.
    """
    px = gray.load()
    width, height = gray.size
    leaves: list[tuple[int, int, int, int]] = []

    def split(box: tuple[int, int, int, int], depth: int = 0) -> None:
        x1, y1, x2, y2 = box
        w, h = x2 - x1, y2 - y1
        if (
            depth >= 8
            or len(leaves) >= max_panels
            or w < min_panel_size * 2
            or h < min_panel_size
        ):
            leaves.append(box)
            return

        row_strength = []
        for y in range(y1, y2):
            values = [px[x, y] < dark_threshold for x in range(x1, x2)]
            row_strength.append(_longest_dark_run(values) / max(1, w))

        col_strength = []
        for x in range(x1, x2):
            values = [px[x, y] < dark_threshold for y in range(y1, y2)]
            col_strength.append(_longest_dark_run(values) / max(1, h))

        candidates = []
        for start, end, peak in _line_runs(row_strength, threshold=line_ratio):
            a, b = y1 + start, y1 + end
            if a - y1 >= min_panel_size and y2 - b >= min_panel_size:
                candidates.append(("horizontal", a, b, peak * max(1, end - start)))

        for start, end, peak in _line_runs(col_strength, threshold=line_ratio):
            a, b = x1 + start, x1 + end
            if a - x1 >= min_panel_size and x2 - b >= min_panel_size:
                candidates.append(("vertical", a, b, peak * max(1, end - start)))

        if not candidates:
            leaves.append(box)
            return

        candidates.sort(key=lambda row: row[3], reverse=True)
        axis, start, end, _score = candidates[0]
        if axis == "horizontal":
            children = ((x1, y1, x2, start), (x1, end, x2, y2))
        else:
            children = ((x1, y1, start, y2), (end, y1, x2, y2))

        accepted = False
        for child in children:
            cx1, cy1, cx2, cy2 = child
            if cx2 - cx1 >= min_panel_size and cy2 - cy1 >= min_panel_size:
                split(child, depth + 1)
                accepted = True
        if not accepted:
            leaves.append(box)

    split((0, 0, width, height))
    unique = []
    seen = set()
    for box in leaves:
        if box not in seen:
            seen.add(box)
            unique.append(box)
    unique.sort(key=lambda box: (box[1], box[0]))
    return unique[:max_panels]


def segment_panels(
    source_path: str | Path,
    *,
    max_panels: int = 24,
    min_panel_fraction: float = 0.12,
) -> list[dict]:
    """Whitespace XY-cut panel segmentation.

    This is intentionally geometric, not semantic vision. It detects large
    gutter-separated regions and never claims which character/object a panel
    contains.
    """
    from PIL import Image, ImageOps

    source = Path(source_path).expanduser().resolve(strict=True)
    gray = ImageOps.grayscale(Image.open(source).convert("RGB"))
    width, height = gray.size
    min_panel_size = max(40, round(min(width, height) * min_panel_fraction))

    initial = _trim_white(gray, (0, 0, width, height))
    queue = [initial]
    leaves = []

    while queue and len(queue) + len(leaves) < max_panels * 2:
        box = queue.pop(0)
        x1, y1, x2, y2 = box
        if x2 - x1 < min_panel_size * 2 or y2 - y1 < min_panel_size:
            leaves.append(box)
            continue

        gap = _best_internal_gap(gray, box, min_panel_size=min_panel_size)
        if gap is None:
            leaves.append(box)
            continue

        axis, start, end, _score = gap
        if axis == "vertical":
            a = _trim_white(gray, (x1, y1, start, y2))
            b = _trim_white(gray, (end, y1, x2, y2))
        else:
            a = _trim_white(gray, (x1, y1, x2, start))
            b = _trim_white(gray, (x1, end, x2, y2))

        for child in (a, b):
            cx1, cy1, cx2, cy2 = child
            if cx2 - cx1 >= min_panel_size and cy2 - cy1 >= min_panel_size:
                queue.append(child)
            else:
                leaves.append(child)

        if len(leaves) >= max_panels:
            break

    leaves.extend(queue)
    unique = []
    seen = set()
    for box in leaves:
        x1, y1, x2, y2 = box
        if x2 <= x1 or y2 <= y1:
            continue
        key = tuple(round(v) for v in box)
        if key not in seen:
            seen.add(key)
            unique.append(key)

    unique.sort(key=lambda b: (b[1], b[0]))

    # The founding 008m specimens use heavy black borders and overlapping
    # manga composition. If whitespace XY-cut finds no useful subdivision,
    # fall back to continuous-border splitting rather than pretending the
    # entire page is one panel.
    if len(unique) <= 1:
        unique = _border_split_panels(
            gray,
            max_panels=max_panels,
            min_panel_size=min_panel_size,
        )

    page_area = max(1, width * height)
    result = []
    for i, (x1, y1, x2, y2) in enumerate(unique[:max_panels], start=1):
        w, h = x2 - x1, y2 - y1
        aspect = w / max(1, h)
        if aspect >= 1.45:
            geometry = "wide"
        elif aspect <= 0.72:
            geometry = "tall"
        elif w * h / page_area <= 0.08:
            geometry = "insert"
        else:
            geometry = "balanced"
        result.append({
            "id": f"panel-{i:03d}",
            "x": x1,
            "y": y1,
            "width": w,
            "height": h,
            "areaRatio": round((w * h) / page_area, 6),
            "aspectRatio": round(aspect, 6),
            "geometry": geometry,
        })
    return result


def _edge_density(image) -> float:
    from PIL import ImageFilter, ImageOps

    gray = ImageOps.grayscale(image.convert("RGB"))
    edge = gray.filter(ImageFilter.FIND_EDGES)
    hist = edge.histogram()
    total = max(1, sum(hist))
    high = sum(hist[72:])
    return high / total


def analyze_page(manifest: dict) -> dict:
    from PIL import Image

    if manifest.get("schema") != SOURCE_SCHEMA:
        raise ValueError("Expected page source manifest")

    source = Path(manifest["sourcePath"]).expanduser().resolve(strict=True)
    if _file_sha(source) != manifest["sourceSha256"]:
        raise ValueError("Page source bytes changed after manifest creation")

    panels = segment_panels(source)
    image = Image.open(source).convert("RGB")

    analyzed = []
    for panel in panels:
        box = (
            panel["x"],
            panel["y"],
            panel["x"] + panel["width"],
            panel["y"] + panel["height"],
        )
        crop = image.crop(box)
        density = _edge_density(crop)
        analyzed.append({
            **panel,
            "edgeDensity": round(density, 6),
            "cleanPlateCandidate": density <= 0.22,
        })

    geometry_sequence = [row["geometry"] for row in analyzed]
    body = {
        "schema": REPORT_SCHEMA,
        "sourceId": manifest["id"],
        "sourceSha256": manifest["sourceSha256"],
        "sourceClass": manifest["sourceClass"],
        "rights": manifest["rights"],
        "grammarFamilies": manifest.get("grammarFamilies") or [],
        "panelCount": len(analyzed),
        "panels": analyzed,
        "geometrySequence": geometry_sequence,
        "geometryCounts": {
            kind: sum(1 for row in analyzed if row["geometry"] == kind)
            for kind in ("wide", "tall", "balanced", "insert")
        },
        "meanPanelEdgeDensity": round(
            mean([row["edgeDensity"] for row in analyzed]) if analyzed else 0.0,
            6,
        ),
        "laws": [
            "PANEL MAP IS GEOMETRY, NOT SEMANTIC UNDERSTANDING",
            "WHITE GUTTER AND DARK BORDER DETECTION ARE BOTH HEURISTICS",
            "PANEL != FINAL FRAME",
            "PANEL RHYTHM != SHOT PLAN",
        ],
    }
    return {**body, "id": "page-grammar-report:" + _hash(body)[:24]}


def _panel_asset_rows(report: dict, source_path: Path, output_dir: Path) -> list[dict]:
    from PIL import Image, ImageFilter, ImageOps

    image = Image.open(source_path).convert("RGBA")
    assets = []
    for panel in report["panels"]:
        box = (
            panel["x"],
            panel["y"],
            panel["x"] + panel["width"],
            panel["y"] + panel["height"],
        )
        crop = image.crop(box)
        panel_dir = output_dir / panel["id"]
        panel_dir.mkdir(parents=True, exist_ok=True)

        full = panel_dir / "panel.png"
        crop.save(full)
        assets.append({
            "kind": "panel",
            "panelId": panel["id"],
            "path": str(full),
            "sha256": _file_sha(full),
            "recipe": {"op": "panel-crop", "box": list(box)},
        })

        # Useful non-semantic region crops: center and four quadrants.
        w, h = crop.size
        cw, ch = max(16, round(w * 0.62)), max(16, round(h * 0.62))
        anchors = {
            "center": ((w - cw) // 2, (h - ch) // 2),
            "nw": (0, 0),
            "ne": (max(0, w - cw), 0),
            "sw": (0, max(0, h - ch)),
            "se": (max(0, w - cw), max(0, h - ch)),
        }
        for name, (x, y) in anchors.items():
            region = crop.crop((x, y, x + cw, y + ch))
            out = panel_dir / f"region-{name}.png"
            region.save(out)
            assets.append({
                "kind": "region-candidate",
                "panelId": panel["id"],
                "path": str(out),
                "sha256": _file_sha(out),
                "recipe": {
                    "op": "panel-region-crop",
                    "anchor": name,
                    "box": [x, y, x + cw, y + ch],
                },
            })

        # Edge mask can later help a human/tool isolate figures or FX, but it is
        # explicitly not semantic segmentation.
        edge = ImageOps.grayscale(crop.convert("RGB")).filter(ImageFilter.FIND_EDGES)
        edge = ImageOps.autocontrast(edge)
        mask = edge.point(lambda p: 255 if p > 48 else 0)
        mask_rgba = Image.new("RGBA", crop.size, (255, 255, 255, 0))
        mask_rgba.putalpha(mask)
        mask_out = panel_dir / "edge-mask.png"
        mask_rgba.save(mask_out)
        assets.append({
            "kind": "edge-mask",
            "panelId": panel["id"],
            "path": str(mask_out),
            "sha256": _file_sha(mask_out),
            "recipe": {"op": "edge-mask", "semantic": False},
        })
    return assets


def harvest_page(manifest: dict, output_dir: str | Path) -> dict:
    if manifest.get("schema") != SOURCE_SCHEMA:
        raise ValueError("Expected page source manifest")
    rights = manifest.get("rights") or {}
    if not rights.get("pixelReuse") or not rights.get("derivativeReuse"):
        raise PermissionError("Page source does not authorize pixel/derivative harvesting")

    source = Path(manifest["sourcePath"]).expanduser().resolve(strict=True)
    if _file_sha(source) != manifest["sourceSha256"]:
        raise ValueError("Page source bytes changed after manifest creation")

    root = Path(output_dir).expanduser().resolve()
    if root.exists() and any(root.iterdir()):
        raise FileExistsError("Page harvest output directory must be empty")
    root.mkdir(parents=True, exist_ok=True)

    report = analyze_page(manifest)
    assets = _panel_asset_rows(report, source, root / "panels")
    for row in assets:
        row["sourceSha256"] = manifest["sourceSha256"]
        row["sourceId"] = manifest["id"]

    body = {
        "schema": "haunted-blender/page-harvest/v1",
        "sourceId": manifest["id"],
        "sourceSha256": manifest["sourceSha256"],
        "sourceClass": manifest["sourceClass"],
        "rights": manifest["rights"],
        "reportId": report["id"],
        "panelCount": report["panelCount"],
        "assetCount": len(assets),
        "assets": assets,
        "cost": {"externalGenerations": 0, "providerCredits": 0, "usdMicros": 0},
        "externalGenerations": 0,
        "providerCredits": 0,
        "usdMicros": 0,
        "laws": [
            "OWNED OR LICENSED PAGE MAY BE DISASSEMBLED",
            "HARVESTED ASSET != CHARACTER IDENTITY",
            "EDGE MASK != SEMANTIC SEGMENTATION",
            "PAGE MAY YIELD ACTORS FX PROPS AND BACKGROUNDS AFTER SELECTION",
        ],
    }
    result = {**body, "id": "page-harvest:" + _hash(body)[:24]}
    (root / "page-grammar-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (root / "page-harvest.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def build_atlas(reports: list[dict]) -> dict:
    if not reports:
        raise ValueError("Atlas requires at least one page report")
    families = {}
    all_sequences = []
    for report in reports:
        if report.get("schema") != REPORT_SCHEMA:
            raise ValueError("Unsupported page report")
        all_sequences.append({
            "reportId": report["id"],
            "sourceId": report["sourceId"],
            "families": report.get("grammarFamilies") or [],
            "sequence": report.get("geometrySequence") or [],
        })
        for family in report.get("grammarFamilies") or []:
            bucket = families.setdefault(
                family,
                {
                    "sourceReports": [],
                    "panelGeometryCounts": {
                        "wide": 0,
                        "tall": 0,
                        "balanced": 0,
                        "insert": 0,
                    },
                    "sequences": [],
                },
            )
            bucket["sourceReports"].append(report["id"])
            bucket["sequences"].append(report.get("geometrySequence") or [])
            for kind, count in (report.get("geometryCounts") or {}).items():
                bucket["panelGeometryCounts"][kind] = (
                    bucket["panelGeometryCounts"].get(kind, 0) + int(count)
                )

    body = {
        "schema": ATLAS_SCHEMA,
        "reportIds": [r["id"] for r in reports],
        "families": families,
        "sequences": all_sequences,
        "laws": [
            "ATLAS AGGREGATES GRAMMAR NOT OWNERSHIP",
            "OWNERSHIP DOES NOT TRANSFER BETWEEN SOURCES",
            "GEOMETRY PATTERN MAY GUIDE DIRECTION WITHOUT COPYING PIXELS",
        ],
    }
    return {**body, "id": "manga-anime-atlas:" + _hash(body)[:24]}


def director_prescription(report: dict) -> dict:
    if report.get("schema") != REPORT_SCHEMA:
        raise ValueError("Expected page grammar report")

    map_type = {
        "wide": "WIDE",
        "tall": "CLOSE_UP",
        "balanced": "SPEAKER",
        "insert": "INSERT",
    }
    shots = []
    previous = None
    for index, panel in enumerate(report.get("panels") or []):
        shot = map_type.get(panel["geometry"], "WIDE")
        if previous == shot:
            shot = "REACTION" if shot != "REACTION" else "RETURN"
        shots.append({
            "panelId": panel["id"],
            "panelGeometry": panel["geometry"],
            "suggestedShot": shot,
            "areaRatio": panel["areaRatio"],
            "cleanPlateCandidate": panel["cleanPlateCandidate"],
            "authority": "grammar-proposal-only",
        })
        previous = shot

    body = {
        "schema": "haunted-blender/page-to-director-prescription/v1",
        "reportId": report["id"],
        "sourceId": report["sourceId"],
        "shots": shots,
        "laws": [
            "PANEL RHYTHM MAY GUIDE SHOT RHYTHM",
            "PANEL GEOMETRY != REQUIRED CAMERA",
            "GRAMMAR PROPOSAL != EDITORIAL KEEP",
        ],
    }
    return {**body, "id": "page-director-prescription:" + _hash(body)[:24]}
