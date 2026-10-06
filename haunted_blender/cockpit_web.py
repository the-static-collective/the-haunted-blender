from __future__ import annotations

import json
import mimetypes
import re
import shutil
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from . import cockpit, cockpit_engine, cockpit_media, provider_driver

WEB_DIR = Path(__file__).resolve().parent / "web"


def _json_bytes(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _safe_filename(value: str) -> str:
    name = Path(value).name
    name = re.sub(r"[^A-Za-z0-9._ -]+", "_", name).strip()
    if not name:
        raise ValueError("Upload filename is empty")
    return name[:180]


def _section_state(root: Path, section_id: str) -> dict:
    view = cockpit.cockpit_view(root)
    section = next((item for item in view["sections"] if item["id"] == section_id), None)
    if section is None:
        raise ValueError("Unknown section")
    return section


def make_handler(project_root: str | Path):
    root = Path(project_root).expanduser().resolve()

    class CockpitHandler(BaseHTTPRequestHandler):
        server_version = "HauntedBlenderCockpit/008a"

        def log_message(self, format, *args):
            return

        def _send_json(self, status: int, value) -> None:
            body = _json_bytes(value)
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _read_json(self) -> dict:
            length = int(self.headers.get("Content-Length") or 0)
            if length > 2_000_000:
                raise ValueError("JSON request is too large")
            raw = self.rfile.read(length) if length else b"{}"
            value = json.loads(raw.decode("utf-8"))
            if not isinstance(value, dict):
                raise ValueError("Expected a JSON object")
            return value

        def _send_file(self, path: Path, *, allow_ranges: bool = False) -> None:
            size = path.stat().st_size
            mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            start = 0
            end = size - 1
            status = 200
            range_header = self.headers.get("Range") if allow_ranges else None
            if range_header:
                match = re.fullmatch(r"bytes=(\d*)-(\d*)", range_header.strip())
                if match:
                    left, right = match.groups()
                    if left:
                        start = int(left)
                    if right:
                        end = min(int(right), size - 1)
                    if not left and right:
                        count = int(right)
                        start = max(0, size - count)
                        end = size - 1
                    if start > end or start >= size:
                        self.send_response(416)
                        self.send_header("Content-Range", f"bytes */{size}")
                        self.end_headers()
                        return
                    status = 206
            length = end - start + 1
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(length))
            self.send_header("Accept-Ranges", "bytes")
            if status == 206:
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            with path.open("rb") as handle:
                handle.seek(start)
                remaining = length
                while remaining > 0:
                    chunk = handle.read(min(1024 * 1024, remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)

        def do_GET(self):
            try:
                parsed = urlparse(self.path)
                path = parsed.path
                if path == "/api/view":
                    self._send_json(200, cockpit.cockpit_view(root))
                    return
                if path == "/api/resume":
                    self._send_json(200, cockpit.resume_summary(root))
                    return
                if path.startswith("/api/media-view/"):
                    section_id = unquote(path.removeprefix("/api/media-view/"))
                    self._send_json(200, cockpit_media.media_view(root, section_id))
                    return
                if path.startswith("/api/engine-view/"):
                    section_id = unquote(path.removeprefix("/api/engine-view/"))
                    self._send_json(200, cockpit_engine.engine_view(root, section_id))
                    return
                if path.startswith("/api/provider-view/"):
                    section_id = unquote(path.removeprefix("/api/provider-view/"))
                    self._send_json(200, provider_driver.provider_view(root, section_id))
                    return
                if path.startswith("/media/"):
                    relative = unquote(path.removeprefix("/media/"))
                    media = cockpit_media.resolve_media(root, relative)
                    self._send_file(media, allow_ranges=True)
                    return

                static_name = "cockpit.html" if path in {"/", "/index.html"} else path.lstrip("/")
                if static_name not in {"cockpit.html", "cockpit.css", "cockpit.js"}:
                    self._send_json(404, {"error": "Not found"})
                    return
                static_path = WEB_DIR / static_name
                self._send_file(static_path)
            except Exception as exc:
                self._send_json(400, {"error": str(exc)})

        def do_POST(self):
            try:
                parsed = urlparse(self.path)
                path = parsed.path

                if path == "/api/auto/play":
                    result = cockpit_engine.play(root)
                    self._send_json(200, result)
                    return
                if path.startswith("/api/provider/section/"):
                    rest = path.removeprefix("/api/provider/section/").split("/")
                    if len(rest) != 2:
                        raise ValueError("Expected /api/provider/section/<id>/<action>")
                    section_id, action = map(unquote, rest)
                    body = self._read_json()
                    if action == "drive":
                        result = provider_driver.drive(
                            root, section_id, max_steps=int(body.get("maxSteps") or 12)
                        )
                    elif action == "approve":
                        result = provider_driver.approve_spend(
                            root,
                            section_id,
                            expected_usd_micros=body.get("expectedUsdMicros"),
                            approved_at=str(body.get("approvedAt") or ""),
                        )
                    elif action == "reconcile":
                        result = provider_driver.reconcile_submission(
                            root,
                            section_id,
                            vendor_request_id=str(body.get("vendorRequestId") or ""),
                            submitted_parameter_sha256=str(body.get("submittedParameterSha256") or ""),
                            observed_at=str(body.get("observedAt") or ""),
                        )
                    elif action == "decline":
                        result = provider_driver.decline_current_candidate(
                            root, section_id, reason=str(body.get("reason") or "")
                        )
                    elif action == "accept":
                        result = provider_driver.accept_candidate(
                            root, section_id, str(body["candidatePath"])
                        )
                    else:
                        raise ValueError("Unknown provider-driver action")
                    self._send_json(200, result)
                    return


                if path.startswith("/api/auto/section/"):
                    rest = path.removeprefix("/api/auto/section/").split("/")
                    if len(rest) != 2:
                        raise ValueError("Expected /api/auto/section/<id>/<verb>")
                    section_id, verb = map(unquote, rest)
                    body = self._read_json()
                    if verb == "grow":
                        result = cockpit_engine.grow(root, section_id)
                    elif verb == "keep":
                        result = cockpit_engine.keep(root, section_id, slot=int(body["slot"]))
                    elif verb == "awaken":
                        result = cockpit_engine.awaken(root, section_id)
                    else:
                        raise ValueError("Unknown automatic Cockpit verb")
                    self._send_json(200, result)
                    return

                if path == "/api/local-only":
                    body = self._read_json()
                    result = cockpit.set_local_only(root, bool(body.get("enabled")))
                    self._send_json(200, result)
                    return

                if path == "/api/bind-media":
                    body = self._read_json()
                    result = cockpit_media.bind_media(
                        root,
                        str(body["sectionId"]),
                        kind=str(body["kind"]),
                        media_path=str(body["path"]),
                        provider_id=body.get("providerId"),
                        offer_id=body.get("offerId"),
                        cost_class=str(body.get("costClass") or "deterministic"),
                        label=body.get("label"),
                    )
                    self._send_json(200, result)
                    return

                if path == "/api/upload":
                    section_id = self.headers.get("X-Section-Id")
                    kind = self.headers.get("X-Media-Kind")
                    filename = _safe_filename(self.headers.get("X-File-Name") or "upload.mp4")
                    cost_class = self.headers.get("X-Cost-Class") or "deterministic"
                    if not section_id or kind not in cockpit_media.MEDIA_KINDS:
                        raise ValueError("Upload requires X-Section-Id and a valid X-Media-Kind")
                    _section_state(root, section_id)
                    length = int(self.headers.get("Content-Length") or 0)
                    if length <= 0 or length > 1_500_000_000:
                        raise ValueError("Upload size is invalid")
                    folder = root / "cockpit-media" / _safe_filename(section_id)
                    folder.mkdir(parents=True, exist_ok=True)
                    destination = folder / filename
                    if destination.exists():
                        raise FileExistsError("Cockpit upload never overwrites an existing media file")
                    remaining = length
                    with destination.open("xb") as out:
                        while remaining > 0:
                            chunk = self.rfile.read(min(1024 * 1024, remaining))
                            if not chunk:
                                break
                            out.write(chunk)
                            remaining -= len(chunk)
                    if remaining != 0:
                        destination.unlink(missing_ok=True)
                        raise ValueError("Upload ended before declared Content-Length")
                    result = cockpit_media.bind_media(
                        root,
                        section_id,
                        kind=kind,
                        media_path=destination,
                        provider_id=self.headers.get("X-Provider-Id"),
                        offer_id=self.headers.get("X-Offer-Id"),
                        cost_class=cost_class,
                        label=self.headers.get("X-Label") or filename,
                    )
                    self._send_json(201, result)
                    return

                if not path.startswith("/api/section/"):
                    self._send_json(404, {"error": "Not found"})
                    return

                rest = path.removeprefix("/api/section/").split("/")
                if len(rest) != 2:
                    raise ValueError("Expected /api/section/<id>/<action>")
                section_id, action = map(unquote, rest)
                body = self._read_json()

                if action == "grow":
                    result = cockpit.action_grow(root, section_id, ecology_id=str(body["ecologyId"]))
                elif action == "keep":
                    result = cockpit.action_keep(
                        root,
                        section_id,
                        proposal_id=str(body["proposalId"]),
                        scene_id=body.get("sceneId"),
                    )
                elif action == "moving":
                    result = cockpit.action_scene_rendered(root, section_id, scene_id=str(body["sceneId"]))
                elif action == "awaken":
                    result = cockpit.action_awaken(root, section_id, window_id=str(body["windowId"]))
                elif action == "witness":
                    result = cockpit.action_witness(root, section_id, video_address=str(body["videoAddress"]))
                elif action == "alive":
                    result = cockpit.action_alive(root, section_id)
                elif action == "haunt":
                    result = cockpit.action_haunt(root, section_id, haunt_id=str(body["hauntId"]))
                else:
                    raise ValueError("Unknown Cockpit section action")
                self._send_json(200, result)
            except Exception as exc:
                self._send_json(400, {"error": str(exc)})

    return CockpitHandler


def serve(project_root: str | Path, *, host: str = "127.0.0.1", port: int = 8765) -> None:
    root = Path(project_root).expanduser().resolve()
    cockpit.load_project(root)
    server = ThreadingHTTPServer((host, int(port)), make_handler(root))
    print(f"Haunted Blender Cockpit: http://{host}:{port}")
    print(f"Project: {root}")
    server.serve_forever()


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="haunted-blender-cockpit-web")
    parser.add_argument("root")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    serve(args.root, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
