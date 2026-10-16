"""Free TripoSR image->GLB loopback bridge. No cloud account, public upload or paid API.

This service runs ONLY on the computer hosting TripoSR. The GitHub Pages site
may explicitly call it with the user's permission; it never runs on Pages.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

MAX_IMAGE = 20 * 1024 * 1024
MAX_GLB = 30 * 1024 * 1024
ALLOWED_ORIGINS = frozenset({
    "https://hoanggiaktsda-beep.github.io",
    "http://127.0.0.1:8765",
    "http://127.0.0.1:8766",
    "http://localhost:8765",
    "http://localhost:8766",
})
IMAGE_TYPES = frozenset({"image/png", "image/jpeg", "image/webp"})


def valid_image(data: bytes, mime: str) -> bool:
    if mime == "image/png":
        return data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 33
    if mime == "image/jpeg":
        return data.startswith(b"\xff\xd8\xff") and data.endswith(b"\xff\xd9")
    if mime == "image/webp":
        return len(data) >= 16 and data[:4] == b"RIFF" and data[8:12] == b"WEBP"
    return False


def validate_glb(data: bytes) -> None:
    if len(data) < 20 or len(data) > MAX_GLB:
        raise ValueError("GLB missing or too large")
    if data[:4] != b"glTF" or int.from_bytes(data[4:8], "little") != 2:
        raise ValueError("Invalid GLB v2 header")
    if int.from_bytes(data[8:12], "little") != len(data):
        raise ValueError("GLB length mismatch")
    json_len = int.from_bytes(data[12:16], "little")
    if data[16:20] != b"JSON" or json_len < 2 or 20 + json_len > len(data):
        raise ValueError("Invalid GLB JSON chunk")
    obj = json.loads(data[20:20 + json_len].decode("utf-8").strip())
    if not obj.get("meshes") or not obj.get("accessors"):
        raise ValueError("GLB contains no editable mesh")
    if any("uri" in item for group in ("images", "buffers") for item in obj.get(group, [])):
        raise ValueError("External GLB resources are not permitted")


class TripoSRService:
    def __init__(self, repo_dir: Path, python_executable: str = sys.executable,
                 timeout: int = 900, resolution: int = 192):
        self.repo_dir = Path(repo_dir).resolve()
        candidate = Path(python_executable).expanduser()
        # Subprocess runs with cwd=TripoSR; relative venv paths must be resolved first.
        self.python_executable = str(candidate.resolve()) if (candidate.is_absolute() or '/' in python_executable or '\\' in python_executable) else python_executable
        self.timeout = timeout
        self.resolution = resolution
        self.lock = threading.Lock()

    @property
    def installed(self) -> bool:
        return (self.repo_dir / "run.py").is_file()

    def generate(self, image: bytes, mime: str) -> bytes:
        if not self.installed:
            raise FileNotFoundError("TripoSR is not installed")
        if not valid_image(image, mime):
            raise ValueError("Invalid image bytes")
        suffix = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}[mime]
        with tempfile.TemporaryDirectory(prefix="hg-triposr-") as tmp:
            folder = Path(tmp)
            source = folder / ("source" + suffix)
            source.write_bytes(image)
            output = folder / "result"
            command = [
                self.python_executable, str(self.repo_dir / "run.py"), str(source),
                "--output-dir", str(output), "--model-save-format", "glb",
                "--mc-resolution", str(self.resolution), "--chunk-size", "4096",
            ]
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            completed = subprocess.run(
                command, cwd=self.repo_dir, env=env, capture_output=True,
                timeout=self.timeout, check=False,
            )
            if completed.returncode:
                # Diagnostic stays ONLY in the operator's terminal, never in HTTP/Pages.
                tail = completed.stderr.decode("utf-8", errors="replace")[-1600:]
                print(f"TripoSR exited {completed.returncode}: {tail}", file=sys.stderr)
                raise RuntimeError("TripoSR failed. Check the local terminal for GPU, dependencies and model weights.")
            result = output / "0" / "mesh.glb"
            if not result.is_file() or result.stat().st_size > MAX_GLB:
                raise ValueError("TripoSR did not produce a usable GLB")
            data = result.read_bytes()
            validate_glb(data)
            return data


def make_handler(service: TripoSRService, port: int):
    class Handler(BaseHTTPRequestHandler):
        server_version = "HGTripoSR/1.0"
        sys_version = ""

        def log_message(self, fmt, *args):
            # Never log source image bytes, customer filenames or query strings.
            if self.path.split("?")[0] == "/health":
                return
            print("TripoSR request completed", file=sys.stderr)

        def origin(self):
            return self.headers.get("Origin", "")

        def allowed_host(self):
            return self.headers.get("Host", "") in {
                f"127.0.0.1:{port}", f"localhost:{port}",
            }

        def headers_common(self, mime: str, length: int):
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(length))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cross-Origin-Resource-Policy", "cross-origin")
            self.send_header("Access-Control-Allow-Private-Network", "true")
            if self.origin() in ALLOWED_ORIGINS:
                self.send_header("Access-Control-Allow-Origin", self.origin())
                self.send_header("Vary", "Origin")

        def respond(self, status: int, payload: dict):
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.headers_common("application/json; charset=utf-8", len(body))
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self):
            if not self.allowed_host() or self.origin() not in ALLOWED_ORIGINS:
                self.respond(403, {"error": "Origin not permitted"})
                return
            if urlsplit(self.path).path not in ("/health", "/v1/generate"):
                self.respond(404, {"error": "Unknown endpoint"})
                return
            self.send_response(204)
            self.headers_common("text/plain", 0)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Max-Age", "300")
            self.end_headers()

        def do_GET(self):
            if not self.allowed_host():
                self.respond(403, {"error": "Invalid host"})
                return
            if urlsplit(self.path).path != "/health":
                self.respond(404, {"error": "Unknown endpoint"})
                return
            self.respond(200, {
                "engine": "TripoSR", "local_only": True, "free_software": True,
                "engine_found": service.installed,
                "inference_verified": False,
                "busy": service.lock.locked(),
                "notice": "Model/GPU readiness is only established by a successful inference.",
            })

        def do_POST(self):
            if not self.allowed_host() or self.origin() not in ALLOWED_ORIGINS:
                self.respond(403, {"error": "Only the approved local website may submit images"})
                return
            if urlsplit(self.path).path != "/v1/generate":
                self.respond(404, {"error": "Unknown endpoint"})
                return
            mime = self.headers.get("Content-Type", "").split(";", 1)[0].lower().strip()
            if mime not in IMAGE_TYPES:
                self.respond(415, {"error": "Use PNG, JPEG or WebP"})
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                size = 0
            if size < 33 or size > MAX_IMAGE:
                self.respond(413, {"error": "Image must be 33 bytes to 20 MB"})
                return
            if not service.installed:
                self.respond(503, {"error": "TripoSR not installed on this computer"})
                return
            if not service.lock.acquire(blocking=False):
                self.respond(429, {"error": "TripoSR is busy; wait for the previous request"})
                return
            try:
                image = self.rfile.read(size)
                if len(image) != size or not valid_image(image, mime):
                    self.respond(422, {"error": "Image format invalid"})
                    return
                try:
                    glb = service.generate(image, mime)
                except subprocess.TimeoutExpired:
                    self.respond(504, {"error": "TripoSR timed out; check local GPU and memory"})
                    return
                except Exception:
                    self.respond(500, {"error": "TripoSR failed locally; check dependencies and GPU"})
                    return
                self.send_response(200)
                self.headers_common("model/gltf-binary", len(glb))
                self.send_header("Content-Disposition", 'attachment; filename="triposr-draft.glb"')
                self.end_headers()
                self.wfile.write(glb)
            finally:
                service.lock.release()
    return Handler


def create_server(service: TripoSRService, port: int = 8787):
    return ThreadingHTTPServer(("127.0.0.1", port), make_handler(service, port))


def main():
    parser = argparse.ArgumentParser(description="Free TripoSR bridge; loopback only")
    parser.add_argument("--triposr-dir", type=Path, default=Path(".private/TripoSR"))
    parser.add_argument("--python", default=sys.executable, help="Python with TripoSR dependencies")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--resolution", type=int, choices=(128, 192, 256), default=192)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535 or not 30 <= args.timeout <= 3600:
        parser.error("Port must be 1024..65535 and timeout 30..3600 seconds")
    service = TripoSRService(args.triposr_dir, args.python, args.timeout, args.resolution)
    print(f"HOANGGIA TripoSR local bridge: http://127.0.0.1:{args.port}/health", flush=True)
    print("TripoSR source found:", service.installed, "| no inference is run until user clicks Generate", flush=True)
    with create_server(service, args.port) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
