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
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress default HTTP server logging."""
        pass


def main():
    port = int(os.environ.get("HEALTH_CHECK_PORT", "9090"))
    server = http.server.HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    sys.stdout.write(f"Health check server listening on port {port}\n")
    sys.stdout.flush()
    server.serve_forever()


if __name__ == "__main__":
    main()
