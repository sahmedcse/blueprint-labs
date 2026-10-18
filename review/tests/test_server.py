import http.client
import json
import os
import subprocess
import sys
import time

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REVIEW = os.path.dirname(HERE)
REQ = "REQ-0001-demo"


@pytest.fixture
def server(tmp_path):
    root = tmp_path
    (root / "review").mkdir()
    (root / "review" / "hub.html").write_text("<html>hub</html>")
    art = root / ".runs" / REQ / "artifacts" / "design"
    art.mkdir(parents=True)
    (art / "checkout.html").write_text("<html><body>checkout</body></html>")
    proc = subprocess.Popen([sys.executable, os.path.join(REVIEW, "server.py"), str(root), REQ],
                            stdout=subprocess.PIPE, text=True)
    url = proc.stdout.readline().strip()
    port = int(url.rsplit(":", 1)[1].strip("/"))
    yield root, port
    proc.terminate()
    proc.wait()


def req(port, method, path, body=None, host=None, ctype="application/json"):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    headers = {"Host": host or f"127.0.0.1:{port}"}
    data = None
    if body is not None:
        data = json.dumps(body).encode() if not isinstance(body, bytes) else body
        headers["Content-Type"] = ctype
        headers["Content-Length"] = str(len(data))
    c.request(method, path, body=data, headers=headers)
    r = c.getresponse()
    return r.status, r.read().decode()


def test_serves_hub_and_artifacts(server):
    root, port = server
    assert req(port, "GET", "/") == (200, "<html>hub</html>")
    status, body = req(port, "GET", "/a/design/checkout.html")
    assert status == 200 and "checkout" in body


def test_url_file_written(server):
    root, port = server
    assert (root / ".runs" / REQ / "review.url").read_text().strip().endswith(f":{port}/")


def test_rejects_path_traversal(server):
    _, port = server
    assert req(port, "GET", "/a/../../review/hub.html")[0] == 404
    assert req(port, "GET", "/etc/passwd")[0] == 404


def test_rejects_bad_host(server):
    _, port = server
    assert req(port, "GET", "/", host="evil.example:80")[0] == 403
    assert req(port, "POST", "/__notes/design/checkout", {"notes": []}, host="evil.example")[0] == 403


def test_rejects_non_json_post(server):
    _, port = server
    assert req(port, "POST", "/__notes/design/checkout", b"notes=1", ctype="text/plain")[0] == 415


def test_rejects_bad_key_and_shape(server):
    _, port = server
    assert req(port, "POST", "/__notes/../x", {"notes": []})[0] in (400, 404)
    assert req(port, "POST", "/__notes/Design/X", {"notes": []})[0] == 400
    assert req(port, "POST", "/__notes/design/checkout", {"nope": 1})[0] == 400


def test_notes_saved_per_artifact(server):
    root, port = server
    body = {"rev": "abc", "done": True, "decision": "revise", "notes": [{"text": "bigger"}], "req": "spoof"}
    assert req(port, "POST", "/__notes/design/checkout", body)[0] == 200
    assert req(port, "POST", "/__notes/arch/adr-001", {"notes": []})[0] == 200
    saved = json.loads((root / ".runs" / REQ / "notes" / "design" / "checkout.json").read_text())
    assert saved["req"] == REQ and saved["artifact"] == "design/checkout"
    assert saved["notes"][0]["text"] == "bigger"
    assert (root / ".runs" / REQ / "notes" / "arch" / "adr-001.json").exists()


def test_status_and_reviews_default_when_missing(server):
    _, port = server
    status, body = req(port, "GET", "/__reviews")
    assert status == 200 and json.loads(body)["artifacts"] == {}
    assert json.loads(req(port, "GET", "/__status")[1])["req"] == REQ
