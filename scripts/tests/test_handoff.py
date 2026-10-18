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


