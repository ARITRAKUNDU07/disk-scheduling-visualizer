"""High-Performance Native HTTP/API Server for OSRM.

Built strictly on Python's standard library (http.server.ThreadingHTTPServer).
Features:
- Pure offline static file streaming with strict path-traversal sandboxing.
- RESTful JSON API endpoints mapping directly to core algorithms.
- 1 MB request payload safety ceiling.
- Audit logging of every request latency and status to logs/activity.log.
- Explicit binding to 127.0.0.1 (loopback interface).
"""

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import time
import traceback
from typing import Any, Callable, Dict, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from core.logger import log_event
from core.validators import OSRMError
import web.api as api_routes

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = (PROJECT_ROOT / "web" / "static").resolve()
OUTPUT_CHARTS_DIR = (PROJECT_ROOT / "output" / "charts").resolve()
MAX_BODY_BYTES = 1_048_576  # 1 MB ceiling


class OSRMRequestHandler(BaseHTTPRequestHandler):
    """Custom HTTP request handler serving static UI assets and routing REST API calls."""

    server_version = "OSRM-Server/1.0"

    def send_response(self, code: int, message: Optional[str] = None) -> None:
        self.current_status = int(code)
        super().send_response(code, message)

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default stderr HTTP logging to keep console clean for CLI/server view."""
        pass

    def _set_security_headers(self, content_type: str, is_api: bool = False) -> None:
        """Inject mandated defensive HTTP headers."""
        self.send_header("Content-Type", content_type)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        if is_api:
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        else:
            self.send_header("Cache-Control", "public, max-age=3600")

    def _send_json_response(self, status: int, data: Any) -> None:
        """Serialize and transmit a JSON payload."""
        payload_bytes = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self._set_security_headers("application/json; charset=utf-8", is_api=True)
        self.send_header("Content-Length", str(len(payload_bytes)))
        self.end_headers()
        self.wfile.write(payload_bytes)

    def _send_error_json(self, status: int, message: str, field: Optional[str] = None) -> None:
        """Standardized JSON error responder."""
        body = {"error": message}
        if field:
            body["field"] = field
        self._send_json_response(status, body)

    def _read_json_body(self) -> Optional[Dict[str, Any]]:
        """Safely read and deserialize inbound JSON payload respecting size ceilings."""
        content_length_header = self.headers.get("Content-Length")
        if not content_length_header:
            return {}

        try:
            content_length = int(content_length_header)
        except ValueError:
            self._send_error_json(HTTPStatus.BAD_REQUEST, "Invalid Content-Length header", "Content-Length")
            return None

        if content_length > MAX_BODY_BYTES:
            try:
                discarded = 0
                while discarded < content_length:
                    chunk = self.rfile.read(min(65536, content_length - discarded))
                    if not chunk:
                        break
                    discarded += len(chunk)
            except Exception:
                pass

            self._send_error_json(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                f"Request body exceeds 1 MB limit (received {content_length} bytes)",
                "body"
            )
            return None

        raw_bytes = self.rfile.read(content_length)
        if not raw_bytes:
            return {}

        try:
            return json.loads(raw_bytes.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            self._send_error_json(HTTPStatus.BAD_REQUEST, "Malformed JSON request body", "body")
            return None

    def _serve_static_file(self, req_path: str) -> None:
        """Safely stream static files with path-traversal prevention."""
        clean_path = req_path.split("?")[0].lstrip("/")
        if clean_path == "" or clean_path == "index.html":
            target_file = STATIC_DIR / "index.html"
        elif clean_path.startswith("output/charts/"):
            # Allow serving dynamic report charts
            chart_filename = clean_path.replace("output/charts/", "")
            target_file = OUTPUT_CHARTS_DIR / chart_filename
        else:
            target_file = (STATIC_DIR / clean_path).resolve()

        # Path traversal guard: ensure resolved path starts within allowed directories
        try:
            target_str = str(target_file.resolve())
            is_in_static = os.path.commonpath([str(STATIC_DIR), target_str]) == str(STATIC_DIR)
            is_in_charts = os.path.commonpath([str(OUTPUT_CHARTS_DIR), target_str]) == str(OUTPUT_CHARTS_DIR)
        except (ValueError, OSError):
            self._send_error_json(HTTPStatus.FORBIDDEN, "Access forbidden", "path")
            return

        if not (is_in_static or is_in_charts) or not target_file.is_file():
            self._send_error_json(HTTPStatus.NOT_FOUND, f"Resource not found: {req_path}", "path")
            return

        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(str(target_file))
        if not mime_type:
            if target_file.suffix == ".js":
                mime_type = "application/javascript"
            elif target_file.suffix == ".css":
                mime_type = "text/css"
            elif target_file.suffix == ".html":
                mime_type = "text/html"
            else:
                mime_type = "application/octet-stream"

        file_bytes = target_file.read_bytes()
        self.send_response(HTTPStatus.OK)
        self._set_security_headers(f"{mime_type}; charset=utf-8" if "text" in mime_type or "javascript" in mime_type else mime_type, is_api=False)
        self.send_header("Content-Length", str(len(file_bytes)))
        self.end_headers()
        self.wfile.write(file_bytes)

    # -------------------------------------------------------------------------
    # Route Handlers
    # -------------------------------------------------------------------------

    def do_GET(self) -> None:
        start_time = time.perf_counter()
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        status_code = HTTPStatus.OK
        try:
            if path == "/api/meta":
                data = api_routes.get_meta()
                self._send_json_response(HTTPStatus.OK, data)

            elif path.startswith("/api/samples/"):
                module_name = path.replace("/api/samples/", "").strip()
                data = api_routes.get_samples(module_name)
                self._send_json_response(HTTPStatus.OK, data)

            elif path == "/api/summary":
                data = api_routes.get_summary()
                self._send_json_response(HTTPStatus.OK, data)

            elif path == "/api/pages/belady":
                data = api_routes.handle_pages_belady()
                self._send_json_response(HTTPStatus.OK, data)

            elif path == "/api/logs/summary":
                data = api_routes.handle_logs_summary()
                self._send_json_response(HTTPStatus.OK, data)

            elif path == "/api/sysinfo":
                data = api_routes.handle_sysinfo()
                self._send_json_response(HTTPStatus.OK, data)

            elif path.startswith("/api/"):
                status_code = HTTPStatus.NOT_FOUND
                self._send_error_json(status_code, f"API endpoint not found: {path}", "path")

            else:
                self._serve_static_file(path)
                status_code = HTTPStatus.OK

        except OSRMError as exc:
            status_code = HTTPStatus.BAD_REQUEST
            self._send_error_json(status_code, exc.message, exc.field)
        except Exception as exc:
            status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            log_event("server", f"Unhandled GET exception on {path}: {str(exc)}", level="ERROR", exc_info=exc)
            self._send_error_json(status_code, "Internal error")
        finally:
            ms = (time.perf_counter() - start_time) * 1000.0
            logged_status = getattr(self, "current_status", int(status_code))
            log_event("server", f"GET {path} -> {logged_status} ({ms:.2f} ms)")

    def do_POST(self) -> None:
        start_time = time.perf_counter()
        parsed = urlparse(self.path)
        path = parsed.path

        status_code = HTTPStatus.OK
        try:
            body = self._read_json_body()
            if body is None:
                # Error response already transmitted by _read_json_body
                return

            routes: Dict[str, Callable[[Any], Dict[str, Any]]] = {
                "/api/disk/run": api_routes.handle_disk_run,
                "/api/disk/compare": api_routes.handle_disk_compare,
                "/api/cpu/run": api_routes.handle_cpu_run,
                "/api/cpu/compare": api_routes.handle_cpu_compare,
                "/api/pages/run": api_routes.handle_pages_run,
                "/api/pages/compare": api_routes.handle_pages_compare,
                "/api/deadlock/safety": api_routes.handle_deadlock_safety,
                "/api/deadlock/request": api_routes.handle_deadlock_request,
                "/api/report/generate": api_routes.handle_report_generate,
                "/api/tests/run": api_routes.handle_tests_run,
            }

            if path in routes:
                handler = routes[path]
                res_data = handler(body)
                self._send_json_response(HTTPStatus.OK, res_data)
            else:
                status_code = HTTPStatus.NOT_FOUND
                self._send_error_json(status_code, f"API endpoint not found: {path}", "path")

        except OSRMError as exc:
            status_code = HTTPStatus.BAD_REQUEST
            self._send_error_json(status_code, exc.message, exc.field)
        except Exception as exc:
            status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            log_event("server", f"Unhandled POST exception on {path}: {str(exc)}", level="ERROR", exc_info=exc)
            self._send_error_json(status_code, "Internal error")
        finally:
            ms = (time.perf_counter() - start_time) * 1000.0
            logged_status = getattr(self, "current_status", int(status_code))
            log_event("server", f"POST {path} -> {logged_status} ({ms:.2f} ms)")


def create_server(host: str = "127.0.0.1", port: int = 8080) -> ThreadingHTTPServer:
    """Instantiate a multi-threaded HTTP server bound strictly to loopback interface."""
    server_address = (host, port)
    return ThreadingHTTPServer(server_address, OSRMRequestHandler)


def run_web_server(host: str = "127.0.0.1", port: int = 8080) -> None:
    """Start the HTTP server on the main thread and serve indefinitely until interrupted."""
    server = create_server(host, port)
    url = f"http://{host}:{port}"
    print(f"\n=======================================================")
    print(f"  OS Resource Manager Simulator (OSRM) Web Server     ")
    print(f"  Endpoint: {url}")
    print(f"  Static Root: {STATIC_DIR}")
    print(f"  Bound to: {host} (Local loopback only)")
    print(f"  Press Ctrl+C to terminate.")
    print(f"=======================================================\n")
    log_event("server", f"Server started at {url}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[OSRM] Terminating server gracefully...")
    finally:
        server.server_close()
        log_event("server", "Server shutdown complete.")
        print("[OSRM] Server stopped.")
