import json
import os
import shutil
import subprocess
import sys
import time

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REQ = "REQ-0001-demo"
PAGE = "<html><body><h1>Checkout</h1><button>Pay</button></body></html>"


@pytest.fixture
def root(tmp_path):
    shutil.copytree(os.path.join(REPO, "review"), tmp_path / "review",
                    ignore=shutil.ignore_patterns("tests", "__pycache__"))
    shutil.copytree(os.path.join(REPO, "scripts", "lib"), tmp_path / "scripts" / "lib",
                    ignore=shutil.ignore_patterns("__pycache__"))
    subprocess.run(["git", "init", "-q", "-b", "main", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.email", "t@e.com"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "t"], check=True)
    art = tmp_path / ".runs" / REQ / "artifacts" / "design"
    art.mkdir(parents=True)
    (art / "checkout.html").write_text(PAGE)
    return tmp_path


def run(root, *args, check=True):
    env = {**os.environ, "BPL_NO_NOTIFY": "1"}
    r = subprocess.run([str(root / "review" / "review.sh"), *args], capture_output=True, text=True, env=env)
    if check:
        assert r.returncode == 0, r.stderr
    return r


@pytest.fixture
def served(root):
    proc = subprocess.Popen([str(root / "review" / "review.sh"), "serve", REQ], stdout=subprocess.PIPE, text=True)
    proc.stdout.readline()
    yield root
    proc.terminate()
    proc.wait()


def post_notes(root, key, rev, decision, texts):
    nf = root / ".runs" / REQ / "notes" / (key + ".json")
    nf.parent.mkdir(parents=True, exist_ok=True)
    nf.write_text(json.dumps({"rev": rev, "done": True, "decision": decision,
                              "notes": [{"label": "Checkout", "target": "Pay", "text": t} for t in texts]}))


def reviews(root):
    return json.loads((root / ".runs" / REQ / "reviews.json").read_text())["artifacts"]


def test_register_injects_layer_idempotently(root):
    rev = run(root, "register", REQ, "design/checkout", "--owner", "ux-designer", "--title", "Checkout").stdout.strip()
    page = (root / ".runs" / REQ / "artifacts" / "design" / "checkout.html").read_text()
    assert page.count("bpl:begin") == 1 and '"rev": "%s"' % rev in page
    assert run(root, "register", REQ, "design/checkout").stdout.strip() == rev
    page2 = (root / ".runs" / REQ / "artifacts" / "design" / "checkout.html").read_text()
    assert page2.count("bpl:begin") == 1
    assert reviews(root)["design/checkout"]["round"] == 1


def test_register_requires_owner_and_file(root):
    assert run(root, "register", REQ, "design/checkout", check=False).returncode == 2
    assert run(root, "register", REQ, "design/missing", "--owner", "x", check=False).returncode == 2


def test_wait_reports_server_down(root):
    run(root, "register", REQ, "design/checkout", "--owner", "ux-designer")
    r = run(root, "wait", REQ, check=False)
    assert r.returncode == 1 and r.stdout.startswith("SERVER DOWN")


def test_wait_idle_when_nothing_pending(served):
    r = run(served, "wait", REQ, check=False)
    assert r.returncode == 3 and r.stdout.startswith("IDLE")


def test_revise_then_approve_with_trail(served):
    root = served
    rev = run(root, "register", REQ, "design/checkout", "--owner", "ux-designer", "--title", "Checkout").stdout.strip()
    post_notes(root, "design/checkout", rev, "revise", ["Make Pay bigger"])
    r = run(root, "wait", REQ, "--interval", "0.1")
    assert "DECISION artifact=design/checkout owner=ux-designer decision=revise" in r.stdout
    assert reviews(root)["design/checkout"]["state"] == "revise"
    notes = run(root, "notes", REQ, "design/checkout").stdout
    assert '[Checkout] on "Pay": Make Pay bigger' in notes

    # The owner revises; re-registering bumps the round and sets the old notes aside.
    page = root / ".runs" / REQ / "artifacts" / "design" / "checkout.html"
    page.write_text(page.read_text().replace("<button>Pay</button>", "<button class=big>Pay</button>"))
    rev2 = run(root, "register", REQ, "design/checkout").stdout.strip()
    assert rev2 != rev and reviews(root)["design/checkout"]["round"] == 2

    post_notes(root, "design/checkout", rev2, "approve", [])
    r = run(root, "wait", REQ, "--interval", "0.1")
    assert "decision=approve" in r.stdout and "round=2" in r.stdout

    archived = (root / "requests" / REQ / "artifacts" / "design" / "checkout.html").read_text()
    assert "bpl:begin" not in archived and "big" in archived
    assert (root / "requests" / REQ / "reviews" / "design" / "checkout" / "round-1.json").exists()
    journal = (root / "decisions" / "journal.md").read_text()
    assert "revise (1 notes), round 1: 1) Make Pay bigger" in journal and "approved, round 2" in journal
    log = subprocess.run(["git", "-C", str(root), "log", "--format=%s"], capture_output=True, text=True).stdout
    assert log.splitlines() == [f"review({REQ}): design/checkout approved, round 2",
                                f"review({REQ}): design/checkout revise (1 notes), round 1"]


def test_stale_decision_is_set_aside(served):
    root = served
    run(root, "register", REQ, "design/checkout", "--owner", "ux-designer")
    post_notes(root, "design/checkout", "oldrev", "approve", [])
    proc = subprocess.Popen([str(root / "review" / "review.sh"), "wait", REQ, "--interval", "0.1"],
                            stdout=subprocess.PIPE, text=True, env={**os.environ, "BPL_NO_NOTIFY": "1"})
    assert proc.stdout.readline().startswith("STALE: design/checkout")
    proc.terminate()
    proc.wait()
    assert reviews(root)["design/checkout"]["state"] == "pending"


def test_size_warning(root):
    big = "<html><body>" + "".join(f"<h2>S{i}</h2>" for i in range(10)) + "</body></html>"
    (root / ".runs" / REQ / "artifacts" / "design" / "big.html").write_text(big)
    r = run(root, "register", REQ, "design/big", "--owner", "ux-designer")
    assert "WARN: design/big is large" in r.stderr


def test_parent_approval_cascades_to_pending_details(served):
    root = served
    art = root / ".runs" / REQ / "artifacts" / "product"
    art.mkdir(parents=True)
    for k in ("overview", "prd-a", "prd-b"):
        (art / f"{k}.html").write_text(f"<html><body>{k}</body></html>")
    rev = run(root, "register", REQ, "product/overview", "--owner", "product-manager").stdout.strip()
    rev_a = run(root, "register", REQ, "product/prd-a", "--owner", "prd-writer", "--parent", "product/overview").stdout.strip()
    run(root, "register", REQ, "product/prd-b", "--owner", "prd-writer", "--parent", "product/overview")
    run(root, "register", REQ, "design/checkout", "--owner", "ux-designer")
    # A detail can be revised on its own.
    post_notes(root, "product/prd-a", rev_a, "revise", ["Scope down"])
    assert "artifact=product/prd-a" in run(root, "wait", REQ, "--interval", "0.1").stdout
    post_notes(root, "product/overview", rev, "approve", [])
    out = run(root, "wait", REQ, "--interval", "0.1").stdout
    assert "artifact=product/overview" in out and "also_approved=product/prd-b" in out
    r = reviews(root)
    assert r["product/prd-b"]["state"] == "approved" and r["product/prd-a"]["state"] == "revise"
    assert r["design/checkout"]["state"] == "pending"
    assert (root / "requests" / REQ / "artifacts" / "product" / "prd-b.html").exists()
    assert "approved with product/overview" in (root / "decisions" / "journal.md").read_text()
    assert "under product/overview" in run(root, "list", REQ).stdout


def test_withdraw(root):
    run(root, "register", REQ, "design/checkout", "--owner", "ux-designer")
    run(root, "withdraw", REQ, "design/checkout", "--why", "replaced by a later step")
    assert reviews(root)["design/checkout"]["state"] == "withdrawn"
    assert "withdrawn: replaced by a later step" in (root / "decisions" / "journal.md").read_text()
