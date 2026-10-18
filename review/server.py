"""Loopback-only review server for one request. Started by `review/review.sh serve <REQ>`.

    python3 review/server.py <repo-root> <req-id> [--port N]

Routes
  GET  /                    the hub (review/hub.html)
  GET  /_review/<file>      review assets: annotate.js, base.css, vendor/mermaid.min.js
  GET  /a/<path>            the request's artifacts (.runs/<REQ>/artifacts/<path>)
  GET  /__reviews           .runs/<REQ>/reviews.json  (artifact list + review state)
  GET  /__status            requests/<REQ>/status.json (overall status, tickets, journal)
  POST /__notes/<artifact>  the page's notes and decision -> .runs/<REQ>/notes/<artifact>.json

The base URL is written to .runs/<REQ>/review.url. Nothing leaves the machine.

Guards, because any page the user has open can reach a local server:
- bound to 127.0.0.1 only;
- a POST must be Content-Type: application/json, so a cross-origin page cannot send one without a
  CORS preflight, which this server never answers;
- the Host header must name this exact loopback port, so DNS rebinding cannot reach it;
- the body is capped at 1 MiB and must be a JSON object with a `notes` list;
- the artifact key must be [a-z0-9-/] and resolve inside the notes directory.
"""
import json
import os
import re
import sys
import tempfile
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

MAX_BODY = 1 << 20
KEY_RE = re.compile(r"^[a-z0-9][a-z0-9-]*(/[a-z0-9][a-z0-9-]*)*$")


def atomic_write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".tmp-", suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(obj, f, indent=2)
    os.replace(tmp, path)


def make_handler(root, req):
    review_dir = os.path.join(root, "review")
    run_dir = os.path.join(root, ".runs", req)
    artifacts_dir = os.path.join(run_dir, "artifacts")
    notes_dir = os.path.join(run_dir, "notes")
    status_file = os.path.join(root, "requests", req, "status.json")
    reviews_file = os.path.join(run_dir, "reviews.json")

    class Handler(SimpleHTTPRequestHandler):
        def log_message(self, fmt, *args):  # keep background task output quiet
            pass

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

        def _reply(self, code, msg, ctype="text/plain"):
            body = msg.encode() if isinstance(msg, str) else msg
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _host_ok(self):
            port = self.server.server_address[1]
            return self.headers.get("Host") in (f"127.0.0.1:{port}", f"localhost:{port}")

        def _json_file(self, path, empty):
            try:
                with open(path, "rb") as f:
                    return self._reply(200, f.read(), "application/json")
            except FileNotFoundError:
                return self._reply(200, json.dumps(empty), "application/json")

        def translate_path(self, path):
            # Map URL prefixes onto their directories; anything else is a 404 path.
            p = unquote(urlparse(path).path)
            if p in ("/", "/index.html"):
                return os.path.join(review_dir, "hub.html")
            for prefix, base in (("/_review/", review_dir), ("/a/", artifacts_dir)):
                if p.startswith(prefix):
                    full = os.path.realpath(os.path.join(base, p[len(prefix):]))
                    if full == base or full.startswith(os.path.realpath(base) + os.sep):
                        return full
            return os.path.join(run_dir, "__nonexistent__")

        def do_GET(self):
            if not self._host_ok():
                return self._reply(403, "bad host")
            p = urlparse(self.path).path
            if p == "/__reviews":
                return self._json_file(reviews_file, {"req": req, "artifacts": {}})
            if p == "/__status":
                return self._json_file(status_file, {"req": req})
            return super().do_GET()

        def do_POST(self):
            if not self._host_ok():
                return self._reply(403, "bad host")
            p = unquote(urlparse(self.path).path)
            if not p.startswith("/__notes/"):
                return self._reply(404, "not found")
            key = p[len("/__notes/"):]
            if not KEY_RE.match(key):
                return self._reply(400, "bad artifact key")
            if not (self.headers.get("Content-Type") or "").startswith("application/json"):
                return self._reply(415, "json only")
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0 or length > MAX_BODY:
                return self._reply(413, "bad length")
            try:
                body = json.loads(self.rfile.read(length))
            except ValueError:
                return self._reply(400, "bad json")
            if not isinstance(body, dict) or not isinstance(body.get("notes"), list):
                return self._reply(400, "expected {notes: [...]}")
            # The request and artifact are whatever this server and URL say, never the page.
            body["req"], body["artifact"] = req, key
            atomic_write_json(os.path.join(notes_dir, key + ".json"), body)
            return self._reply(200, "ok")

    return Handler


def main(argv):
    if len(argv) < 2:
        sys.exit("usage: server.py <repo-root> <req-id> [--port N]")
    root, req = os.path.realpath(argv[0]), argv[1]
    port = int(argv[3]) if len(argv) > 3 and argv[2] == "--port" else 0
    run_dir = os.path.join(root, ".runs", req)
    os.makedirs(run_dir, exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(root, req))
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    with open(os.path.join(run_dir, "review.url"), "w") as f:
        f.write(url + "\n")
    print(url, flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main(sys.argv[1:])
