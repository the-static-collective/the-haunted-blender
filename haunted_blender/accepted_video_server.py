"""Loopback-only read-only server for accepted Haunted Blender video takes."""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from .video_resolver import (
    VideoResolverError,
    resolve_accepted_video,
    resolve_accepted_video_for_serve,
)

DIGEST_PATH = re.compile(r"^/v0/(resolve|media)/([a-f0-9]{64})$")


def _parse_range(value: str | None, length: int):
    if value is None:
        return None
    match = re.fullmatch(r"bytes=(\d*)-(\d*)", value)
    if match is None:
        raise VideoResolverError("INVALID_RANGE", "Only one byte range is supported.", 416)

    left, right = match.groups()
    if left == "":
        suffix = int(right) if right else 0
        if suffix <= 0:
            raise VideoResolverError("INVALID_RANGE", "Invalid byte range.", 416)
        start = max(0, length - suffix)
        end = length - 1
    else:
        start = int(left)
        end = length - 1 if right == "" else int(right)

    if start < 0 or end < start or start >= length:
        raise VideoResolverError("INVALID_RANGE", "Unsatisfiable byte range.", 416)
    return start, min(end, length - 1)


def make_handler(root: Path, allowed_origin: str):
    class Handler(BaseHTTPRequestHandler):
        server_version = "HauntedBlenderAcceptedVideoResolver/001"

        def _origin(self):
            origin = self.headers.get("Origin")
            if origin is None:
                return None
            if origin != allowed_origin:
                raise VideoResolverError("ORIGIN_REFUSED", "Origin is not the configured local Room.", 403)
            return origin

        def _guard(self):
            expected = {
                f"127.0.0.1:{self.server.server_port}",
                f"localhost:{self.server.server_port}",
            }
            if self.headers.get("Host", "") not in expected:
                raise VideoResolverError("HOST_REFUSED", "Loopback Host header required.", 403)
            return self._origin()

        def _json(self, status: int, value: dict, origin=None):
            body = json.dumps(value, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            if origin:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def do_OPTIONS(self):
            try:
                origin = self._guard()
                self.send_response(204)
                self.send_header("Access-Control-Allow-Origin", origin or allowed_origin)
                self.send_header("Access-Control-Allow-Methods", "GET,HEAD,OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Range")
                self.send_header("Access-Control-Max-Age", "300")
                self.send_header("Vary", "Origin")
                self.end_headers()
            except VideoResolverError as exc:
                self._json(exc.status, {"code": exc.code, "detail": str(exc)})

        def _serve(self):
            try:
                origin = self._guard()
                path = urlsplit(self.path).path

                if path == "/v0/status":
                    self._json(
                        200,
                        {
                            "schema": "haunted-blender-accepted-video-resolver-status/v0",
                            "status": "ready",
                            "authority": "none",
                            "transport": "loopback-read-only",
                            "selection": "filmmaker-accepted-private-take-only",
                        },
                        origin,
                    )
                    return

                match = DIGEST_PATH.fullmatch(path)
                if match is None:
                    self._json(404, {"code": "NOT_FOUND", "detail": "No such resolver endpoint."}, origin)
                    return

                action, digest = match.groups()
                address = "sha256:" + digest

                if action == "resolve":
                    self._json(200, resolve_accepted_video(root, address), origin)
                    return

                descriptor, video = resolve_accepted_video_for_serve(root, address)
                length = descriptor["byteLength"]
                byte_range = _parse_range(self.headers.get("Range"), length)

                self.send_response(206 if byte_range else 200)
                self.send_header("Content-Type", "video/mp4")
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-SHA256", digest)
                if origin:
                    self.send_header("Access-Control-Allow-Origin", origin)
                    self.send_header("Vary", "Origin")

                if byte_range:
                    start, end = byte_range
                    size = end - start + 1
                    self.send_header("Content-Length", str(size))
                    self.send_header("Content-Range", f"bytes {start}-{end}/{length}")
                else:
                    start, end = 0, length - 1
                    self.send_header("Content-Length", str(length))
                self.end_headers()

                if self.command == "HEAD":
                    return

                with video.open("rb") as handle:
                    handle.seek(start)
                    remaining = end - start + 1
                    while remaining:
                        block = handle.read(min(1024 * 1024, remaining))
                        if not block:
                            break
                        self.wfile.write(block)
                        remaining -= len(block)

            except VideoResolverError as exc:
                self._json(exc.status, {"code": exc.code, "detail": str(exc)})
            except (BrokenPipeError, ConnectionResetError):
                return
            except Exception:
                self._json(500, {"code": "RESOLVER_FAILURE", "detail": "Resolver failed closed."})

        def do_GET(self):
            self._serve()

        def do_HEAD(self):
            self._serve()

        def do_POST(self):
            self._json(405, {"code": "METHOD_REFUSED", "detail": "Resolver is read-only."})

        do_PUT = do_POST
        do_PATCH = do_POST
        do_DELETE = do_POST

        def log_message(self, fmt, *args):
            return

    return Handler


def main():
    parser = argparse.ArgumentParser(description="Haunted Blender accepted-video resolver")
    parser.add_argument("root", help="Private Haunted Blender library root")
    parser.add_argument("--port", type=int, default=13704)
    parser.add_argument("--room-origin", default="http://127.0.0.1:13702")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve(strict=True)
    if not 1 <= args.port <= 65535:
        parser.error("port must be 1-65535")
    if args.room_origin not in {
        "http://127.0.0.1:13702",
        "http://localhost:13702",
    }:
        parser.error("room-origin must be the local ROroomOM origin")

    with ThreadingHTTPServer(
        ("127.0.0.1", args.port),
        make_handler(root, args.room_origin),
    ) as server:
        print(
            f"Haunted Blender accepted-video resolver: http://127.0.0.1:{args.port}",
            flush=True,
        )
        server.serve_forever()


if __name__ == "__main__":
    main()
