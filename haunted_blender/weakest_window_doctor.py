"""FRANKEN BLENDER 008f — Weakest Window Doctor.

A complete movie exists before this module begins.

The Doctor samples the actual rendered bytes, combines those observations with
008e source/reuse provenance, ranks weak windows, prescribes the cheapest
deterministic treatment first, and rescans the treated movie.

It never purchases or submits provider work.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import shutil
import subprocess
from pathlib import Path
from statistics import mean

from . import zero_dollar_mill

REPORT_SCHEMA = "haunted-blender/weakest-window-report/v1"
TREATMENT_SCHEMA = "haunted-blender/weakest-window-treatment/v1"

# Level-1 mutations only. Higher levels are recommendations, not automatic work.
LOCAL_RECIPE_LADDER = {
    "fit": ("kinetic-push", "push", "mirror", "reverse"),
    "mirror": ("push", "reverse", "soft-loop"),
    "reverse": ("push", "mirror", "fast"),
    "slow": ("fast", "push", "mirror-reverse"),
    "fast": ("slow", "push", "reverse"),
    "push": ("kinetic-push", "pull", "mirror", "misregister"),
    "pull": ("push", "mirror", "reverse"),
    "misregister": ("push", "mirror-reverse", "soft-loop"),
    "mirror-reverse": ("push", "pull", "soft-loop"),
    "soft-loop": ("kinetic-push", "push", "reverse", "misregister"),
}

WEIGHTS = {
    "stasis": 0.30,
    "sourceOveruse": 0.25,
    "recentRepetition": 0.20,
    "noveltyDeficit": 0.15,
    "transitionJolt": 0.10,
}


def _stable_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _sha(value: object) -> str:
    return hashlib.sha256(_stable_bytes(value)).hexdigest()


def _sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _probe_duration(path: Path) -> float:
    proc = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=nw=1:nk=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(proc.stdout.strip())


def _raw_frames(video: Path, *, fps: int = 4, width: int = 64, height: int = 36) -> list[bytes]:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("FFmpeg required")
    proc = subprocess.run(
        [
            "ffmpeg", "-nostdin", "-v", "error",
            "-i", str(video),
            "-vf", f"fps={int(fps)},scale={int(width)}:{int(height)},format=gray",
            "-f", "rawvideo", "-pix_fmt", "gray", "-",
        ],
        check=True,
        capture_output=True,
    )
    frame_size = int(width) * int(height)
    if frame_size <= 0 or len(proc.stdout) < frame_size:
        raise ValueError("Could not sample rendered movie")
    usable = len(proc.stdout) - (len(proc.stdout) % frame_size)
    data = proc.stdout[:usable]
    return [data[i:i + frame_size] for i in range(0, usable, frame_size)]


def _diff(a: bytes, b: bytes) -> float:
    if len(a) != len(b) or not a:
        raise ValueError("Frame dimensions changed during scan")
    return sum(abs(x - y) for x, y in zip(a, b)) / (len(a) * 255.0)


def _window_ranges(duration: float, window_seconds: float) -> list[tuple[float, float]]:
    if window_seconds < 1 or window_seconds > 10:
        raise ValueError("window_seconds must be between 1 and 10")
    count = int(math.ceil(duration / window_seconds))
    return [
        (
            round(i * window_seconds, 6),
            round(min(duration, (i + 1) * window_seconds), 6),
        )
        for i in range(count)
    ]


def _frames_for_window(
    frames: list[bytes],
    *,
    start: float,
    end: float,
    sample_fps: int,
) -> list[bytes]:
    first = max(0, int(math.floor(start * sample_fps)))
    last = min(len(frames), max(first + 1, int(math.ceil(end * sample_fps))))
    return frames[first:last]


def _normalize(values: list[float]) -> list[float]:
    if not values:
        return []
    lo, hi = min(values), max(values)
    if abs(hi - lo) < 1e-12:
        return [0.0 for _ in values]
    return [(value - lo) / (hi - lo) for value in values]


def _overlap(a0: float, a1: float, b0: float, b1: float) -> float:
    return max(0.0, min(a1, b1) - max(a0, b0))


def _slug_spans(plan: dict) -> list[dict]:
    cursor = 0.0
    rows = []
    for slug in plan.get("slugs") or []:
        duration = float(slug["durationSeconds"])
        rows.append({
            **slug,
            "timelineStart": round(cursor, 6),
            "timelineEnd": round(cursor + duration, 6),
        })
        cursor += duration
    return rows


def _window_sources(slugs: list[dict], start: float, end: float) -> list[dict]:
    rows = []
    for slug in slugs:
        overlap = _overlap(start, end, slug["timelineStart"], slug["timelineEnd"])
        if overlap > 0:
            rows.append({
                "slugId": slug["id"],
                "recipe": slug["recipe"],
                "sourceAssetId": slug["sourceAssetId"],
                "sourceSha256": slug["sourceSha256"],
                "seconds": round(overlap, 6),
            })
    return rows


def scan(
    video_path: str | Path,
    plan: dict,
    *,
    window_seconds: float = 4.0,
    sample_fps: int = 4,
) -> dict:
    if plan.get("schema") != zero_dollar_mill.PLAN_SCHEMA:
        raise ValueError("Weakest Window Doctor expects an 008e plan")
    video = Path(video_path).expanduser().resolve(strict=True)
    observed_duration = _probe_duration(video)
    target = float(plan["targetSeconds"])
    if observed_duration + 0.08 < target:
        raise ValueError("Doctor refuses to score a cut that lost target coverage")

    frames = _raw_frames(video, fps=sample_fps)
    ranges = _window_ranges(target, float(window_seconds))
    slugs = _slug_spans(plan)
    total_source_seconds: dict[str, float] = {}
    for slug in slugs:
        key = slug["sourceSha256"]
        total_source_seconds[key] = total_source_seconds.get(key, 0.0) + float(slug["durationSeconds"])

    raw_rows = []
    previous_first: bytes | None = None
    previous_last: bytes | None = None
    previous_sources: set[str] = set()

    for index, (start, end) in enumerate(ranges, start=1):
        wf = _frames_for_window(
            frames, start=start, end=end, sample_fps=sample_fps
        )
        if not wf:
            wf = [frames[min(len(frames) - 1, int(start * sample_fps))]]

        motion_pairs = [_diff(wf[i - 1], wf[i]) for i in range(1, len(wf))]
        motion_energy = mean(motion_pairs) if motion_pairs else 0.0
        source_rows = _window_sources(slugs, start, end)
        source_set = {row["sourceSha256"] for row in source_rows}
        window_duration = max(0.001, end - start)

        overuse = 0.0
        for source_sha in source_set:
            share = total_source_seconds.get(source_sha, 0.0) / max(0.001, target)
            overuse = max(overuse, share)

        recent_repetition = (
            len(source_set & previous_sources) / max(1, len(source_set | previous_sources))
            if previous_sources else 0.0
        )

        first = wf[0]
        last = wf[-1]
        transition_jolt = _diff(previous_last, first) if previous_last is not None else 0.0
        novelty = _diff(previous_first, first) if previous_first is not None else 1.0

        raw_rows.append({
            "index": index,
            "id": f"window-{index:04d}",
            "start": start,
            "end": end,
            "durationSeconds": round(window_duration, 6),
            "motionEnergy": round(motion_energy, 8),
            "sourceOveruseRaw": round(overuse, 8),
            "recentRepetitionRaw": round(recent_repetition, 8),
            "noveltyRaw": round(novelty, 8),
            "transitionJoltRaw": round(transition_jolt, 8),
            "sources": source_rows,
        })

        previous_first = first
        previous_last = last
        previous_sources = source_set

    motion = [row["motionEnergy"] for row in raw_rows]
    # Low motion is weak, so invert normalized motion.
    motion_norm = _normalize(motion)
    stasis = [1.0 - v for v in motion_norm]
    overuse = _normalize([row["sourceOveruseRaw"] for row in raw_rows])
    repetition = _normalize([row["recentRepetitionRaw"] for row in raw_rows])
    novelty = _normalize([row["noveltyRaw"] for row in raw_rows])
    novelty_deficit = [1.0 - v for v in novelty]

    # Transition jolt penalizes only unusually large jumps relative to this cut.
    jolts = [row["transitionJoltRaw"] for row in raw_rows]
    jolt_norm = _normalize(jolts)

    windows = []
    for idx, row in enumerate(raw_rows):
        components = {
            "stasis": round(stasis[idx], 6),
            "sourceOveruse": round(overuse[idx], 6),
            "recentRepetition": round(repetition[idx], 6),
            "noveltyDeficit": round(novelty_deficit[idx], 6),
            "transitionJolt": round(jolt_norm[idx], 6),
        }
        weakness = sum(components[key] * WEIGHTS[key] for key in WEIGHTS)
        dominant = max(components, key=lambda key: components[key])
        windows.append({
            **row,
            "components": components,
            "weaknessScore": round(weakness, 6),
            "dominantWeakness": dominant,
        })

    ranked = sorted(
        windows,
        key=lambda row: (-row["weaknessScore"], row["start"], row["id"]),
    )

    report_body = {
        "schema": REPORT_SCHEMA,
        "sourceVideo": str(video),
        "sourceVideoSha256": _sha_file(video),
        "planId": plan["id"],
        "targetSeconds": round(target, 6),
        "observedVideoSeconds": round(observed_duration, 6),
        "coverageRatio": round(min(1.0, observed_duration / target), 6),
        "windowSeconds": float(window_seconds),
        "sampleFps": int(sample_fps),
        "weights": copy.deepcopy(WEIGHTS),
        "windows": windows,
        "ranking": [row["id"] for row in ranked],
        "weakest": ranked[0]["id"] if ranked else None,
        "meanWeakness": round(mean(row["weaknessScore"] for row in windows), 6) if windows else 0.0,
        "laws": [
            "COVERAGE BEFORE DIAGNOSIS",
            "WEAKNESS SCORE != AESTHETIC TRUTH",
            "OBSERVED MOTION != MEANING",
            "SOURCE OVERUSE != INVALID SOURCE",
            "DOCTOR MAY RECOMMEND; HUMAN MAY OVERRIDE",
        ],
    }
    return {**report_body, "id": "weak-report:" + _sha(report_body)[:24]}


def _next_recipe(current: str, dominant: str) -> str:
    ladder = LOCAL_RECIPE_LADDER.get(current, ("push", "mirror", "reverse"))
    if dominant == "stasis":
        preferences = ("kinetic-push", "push", "fast", "misregister", "mirror-reverse")
    elif dominant in {"sourceOveruse", "recentRepetition"}:
        preferences = ("reverse", "mirror-reverse", "misregister", "pull")
    elif dominant == "transitionJolt":
        preferences = ("soft-loop", "pull", "fit", "slow")
    else:
        preferences = ("mirror", "push", "reverse", "soft-loop")
    for candidate in preferences:
        if candidate in ladder and candidate != current:
            return candidate
    for candidate in ladder:
        if candidate != current:
            return candidate
    return current


def prescribe(
    report: dict,
    plan: dict,
    *,
    fraction: float = 0.10,
    max_windows: int | None = None,
) -> dict:
    if report.get("schema") != REPORT_SCHEMA:
        raise ValueError("Unsupported Weakest Window report")
    if plan.get("schema") != zero_dollar_mill.PLAN_SCHEMA:
        raise ValueError("Unsupported 008e plan")
    if not (0 < fraction <= 1):
        raise ValueError("fraction must be in (0, 1]")

    windows_by_id = {row["id"]: row for row in report["windows"]}
    count = max(1, int(math.ceil(len(report["windows"]) * fraction)))
    if max_windows is not None:
        count = min(count, max(1, int(max_windows)))
    targets = report["ranking"][:count]
    slugs = _slug_spans(plan)
    mutations = []

    for window_id in targets:
        window = windows_by_id[window_id]
        overlapping = [
            slug for slug in slugs
            if _overlap(
                window["start"], window["end"],
                slug["timelineStart"], slug["timelineEnd"],
            ) > 0
        ]
        for slug in overlapping:
            new_recipe = _next_recipe(slug["recipe"], window["dominantWeakness"])
            mutations.append({
                "windowId": window_id,
                "windowWeaknessScore": window["weaknessScore"],
                "dominantWeakness": window["dominantWeakness"],
                "slugId": slug["id"],
                "fromRecipe": slug["recipe"],
                "toRecipe": new_recipe,
                "level": 1,
                "costClass": "local-repeatable-zero",
                "externalGenerations": 0,
                "providerCredits": 0,
                "usdMicros": 0,
            })

    # One mutation per slug; the highest-ranked window wins.
    unique = {}
    for mutation in mutations:
        unique.setdefault(mutation["slugId"], mutation)
    mutations = list(unique.values())

    body = {
        "schema": TREATMENT_SCHEMA,
        "reportId": report["id"],
        "planId": plan["id"],
        "targetFraction": float(fraction),
        "targetWindowCount": count,
        "mutations": mutations,
        "mutationLadder": [
            {"level": 0, "name": "keep", "costClass": "zero"},
            {"level": 1, "name": "deterministic-remix", "costClass": "local-repeatable-zero"},
            {"level": 2, "name": "owned-clip-compost", "costClass": "local-repeatable-zero"},
            {"level": 3, "name": "topology-text-cutout-treatment", "costClass": "local-repeatable-zero"},
            {"level": 4, "name": "repeatably-free-provider", "costClass": "free-repeatable"},
            {"level": 5, "name": "regenerating-included", "costClass": "included-regenerating"},
            {"level": 6, "name": "finite-credit", "costClass": "finite"},
            {"level": 7, "name": "paid-hero-shot", "costClass": "paid"},
        ],
        "laws": [
            "TREAT WEAKEST WINDOWS FIRST",
            "CHEAPEST EFFECTIVE LEVEL FIRST",
            "AUTOMATIC TREATMENT STOPS AT LEVEL 1",
            "PRESCRIPTION != IMPROVEMENT",
            "RESCORE AFTER TREATMENT",
        ],
    }
    return {**body, "id": "weak-treatment:" + _sha(body)[:24]}


def apply_level_one(plan: dict, treatment: dict) -> dict:
    if plan.get("schema") != zero_dollar_mill.PLAN_SCHEMA:
        raise ValueError("Unsupported 008e plan")
    if treatment.get("schema") != TREATMENT_SCHEMA:
        raise ValueError("Unsupported treatment")
    treated = copy.deepcopy(plan)
    mutations = {row["slugId"]: row for row in treatment.get("mutations") or []}
    changed = 0
    for slug in treated["slugs"]:
        mutation = mutations.get(slug["id"])
        if not mutation:
            continue
        if slug["recipe"] != mutation["fromRecipe"]:
            raise ValueError("Treatment no longer binds current slug recipe")
        slug["recipe"] = mutation["toRecipe"]
        slug["doctorTreatmentId"] = treatment["id"]
        changed += 1

    if changed != len(mutations):
        raise ValueError("Treatment references unknown slug(s)")

    body = {k: v for k, v in treated.items() if k != "id"}
    treated["id"] = "zero-dollar-plan:" + _sha(body)[:24]
    treated["doctor"] = {
        "treatmentId": treatment["id"],
        "changedSlugCount": changed,
        "cost": {"externalGenerations": 0, "providerCredits": 0, "usdMicros": 0},
    }
    return treated


def compare(before: dict, after: dict) -> dict:
    if before.get("schema") != REPORT_SCHEMA or after.get("schema") != REPORT_SCHEMA:
        raise ValueError("compare expects two Doctor reports")
    if after["coverageRatio"] + 1e-9 < before["coverageRatio"]:
        raise ValueError("Doctor treatment reduced coverage")
    before_mean = float(before["meanWeakness"])
    after_mean = float(after["meanWeakness"])
    return {
        "beforeReportId": before["id"],
        "afterReportId": after["id"],
        "beforeMeanWeakness": before_mean,
        "afterMeanWeakness": after_mean,
        "meanWeaknessDelta": round(after_mean - before_mean, 6),
        "improved": after_mean < before_mean,
        "coveragePreserved": after["coverageRatio"] >= before["coverageRatio"],
        "law": "TREATMENT IS KEPT AS IMPROVEMENT ONLY AFTER RESCORE SUPPORTS IT",
    }
