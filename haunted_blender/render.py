"""Deterministic frozen-snapshot FFmpeg storyboard preview adapter (silent stills)."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from .catalog import connect, digest_file, source_for_render
from .project import load_snapshot, stable_bytes

WIDTH = 1280
HEIGHT = 720
FPS = 24


def plan(root: Path, snapshot: Path) -> dict:
    film, snapshot_sha = load_snapshot(root, snapshot)
    con = connect(root)
    try:
        shots = []
        for scene in film["scenes"]:
            for shot in scene["shots"]:
                source = source_for_render(con, shot["source_asset_id"])
                path = Path(source["path"])
                if not path.is_file():
                    raise FileNotFoundError(f"Missing source: {path}")
                if digest_file(path) != source["sha256"]:
                    raise ValueError(f"Source changed since cataloging: {path}; re-scan and re-freeze")
                shots.append({
                    "scene_id": scene["id"], "shot_id": shot["id"],
                    "requested_asset_id": shot["source_asset_id"],
                    "frame_asset_id": source["id"],
                    "path": str(path), "sha256": source["sha256"],
                    "duration_ms": shot["duration_ms"],
                    "framing": shot["framing"], "render_mode": shot["render_mode"],
                })
        if not shots:
            raise ValueError("A render needs at least one shot")
        return {
            "schema": "haunted-blender/render-plan/v1",
            "adapter": "ffmpeg-static-storyboard/v1",
            "snapshot_sha256": snapshot_sha,
            "film_id": film["id"], "width": WIDTH, "height": HEIGHT, "fps": FPS,
            "audio": "none", "captions": "none", "shots": shots,
        }
    finally:
        con.close()


def render(root: Path, snapshot: Path, out: Path) -> dict:
    spec = plan(root, snapshot)
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("FFmpeg is not installed; 'plan' still works without it")
    out = out.expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise FileExistsError(f"Will not overwrite an existing render: {out}")
    with tempfile.TemporaryDirectory(prefix="blender-render-") as folder:
        tmp = Path(folder)
        clips = []
        for index, shot in enumerate(spec["shots"]):
            clip = tmp / f"shot-{index:06d}.mp4"
            duration = shot["duration_ms"] / 1000.0
            cmd = [
                ffmpeg, "-nostdin", "-v", "error", "-y",
                "-loop", "1", "-framerate", str(FPS), "-i", shot["path"],
                "-t", f"{duration:.3f}", "-vf",
                f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease:flags=lanczos,"
                f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={FPS}",
                "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(clip),
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            clips.append(clip)
        playlist = tmp / "playlist.txt"
        playlist.write_text("".join(f"file '{p.name}'\n" for p in clips), encoding="utf-8")
        rendered = tmp / "joined.mp4"
        cmd = [ffmpeg, "-nostdin", "-v", "error", "-y", "-f", "concat", "-safe", "1",
               "-i", str(playlist), "-c", "copy", "-movflags", "+faststart", str(rendered)]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for shot in spec["shots"]:
            if digest_file(Path(shot["path"])) != shot["sha256"]:
                raise ValueError("A source changed during rendering; no receipt will be issued")
        shutil.copyfile(rendered, out)
    receipt = {
        "schema": "haunted-blender/render-receipt/v1", "status": "scoped_complete",
        "claim": "silent 720p storyboard rendered from frozen shots; NOT a completed drama or proof of scene continuity",
        "snapshot_sha256": spec["snapshot_sha256"],
        "adapter": spec["adapter"], "output_path": str(out), "output_sha256": digest_file(out),
        "shot_count": len(spec["shots"]), "sound": "not rendered", "video": "ffmpeg static stills",
    }
    receipt_path = out.with_suffix(out.suffix + ".receipt.json")
    if receipt_path.exists():
        out.unlink(missing_ok=True)
        raise FileExistsError(f"Will not overwrite an existing render receipt: {receipt_path}")
    tmp_receipt = receipt_path.with_suffix(receipt_path.suffix + ".tmp")
    try:
        tmp_receipt.write_bytes(stable_bytes(receipt) + b"\n")
        os.replace(tmp_receipt, receipt_path)
    except Exception:
        out.unlink(missing_ok=True)
        raise
    return receipt
