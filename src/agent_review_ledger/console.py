"""Single-operator loopback console. Not a production security boundary."""

from http.server import BaseHTTPRequestHandler, HTTPServer
from importlib import resources
import json
import secrets
from typing import cast


STATIC = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/app.css": ("app.css", "text/css; charset=utf-8"),
}


def create_server(store, port=8767):
    token = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def respond(self, code, data, content_type="application/json; charset=utf-8"):
            payload = json.dumps(data).encode() if not isinstance(data, bytes) else data
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; "
                "img-src 'none'; frame-ancestors 'none'; object-src 'none'; base-uri 'none'",
            )
            self.end_headers()
            self.wfile.write(payload)

        def valid_host(self):
            expected = "127.0.0.1:%s" % cast(HTTPServer, self.server).server_port
            return self.headers.get("Host") == expected

        def do_GET(self):
            if not self.valid_host():
                return self.respond(403, {"error": "invalid host"})
            if self.path == "/api/state":
                return self.respond(
                    200,
                    {"tasks": store.list_tasks(), "summary": store.summary(), "csrf": token},
                )
            if self.path in STATIC:
                name, mime = STATIC[self.path]
                payload = resources.files("agent_review_ledger").joinpath("static", name).read_bytes()
                return self.respond(200, payload, mime)
            return self.respond(404, {"error": "not found"})

        def do_POST(self):
            origin = "http://127.0.0.1:%s" % cast(HTTPServer, self.server).server_port
            if (
                not self.valid_host()
                or self.headers.get("Origin") != origin
                or not secrets.compare_digest(self.headers.get("X-Console-Token", ""), token)
            ):
                return self.respond(403, {"error": "local origin and token required"})
            if self.headers.get("Content-Type") != "application/json":
                return self.respond(415, {"error": "JSON required"})
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if size <= 0 or size > 16384:
                    return self.respond(413, {"error": "invalid body size"})
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict):
                    raise ValueError("JSON object required")
                if self.path == "/api/tasks":
                    result = store.create_task(**data)
                elif self.path == "/api/transition":
                    result = store.transition(**data)
                elif self.path == "/api/cost":
                    result = store.add_cost(**data)
                else:
                    return self.respond(404, {"error": "not found"})
                return self.respond(200, result)
            except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
                return self.respond(400, {"error": str(exc)})

    return HTTPServer(("127.0.0.1", port), Handler)
