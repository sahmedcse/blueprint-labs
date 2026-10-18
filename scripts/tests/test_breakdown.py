import json

from test_ticket import listed

REQ = "REQ-0001-todo"


def breakdown(**over):
    b = {
        "schema": "blueprint.breakdown.v1", "req": REQ, "summary": "Todo lists with accounts.",
        "epics": [{"key": "e1", "title": "Accounts", "goal": "Sign up"}, {"key": "e2", "title": "Todos"}],
        "tickets": [
            {"ref": "api", "epic": "e2", "title": "Todo API", "repo": "acme-api", "owner_agent": "backend-developer",
             "estimate": "M", "depends_on": ["schema"], "acceptance": ["CRUD works"]},
            {"ref": "schema", "epic": "e2", "title": "Todos table", "repo": "acme-api", "type": "data",
             "owner_agent": "backend-developer", "estimate": "S", "acceptance": ["migration runs"]},
            {"ref": "ui", "epic": "e1", "title": "Sign-up screen", "repo": "acme-web", "owner_agent": "frontend-developer",
             "estimate": "L", "depends_on": ["api"], "acceptance": ["form validates"], "artifacts": ["design/sign-up"]},
        ],
        "open_questions": ["Do we need teams?"],
    }
    b.update(over)
    return b


def write(root, b):
    p = root.path / ".runs" / REQ / "breakdown.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(b))


def test_render_page(root):
    write(root, breakdown())
    out = root.run("ticket.sh", "breakdown", "render", REQ).stdout.strip()
    page = (root.path / out).read_text()
    assert out == f".runs/{REQ}/artifacts/product/breakdown.html"
    assert "3 tickets in 2 epics" in page and "schema --&gt; api" in page
    assert "Large tickets: ui" in page and "Do we need teams?" in page and page.count("</body>") == 1


def test_invalid_breakdown_refused(root):
    b = breakdown()
    b["tickets"][0]["depends_on"] = ["ghost"]
    b["tickets"][1]["acceptance"] = []
    write(root, b)
    r = root.run("ticket.sh", "breakdown", "render", REQ, check=False)
    assert r.returncode == 1 and "unknown ref 'ghost'" in r.stderr and "needs acceptance" in r.stderr


def test_import_creates_tickets_in_one_commit(root):
    write(root, breakdown())
    root.run("ticket.sh", "breakdown", "import", REQ)
    t = listed(root)
    assert [t[i]["title"] for i in sorted(t)] == ["Todo API", "Todos table", "Sign-up screen"]
    assert t["T-0001"]["depends_on"] == ["T-0002"] and t["T-0001"]["status"] == "backlog"
    assert t["T-0002"]["status"] == "ready" and t["T-0003"]["artifacts"] == ["design/sign-up"]
    assert t["T-0003"]["epic"] == "accounts"
    assert root.subjects() == [f"ticket({REQ}): create 3 tickets from approved breakdown"]
    kept = json.loads((root.path / "requests" / REQ / "breakdown.json").read_text())
    assert kept["ids"] == {"api": "T-0001", "schema": "T-0002", "ui": "T-0003"}
    assert root.run("ticket.sh", "breakdown", "import", REQ, check=False).returncode == 1
