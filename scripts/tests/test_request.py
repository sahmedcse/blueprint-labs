import json

from test_ticket import new as new_ticket
from test_ticket_move import move


def test_new_request_then_status(root):
    rid = root.run("request.sh", "new", "Todo lists", "--text", "users keep todo lists").stdout.strip()
    assert rid == "REQ-0001-todo-lists"
    assert "users keep todo lists" in (root.path / "requests" / rid / "request.md").read_text()
    assert root.subjects() == [f"request({rid}): open Todo lists"]
    assert root.run("request.sh", "new", "Second", "--text", "x").stdout.strip() == "REQ-0002-second"


def test_status_aggregates_everything(root, monkeypatch):
    rid = root.run("request.sh", "new", "Todo", "--text", "x").stdout.strip()
    # tickets for this request (test_ticket uses REQ-0001-todo)
    new_ticket(root, "schema", "--status", "ready")
    new_ticket(root, "api", "--depends", "T-0001")
    move(root, "T-0001", "in_progress", "go")
    move(root, "T-0001", "in_review", "PR", "--pr", "https://github.com/o/acme-api/pull/7")
    out = root.run("request.sh", "status", "REQ-0001", "--no-gh", "--phase", "development",
                   "--loop", "product=approved", "--loop", "design=review", "--blocker", "need AWS creds").stdout
    assert "REQ-0001-todo · Todo · phase development" in out and "BLOCKED: need AWS creds" in out
    s = json.loads((root.path / "requests" / rid / "status.json").read_text())
    assert s["counts"]["in_review"] == 1 and s["counts"]["backlog"] == 1
    assert s["loops"] == {"product": "approved", "design": "review"}
    assert s["prs"] == [{"ticket": "T-0001", "url": "https://github.com/o/acme-api/pull/7",
                         "repo": "acme-api", "number": 7, "state": "unknown"}]
    kinds = [e["kind"] for e in s["journal"]]
    assert kinds[0] == "request" and kinds.count("ticket") == 4
    # loops and blockers persist; clear-blockers clears
    root.run("request.sh", "status", "REQ-0001", "--no-gh", "--clear-blockers")
    s = json.loads((root.path / "requests" / rid / "status.json").read_text())
    assert s["blockers"] == [] and s["phase"] == "development" and s["loops"]["design"] == "review"


def test_bad_loop_state(root):
    root.run("request.sh", "new", "Todo", "--text", "x")
    assert root.run("request.sh", "status", "REQ-0001", "--loop", "design=maybe", check=False).returncode == 2
