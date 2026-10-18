import json

from test_gate import setup, git

REQ = "REQ-0001-todo"


def write(root, name, obj):
    p = root.path / ".runs" / REQ / "tickets" / "T-0001" / name
    p.write_text(json.dumps(obj))


def spec(findings):
    return {"schema": "blueprint.review.spec.v1", "findings": findings}


def merged(root, it=1):
    return json.loads((root.path / ".runs" / REQ / "tickets" / "T-0001" / f"review.iter{it}.json").read_text())


def test_merge_review_policy(root):
    setup(root)
    write(root, "review.iter1.spec.json", spec([{"criterion": 1, "problem": f"s{i}"} for i in range(5)]))
    write(root, "review.iter1.quality.json", {"findings": [{"problem": "dup", "escalate": True}, {"problem": "naming"}]})
    write(root, "review.iter1.security.json", {"findings": [{"severity": "high", "problem": "sqli"}, {"severity": "low", "problem": "hdr"}]})
    root.run("merge-review.sh", REQ, "T-0001", "1")
    m = merged(root)
    blocking = [f["problem"] for f in m["findings"] if f["severity"] == "blocking"]
    assert blocking == ["sqli", "dup", "s0", "s1", "s2"]
    assert m["verdict"] == "changes_requested"
    assert [f["problem"] for f in m["findings"] if f.get("demoted")] == ["s3", "s4"]
    assert m["findings"][0]["id"] == "R1.1"


def test_missing_spec_fails_and_missing_quality_is_advisory(root):
    setup(root)
    assert root.run("merge-review.sh", REQ, "T-0001", "1", check=False).returncode == 1
    write(root, "review.iter1.spec.json", spec([{"problem": "no criterion"}]))
    assert root.run("merge-review.sh", REQ, "T-0001", "1", check=False).returncode == 1
    write(root, "review.iter1.spec.json", spec([]))
    root.run("merge-review.sh", REQ, "T-0001", "1")
    m = merged(root)
    assert m["verdict"] == "approved" and m["findings"][0]["problem"] == "quality review missing or unparseable"


def test_brief_carries_failures_and_findings(root):
    setup(root, makefile="gate:\n\t@echo boom-marker; exit 1\n")
    root.run("gate.sh", REQ, "T-0001", "1", check=False)
    write(root, "review.iter1.json", {"findings": [{"id": "R1.1", "severity": "blocking", "file": "a.go", "line": 3,
                                                   "problem": "no 409", "fix": "return 409"}]})
    b = root.run("brief.sh", REQ, "T-0001", "2").stdout
    assert "You are the backend-developer. Implement ticket T-0001 (thing), iteration 2 of 3." in b
    assert "boom-marker" in b and "[R1.1] a.go:3: no 409 Fix: return 409" in b
    assert "principles/learnings/backend-developer.md" in b and "## Acceptance criteria" in b


def test_pr_body(root):
    wt = setup(root)
    root.run("gate.sh", REQ, "T-0001", "1")
    write(root, "review.iter1.json", {"findings": [{"severity": "advisory", "source": "quality", "problem": "rename x"}]})
    body = root.run("pr-body.sh", REQ, "T-0001").stdout
    assert body.startswith("**T-0001** · thing")
    assert "Gate passed at iteration 1" in body and "rename x" in body and "build: add gate target" in body
