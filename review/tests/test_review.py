import json
import os
import shutil
import subprocess
import sys

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


def test_size_warning(root):
    big = "<html><body>" + "".join(f"<h2>S{i}</h2>" for i in range(10)) + "</body></html>"
    (root / ".runs" / REQ / "artifacts" / "design" / "big.html").write_text(big)
    r = run(root, "register", REQ, "design/big", "--owner", "ux-designer")
    assert "WARN: design/big is large" in r.stderr
