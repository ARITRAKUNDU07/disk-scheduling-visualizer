"""Integration Tests for OSRM Native Web Server and REST API.

Spawns the ThreadingHTTPServer on an ephemeral port in a daemon thread, executes
HTTP queries using standard library urllib, and validates response schemas,
security headers, path-traversal protections, and size ceilings.
"""

from http import HTTPStatus
import json
import socket
import threading
import time
from typing import Any
import unittest
import urllib.error
import urllib.request

from web.server import create_server


def find_free_port() -> int:
    """Acquire a temporary open port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class TestAPIEndpoints(unittest.TestCase):
    server: Any = None
    server_thread: threading.Thread = None
    base_url: str = ""

    @classmethod
    def setUpClass(cls):
        port = find_free_port()
        cls.server = create_server("127.0.0.1", port)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.base_url = f"http://127.0.0.1:{port}"
        time.sleep(0.15)  # Allow socket to bind

    @classmethod
    def tearDownClass(cls):
        if cls.server:
            cls.server.shutdown()
            cls.server.server_close()

    def _http_get(self, path: str):
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if "json" in resp.headers.get("Content-Type", "") else content, resp.headers

    def _http_post(self, path: str, payload: dict):
        url = f"{self.base_url}{path}"
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content), resp.headers

    def test_meta_endpoint(self):
        status, data, headers = self._http_get("/api/meta")
        self.assertEqual(status, HTTPStatus.OK)
        self.assertIn("modules", data)
        self.assertIn("disk", data["modules"])
        self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")

    def test_summary_endpoint(self):
        status, data, _ = self._http_get("/api/summary")
        self.assertEqual(status, HTTPStatus.OK)
        self.assertIn("disk", data)
        self.assertIn("cpu", data)
        self.assertIn("pages", data)
        self.assertIn("deadlock", data)

    def test_samples_endpoint(self):
        status, data, _ = self._http_get("/api/samples/disk")
        self.assertEqual(status, HTTPStatus.OK)
        self.assertIn("sample", data)
        self.assertIn("large", data)

    def test_disk_compare_exact_benchmarks(self):
        payload = {
            "requests": [98, 183, 37, 122, 14, 124, 65, 67],
            "head": 53,
            "size": 200,
            "direction": "left",
            "count_jump": True,
            "ms_per_cyl": 1.0
        }
        status, data, _ = self._http_post("/api/disk/compare", payload)
        self.assertEqual(status, HTTPStatus.OK)
        results = data["results"]
        # Mandatory values check:
        # FCFS = 640 | SSTF = 236 | SCAN (left) = 236 | LOOK (left) = 208
        self.assertEqual(results["FCFS"]["total_movement"], 640)
        self.assertEqual(results["SSTF"]["total_movement"], 236)
        self.assertEqual(results["SCAN"]["total_movement"], 236)
        self.assertEqual(results["LOOK"]["total_movement"], 208)

    def test_disk_c_scan_c_look_benchmarks(self):
        payload = {
            "requests": [98, 183, 37, 122, 14, 124, 65, 67],
            "head": 53,
            "size": 200,
            "direction": "right",
            "count_jump": True,
            "ms_per_cyl": 1.0
        }
        status, data, _ = self._http_post("/api/disk/compare", payload)
        self.assertEqual(status, HTTPStatus.OK)
        results = data["results"]
        # C-SCAN (right, jump counted) = 382 | C-LOOK (right, jump counted) = 322
        self.assertEqual(results["C-SCAN"]["total_movement"], 382)
        self.assertEqual(results["C-LOOK"]["total_movement"], 322)

    def test_validation_error_returns_400(self):
        # Invalid disk size
        payload = {"requests": [10], "head": 50, "size": 1}
        url = f"{self.base_url}/api/disk/run"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=5):
                self.fail("Expected HTTP 400 Bad Request")
        except urllib.error.HTTPError as err:
            self.assertEqual(err.code, HTTPStatus.BAD_REQUEST)
            err_data = json.loads(err.read().decode("utf-8"))
            self.assertIn("error", err_data)
            self.assertEqual(err_data.get("field"), "size")

    def test_path_traversal_blocked(self):
        url = f"{self.base_url}/../../main.py"
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                # Should not serve sensitive files outside web/static
                self.assertNotEqual(resp.status, 200)
        except urllib.error.HTTPError as err:
            self.assertIn(err.code, (HTTPStatus.NOT_FOUND, HTTPStatus.FORBIDDEN))

    def test_oversized_payload_rejected(self):
        url = f"{self.base_url}/api/disk/run"
        huge_payload = {"padding": "X" * (1_048_576 + 500)}
        req = urllib.request.Request(
            url,
            data=json.dumps(huge_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=5):
                self.fail("Expected HTTP 413 or rejection")
        except urllib.error.HTTPError as err:
            self.assertIn(err.code, (HTTPStatus.REQUEST_ENTITY_TOO_LARGE, HTTPStatus.BAD_REQUEST))
        except (ConnectionResetError, ConnectionAbortedError):
            # TCP-level rejection before response completion is also a safe rejection
            pass


if __name__ == "__main__":
    unittest.main()
