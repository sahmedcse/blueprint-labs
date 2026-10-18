import json
import subprocess

from test_ticket import new

REQ = "REQ-0001-todo"


def make_product_repo(root, name="acme-api"):
    p = root.path / name
    p.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(p)], check=True)
    (p / "README.md").write_text("hi")
    subprocess.run(["git", "-C", str(p), "add", "."], check=True)
    subprocess.run(["git", "-C", str(p), "-c", "user.email=t@e", "-c", "user.name=t", "commit", "-qm", "init"], check=True)
    (root.path / "repos.json").write_text(json.dumps({"repos": [
        {"name": "acme-api", "kind": "go", "path": "acme-api"}, {"name": "acme-web", "kind": "web"}]}))
    return p


def state(root, tid="T-0001"):
    return json.loads((root.path / ".runs" / REQ / "tickets" / tid / "state.json").read_text())


def test_create_iter_cleanup(root):
    make_product_repo(root)
    new(root, "Todo CRUD API", "--status", "ready")
    branch = root.run("worktree.sh", "create", REQ, "T-0001").stdout.strip()
    assert branch == "feature/t-0001-todo-crud-api"
    wt = root.path / ".worktrees" / REQ / "T-0001"
    assert (wt / "README.md").exists()
    s = state(root)
    assert s["base"] == "main" and s["kind"] == "go" and s["iteration"] == 0
    assert root.run("worktree.sh", "create", REQ, "T-0001", check=False).returncode == 1

    assert root.run("iter.sh", "next", REQ, "T-0001").stdout.strip() == "1"
    root.run("iter.sh", "next", REQ, "T-0001")
    assert root.run("iter.sh", "undo", REQ, "T-0001").stdout.strip() == "1"
    root.run("iter.sh", "next", REQ, "T-0001")
    root.run("iter.sh", "next", REQ, "T-0001")
    r = root.run("iter.sh", "next", REQ, "T-0001", check=False)
    assert r.returncode == 1 and "used all 3 iterations" in r.stderr

    (wt / "dirty.txt").write_text("x")
    assert root.run("worktree.sh", "cleanup", REQ, "T-0001", check=False).returncode == 1
    (wt / "dirty.txt").unlink()
    root.run("worktree.sh", "cleanup", REQ, "T-0001")
    assert not wt.exists()


def test_create_requires_checked_out_repo(root):
    make_product_repo(root)
    root.run("ticket.sh", "new", "--request", REQ, "--title", "web thing", "--repo", "acme-web", "--owner", "frontend-developer")
    r = root.run("worktree.sh", "create", REQ, "T-0001", check=False)
    assert r.returncode == 1 and "not a git repository" in r.stderr
