import json
import subprocess

from test_devloop import make_product_repo
from test_ticket import new

REQ = "REQ-0001-todo"


def setup(root, kind="web", makefile="gate:\n\t@echo gate ran\n"):
    p = make_product_repo(root)
    (root.path / "repos.json").write_text(json.dumps({"repos": [{"name": "acme-api", "kind": kind, "path": "acme-api"}]}))
    new(root, "thing", "--status", "ready")
    root.run("worktree.sh", "create", REQ, "T-0001")
    wt = root.path / ".worktrees" / REQ / "T-0001"
    (wt / "Makefile").write_text(makefile)
    git(wt, "add", "Makefile")
    git(wt, "commit", "-qm", "build: add gate target")
    return wt


def git(wt, *args):
    subprocess.run(["git", "-C", str(wt), "-c", "user.email=t@e", "-c", "user.name=t", *args], check=True)


def result(root, it=1):
    return json.loads((root.path / ".runs" / REQ / "tickets" / "T-0001" / f"gate.iter{it}.json").read_text())


def test_pass_then_verify(root):
    wt = setup(root)
    r = root.run("gate.sh", REQ, "T-0001", "1")
    assert "GATE PASS" in r.stdout and result(root)["status"] == "pass"
    assert root.run("verify-gate.sh", REQ, "T-0001").returncode == 0
    (wt / "late.txt").write_text("x")
    assert root.run("verify-gate.sh", REQ, "T-0001", check=False).returncode == 1


def test_make_gate_failure(root):
    setup(root, makefile="gate:\n\t@exit 3\n")
    r = root.run("gate.sh", REQ, "T-0001", "1", check=False)
    assert r.returncode == 1 and result(root)["first_failed_step"] == "make gate"


def test_suppression_and_uncommitted_fail(root):
    wt = setup(root)
    (wt / "a.ts").write_text("// @ts-ignore\nconst x = 1\n")
    git(wt, "add", "a.ts")
    git(wt, "commit", "-qm", "feat: sneaky")
    assert root.run("gate.sh", REQ, "T-0001", "1", check=False).returncode == 1
    assert result(root)["first_failed_step"] == "no-new-suppressions"


def test_bad_commit_message_fails(root):
    wt = setup(root)
    (wt / "b.txt").write_text("x\n")
    git(wt, "add", "b.txt")
    git(wt, "commit", "-qm", "stuff")
    root.run("gate.sh", REQ, "T-0001", "1", check=False)
    assert result(root)["first_failed_step"] == "commit-check"


def test_uncommitted_fails(root):
    wt = setup(root)
    (wt / "c.txt").write_text("x\n")
    root.run("gate.sh", REQ, "T-0001", "1", check=False)
    assert result(root)["first_failed_step"] == "all-committed"
