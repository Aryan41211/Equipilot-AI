# EquiPilot AI - Frontend Health Check Server
# Lightweight HTTP server for Docker health checks (Streamlit has no built-in health endpoint)

import http.server
import json
import os
import sys


class HealthCheckHandler(http.server.BaseHTTPRequestHandler):
    """Simple health check endpoint for Docker container health probes."""

    def do_GET(self):
        if self.path == "/healthz":
            self._respond(200, {"status": "ok"})
        elif self.path == "/ready":
            self._respond(200, {"status": "ready"})
        else:
            self._respond(404, {"status": "not_found"})

    def _respond(self, code: int, payload: dict) -> None:
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def log_message(self, format, *args):
        """Suppress default HTTP server logging."""
        pass


def main():
    """Serve /healthz on HEALTH_CHECK_HOST:HEALTH_CHECK_PORT (default 0.0.0.0:9090)."""
    host = os.environ.get("HEALTH_CHECK_HOST", "0.0.0.0")
    port = int(os.environ.get("HEALTH_CHECK_PORT", "9090"))
    server = http.server.HTTPServer((host, port), HealthCheckHandler)
    sys.stdout.write(f"Health check server listening on {host}:{port}\n")
    sys.stdout.flush()
    server.serve_forever()


if __name__ == "__main__":
    main()
