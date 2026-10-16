"""Tests the actual local HTTP bridge, but never pretends a GPU ran TripoSR."""
import importlib.util
import json
import socket
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("hg_triposr_bridge", ROOT / "scripts/triposr_local_bridge.py")
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)
PHOTO = (ROOT / "tests/fixtures/dimensioned_cabinet.png").read_bytes()
GLB = (ROOT / "viewer/assets/sample.glb").read_bytes()
ORIGIN = "https://hoanggiaktsda-beep.github.io"


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="hg-triposr-bridge-test-")
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        repo = root / "fake-triposr"
        repo.mkdir()
        # A controlled test runner copies a known fixture; it is NOT an AI result.
        fake = (
            "from pathlib import Path\n"
            "import shutil,sys\n"
            "args=sys.argv\n"
            "out=Path(args[args.index('--output-dir')+1])/'0'\n"
            "out.mkdir(parents=True,exist_ok=True)\n"
            f"shutil.copyfile({str(ROOT/'viewer/assets/sample.glb')!r},out/'mesh.glb')\n"
        )
        (repo / "run.py").write_text(fake)
        self.service = bridge.TripoSRService(repo, python_executable=sys.executable, timeout=10)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        self.server = bridge.create_server(self.service, port)
        self.addCleanup(self.server.server_close)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.server.shutdown)
        self.url = f"http://127.0.0.1:{port}"

    def request(self, path, data=None, origin=ORIGIN, mime="image/png", method=None, headers=None):
        request = Request(
            self.url + path, data=data,
            headers={"Origin": origin, "Content-Type": mime, **(headers or {})},
            method=method or ("POST" if data is not None else "GET"),
        )
        try:
            with urlopen(request, timeout=20) as response:
                return response.status, response.read(), dict(response.headers)
        except HTTPError as error:
            return error.code, error.read(), dict(error.headers)

    def test_health_does_not_claim_gpu_inference_verified(self):
        status, body, headers = self.request("/health")
        self.assertEqual(status, 200)
        self.assertEqual(headers.get("Access-Control-Allow-Origin"), ORIGIN)
        result = json.loads(body)
        self.assertEqual(result["engine"], "TripoSR")
        self.assertTrue(result["engine_found"])
        self.assertFalse(result["inference_verified"])

    def test_valid_image_runs_fixed_fake_test_runner_and_returns_real_glb_bytes(self):
        status, body, headers = self.request("/v1/generate", PHOTO)
        self.assertEqual(status, 200, body)
        self.assertEqual(body, GLB)
        self.assertEqual(headers.get("Content-Type"), "model/gltf-binary")
        self.assertEqual(headers.get("Access-Control-Allow-Origin"), ORIGIN)
        self.assertFalse(list(Path(self.tmp.name).rglob("source.png")))

    def test_rejects_unapproved_origins_and_invalid_image(self):
        status, _, headers = self.request("/v1/generate", PHOTO, origin="https://attacker.example")
        self.assertEqual(status, 403)
        self.assertNotIn("Access-Control-Allow-Origin", headers)
        status, _, _ = self.request("/v1/generate", b"not an image"*10)
        self.assertEqual(status, 422)
        status, _, _ = self.request("/v1/generate", PHOTO, mime="text/plain")
        self.assertEqual(status, 415)
        status, _, _ = self.request("/v1/generate", PHOTO, origin="")
        self.assertEqual(status, 403)

    def test_preflight_is_scoped_and_concurrency_limited(self):
        status, _, headers = self.request(
            "/v1/generate", method="OPTIONS",
            headers={"Access-Control-Request-Method": "POST",
                     "Access-Control-Request-Private-Network": "true"},
        )
        self.assertEqual(status, 204)
        self.assertEqual(headers.get("Access-Control-Allow-Private-Network"), "true")
        self.service.lock.acquire()
        try:
            status, _, _ = self.request("/v1/generate", PHOTO)
            self.assertEqual(status, 429)
        finally:
            self.service.lock.release()

    def test_no_model_no_upload_and_glb_external_resources_rejected(self):
        (self.service.repo_dir / "run.py").unlink()
        status, body, _ = self.request("/v1/generate", PHOTO)
        self.assertEqual(status, 503)
        self.assertIn("not installed", body.decode())
        with self.assertRaises(ValueError):
            bridge.validate_glb(b"not a GLB")
        self.assertFalse(bridge.valid_image(b"FAKE" * 20, "image/png"))


if __name__ == "__main__":
    unittest.main()
