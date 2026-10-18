import json

from test_ticket import new, listed

REQ = "REQ-0001-todo"


def move(root, tid, status, why="because", *extra, check=True):
    return root.run("ticket.sh", "move", tid, status, "--why", why, *extra, check=check)


def test_illegal_move_is_refused(root):
    new(root, "a")
    r = move(root, "T-0001", "done", check=False)
    assert r.returncode == 1 and "cannot move backlog → done" in r.stderr
    assert listed(root)["T-0001"]["status"] == "backlog"


def test_in_progress_waits_for_dependencies(root):
    new(root, "a", "--status", "ready")
    new(root, "b", "--depends", "T-0001", "--status", "ready")
    r = move(root, "T-0002", "in_progress", check=False)
    assert r.returncode == 1 and "waiting on T-0001" in r.stderr


def test_in_review_needs_pr(root):
    new(root, "a", "--status", "ready")
    move(root, "T-0001", "in_progress", "started")
    assert move(root, "T-0001", "in_review", check=False).returncode == 1
    move(root, "T-0001", "in_review", "PR opened", "--pr", "https://github.com/o/acme-api/pull/3")
    assert listed(root)["T-0001"]["pr"] == "https://github.com/o/acme-api/pull/3"


def test_full_flow_logs_journals_commits_and_promotes(root):
    new(root, "schema", "--status", "ready")
    new(root, "api", "--depends", "T-0001")
    assert [t["id"] for t in json.loads(root.run("ticket.sh", "ready-set", "--json").stdout)] == ["T-0001"]
    move(root, "T-0001", "in_progress", "worktree created")
    move(root, "T-0001", "in_review", "PR opened", "--pr", "https://x/pull/1")
    out = move(root, "T-0001", "done", "PR merged").stdout
    assert "promoted T-0002" in out
    t = listed(root)
    assert t["T-0001"]["status"] == "done" and t["T-0002"]["status"] == "ready"
    body = next((root.path / "tickets").glob("T-0001-*.md")).read_text()
    assert "in_progress → in_review: PR opened (https://x/pull/1)" in body
    assert "backlog → ready: all dependencies done (last was T-0001)" in \
        next((root.path / "tickets").glob("T-0002-*.md")).read_text()
    assert root.subjects()[0] == "ticket(T-0001): in_review → done — PR merged"
    journal = (root.path / "decisions" / "journal.md").read_text()
    assert "in_review → done: PR merged; promoted T-0002 to ready" in journal
    assert [x["id"] for x in json.loads(root.run("ticket.sh", "ready-set", "--json").stdout)] == ["T-0002"]


def test_dropped_is_final(root):
    new(root, "a", "--status", "ready")
    move(root, "T-0001", "dropped", "out of scope")
    assert move(root, "T-0001", "ready", check=False).returncode == 1
