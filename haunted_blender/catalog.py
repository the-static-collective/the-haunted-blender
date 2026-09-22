"""Local, source-preserving archive catalog. No cloud calls or source mutations."""
from __future__ import annotations

import hashlib
import os
import sqlite3
from pathlib import Path
from typing import Iterable

SUPPORTED = {
    ".cr2": "raw", ".cr3": "raw", ".dng": "raw",
    ".jpg": "image", ".jpeg": "image", ".png": "image",
    ".tif": "image", ".tiff": "image", ".webp": "image",
    ".mov": "video", ".mp4": "video", ".mkv": "video",
    ".wav": "audio", ".mp3": "audio", ".flac": "audio",
}
DISPLAYABLE = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}


def digest_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def connect(root: Path) -> sqlite3.Connection:
    root = root.expanduser().resolve()
    db = root / ".haunted-blender" / "library.sqlite3"
    if not db.is_file():
        raise FileNotFoundError(f"Initialize the Haunted Blender library first: {root}")
    con = sqlite3.connect(str(db))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init(root: Path) -> Path:
    root = root.expanduser().resolve()
    for name in (".haunted-blender", "projects", "snapshots", "renders"):
        (root / name).mkdir(parents=True, exist_ok=True)
    db = root / ".haunted-blender" / "library.sqlite3"
    con = sqlite3.connect(str(db))
    try:
        con.executescript("""
        PRAGMA foreign_keys = ON;
        CREATE TABLE IF NOT EXISTS assets (
          id TEXT PRIMARY KEY, path TEXT NOT NULL UNIQUE, kind TEXT NOT NULL,
          extension TEXT NOT NULL, size_bytes INTEGER NOT NULL, mtime_ns INTEGER NOT NULL,
          sha256 TEXT NOT NULL, sidecar_path TEXT, rights TEXT NOT NULL DEFAULT 'unassessed',
          indexed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS asset_digest_idx ON assets(sha256);
        CREATE INDEX IF NOT EXISTS asset_kind_idx ON assets(kind);
        CREATE TABLE IF NOT EXISTS derivatives (
          raw_id TEXT PRIMARY KEY REFERENCES assets(id),
          image_id TEXT NOT NULL REFERENCES assets(id),
          associated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)
        con.commit()
    finally:
        con.close()
    return root


def _scan_paths(folder: Path) -> Iterable[Path]:
    for base, dirs, files in os.walk(folder, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not (Path(base) / d).is_symlink() and d not in {".git", ".haunted-blender"})
        for name in sorted(files):
            p = Path(base) / name
            if not p.is_symlink() and p.suffix.lower() in SUPPORTED:
                yield p


def index_file(con: sqlite3.Connection, path: Path) -> tuple[str, bool]:
    """Returns (content-based asset id, whether a path was re-hashed).

    An identical file at two distinct paths has one content identity but two
    separate source records. The path-record identity is deterministic as well.
    """
    supplied = path.expanduser()
    if supplied.is_symlink():
        raise ValueError("Symlinks cannot be indexed as source files")
    path = supplied.resolve(strict=True)
    if not path.is_file():
        raise ValueError("Only regular, non-symlink files may be indexed")
    ext = path.suffix.lower()
    if ext not in SUPPORTED:
        raise ValueError(f"Unsupported extension: {ext}")
    info = path.stat()
    sidecar = path.with_suffix(".xmp")
    if not sidecar.is_file():
        candidate = path.with_suffix(".XMP")
        sidecar = candidate if candidate.is_file() else None
    sidecar_path = str(sidecar) if sidecar else None
    item = con.execute("SELECT id, size_bytes, mtime_ns, sidecar_path FROM assets WHERE path=?", (str(path),)).fetchone()
    if item and item["size_bytes"] == info.st_size and item["mtime_ns"] == info.st_mtime_ns:
        if item["sidecar_path"] != sidecar_path:
            con.execute("UPDATE assets SET sidecar_path=? WHERE id=?", (sidecar_path, item["id"]))
        return item["id"], False
    sha = digest_file(path)
    asset_id = "asset-" + hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:24]
    con.execute("""
      INSERT INTO assets (id, path, kind, extension, size_bytes, mtime_ns, sha256, sidecar_path)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT(path) DO UPDATE SET size_bytes=excluded.size_bytes,
          mtime_ns=excluded.mtime_ns, sha256=excluded.sha256,
          sidecar_path=excluded.sidecar_path, indexed_at=CURRENT_TIMESTAMP
    """, (asset_id, str(path), SUPPORTED[ext], ext, info.st_size, info.st_mtime_ns, sha, sidecar_path))
    return asset_id, True


def scan(root: Path, folder: Path) -> dict:
    folder = folder.expanduser().resolve(strict=True)
    if not folder.is_dir():
        raise NotADirectoryError(folder)
    con = connect(root)
    counts = {"seen": 0, "indexed_or_changed": 0, "unchanged": 0, "errors": 0}
    try:
        for path in _scan_paths(folder):
            counts["seen"] += 1
            try:
                _, changed = index_file(con, path)
                counts["indexed_or_changed" if changed else "unchanged"] += 1
                con.commit()  # resumable even on interruption
            except (OSError, ValueError, sqlite3.Error):
                counts["errors"] += 1
        return counts
    finally:
        con.close()


def derivative(root: Path, raw_id: str, image_path: Path) -> str:
    con = connect(root)
    try:
        raw = con.execute("SELECT kind FROM assets WHERE id=?", (raw_id,)).fetchone()
        if raw is None or raw["kind"] != "raw":
            raise ValueError("Source asset must be a cataloged RAW image")
        if image_path.suffix.lower() not in DISPLAYABLE:
            raise ValueError("Derivative must be JPEG, PNG, TIFF or WebP")
        image_id, _ = index_file(con, image_path)
        con.execute("INSERT INTO derivatives(raw_id,image_id) VALUES (?,?) "
                    "ON CONFLICT(raw_id) DO UPDATE SET image_id=excluded.image_id, associated_at=CURRENT_TIMESTAMP",
                    (raw_id, image_id))
        con.commit()
        return image_id
    finally:
        con.close()


def source_for_render(con: sqlite3.Connection, asset_id: str) -> sqlite3.Row:
    row = con.execute("SELECT * FROM assets WHERE id=?", (asset_id,)).fetchone()
    if row is None:
        raise ValueError(f"Unknown asset: {asset_id}")
    if row["kind"] == "raw":
        derived = con.execute("SELECT a.* FROM derivatives d JOIN assets a ON a.id=d.image_id WHERE d.raw_id=?", (asset_id,)).fetchone()
        if derived is None:
            raise ValueError(f"RAW asset {asset_id} has no renderable derivative; associate an edited export")
        return derived
    if row["kind"] != "image" or row["extension"] not in DISPLAYABLE:
        raise ValueError(f"Asset {asset_id} is not a renderable still image")
    return row


def stats(root: Path) -> dict:
    con = connect(root)
    try:
        rows = con.execute("SELECT kind, COUNT(*) as count, SUM(size_bytes) as bytes FROM assets GROUP BY kind ORDER BY kind").fetchall()
        return {r["kind"]: {"files": r["count"], "bytes": r["bytes"]} for r in rows}
    finally:
        con.close()


def find(root: Path, query: str = "", kind: str | None = None, limit: int = 50) -> list[dict]:
    """Literal filename search; no inferred identities, rights or image content."""
    if kind is not None and kind not in set(SUPPORTED.values()):
        raise ValueError("Unknown asset kind")
    if not 1 <= limit <= 500:
        raise ValueError("Limit must be 1–500")
    con = connect(root)
    try:
        rows = con.execute("""SELECT a.id,a.path,a.kind,a.rights,a.sidecar_path,
          d.image_id AS derivative_id FROM assets a
          LEFT JOIN derivatives d ON d.raw_id=a.id
          WHERE (? IS NULL OR a.kind=?) ORDER BY a.path""", (kind, kind))
        result = []
        for row in rows:
            if query.casefold() not in Path(row["path"]).name.casefold():
                continue
            result.append({**dict(row), "renderable":
                (row["kind"] == "image" and Path(row["path"]).suffix.lower() in DISPLAYABLE)
                or bool(row["derivative_id"])})
            if len(result) == limit:
                break
        return result
    finally:
        con.close()


def inspect(root: Path, asset_id: str) -> dict:
    con = connect(root)
    try:
        row = con.execute("""SELECT a.*,d.image_id AS derivative_id,
          i.path AS derivative_path FROM assets a
          LEFT JOIN derivatives d ON d.raw_id=a.id
          LEFT JOIN assets i ON i.id=d.image_id WHERE a.id=?""", (asset_id,)).fetchone()
        if row is None:
            raise ValueError(f"Unknown asset: {asset_id}")
        return dict(row)
    finally:
        con.close()


def verify(root: Path, limit: int = 50) -> dict:
    """Check all cataloged source bytes without changing source or catalog."""
    if not 1 <= limit <= 500:
        raise ValueError("Limit must be 1–500")
    con = connect(root)
    result = {"checked": 0, "ok": 0, "missing": 0, "changed": 0,
              "unreadable": 0, "missing_sidecars": 0, "examples": []}
    try:
        for row in con.execute("SELECT id,path,sha256,sidecar_path FROM assets ORDER BY path"):
            result["checked"] += 1
            path = Path(row["path"])
            try:
                if path.is_symlink() or not path.is_file():
                    status = "missing"
                else:
                    status = "ok" if digest_file(path) == row["sha256"] else "changed"
            except OSError:
                status = "unreadable"
            result[status] += 1
            if status != "ok" and len(result["examples"]) < limit:
                result["examples"].append({"id": row["id"], "path": row["path"], "status": status})
            if row["sidecar_path"] and not Path(row["sidecar_path"]).is_file():
                result["missing_sidecars"] += 1
        return result
    finally:
        con.close()
