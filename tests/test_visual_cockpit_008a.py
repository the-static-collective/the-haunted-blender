import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen

from haunted_blender import cockpit, cockpit_media
from haunted_blender.cockpit_web import WEB_DIR, make_handler


class VisualCockpit008aTests(unittest.TestCase):
    def make_project(self, root: Path):
        cockpit.create_project(root, project_id="visual-1", title="Visual Test", local_only=True)
        cockpit.add_section(root, section_id="verse", kind="verse", start=0, end=8)

    def test_media_registry_stays_inside_project_root(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as outside:
            root = Path(td)
            self.make_project(root)
            media = root / "preview.mp4"
            media.write_bytes(b"fake-local-video")
            cockpit_media.bind_media(root, "verse", kind="sixup", media_path=media)
            view = cockpit_media.media_view(root, "verse")
            self.assertEqual(view["sixup"]["path"], "preview.mp4")
            self.assertEqual(cockpit_media.resolve_media(root, "preview.mp4"), media.resolve())

            external = Path(outside) / "outside.mp4"
            external.write_bytes(b"outside")
            with self.assertRaises(ValueError):
                cockpit_media.bind_media(root, "verse", kind="scene", media_path=external)

    def test_static_visual_contract_exists(self):
        html = (WEB_DIR / "cockpit.html").read_text(encoding="utf-8")
        css = (WEB_DIR / "cockpit.css").read_text(encoding="utf-8")
        js = (WEB_DIR / "cockpit.js").read_text(encoding="utf-8")
        for verb in ["GROW", "KEEP", "AWAKEN", "PLAY"]:
            self.assertIn(verb, html)
        self.assertIn("LOCAL ONLY", html)
        self.assertIn("candidate-board", html)
        self.assertIn("temperature-chip", css)
        self.assertIn("/api/view", js)
        self.assertIn("/api/upload", js)

    def test_real_http_surface_reads_and_changes_project_state(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_project(root)
            server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(root))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base = f"http://127.0.0.1:{server.server_port}"
                with urlopen(base + "/") as response:
                    html = response.read().decode("utf-8")
                self.assertIn("HAUNTED BLENDER / VISUAL COCKPIT", html)

                with urlopen(base + "/api/view") as response:
                    view = json.loads(response.read())
                self.assertTrue(view["localOnly"])
                self.assertEqual(view["sections"][0]["temperature"], "sleeping")

                request = Request(
                    base + "/api/local-only",
                    data=json.dumps({"enabled": False}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(request) as response:
                    self.assertEqual(response.status, 200)

                with urlopen(base + "/api/view") as response:
                    changed = json.loads(response.read())
                self.assertFalse(changed["localOnly"])
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
