import hashlib
import json

REQ = "REQ-0001-todo"


def test_adr_file_numbers_and_commits(root):
    d = root.path / ".runs" / REQ / "adr"
    d.mkdir(parents=True)
    (d / "use-go.md").write_text("# Use Go for acme-api\n\nBecause.")
    (d / "use-pg.md").write_text("# Use Postgres\n")
    assert root.run("adr.sh", "file", REQ, "use-go").stdout.strip() == "decisions/ADR-0001-use-go.md"
    assert root.run("adr.sh", "file", REQ, "use-pg").stdout.strip() == "decisions/ADR-0002-use-pg.md"
    assert root.run("adr.sh", "file", REQ, "use-go", check=False).returncode != 0
    assert root.subjects()[1] == "docs(adr): ADR-0001 Use Go for acme-api"
    assert "status: accepted" in (root.path / "decisions" / "ADR-0001-use-go.md").read_text()


def test_contracts_filed_and_checked(root):
    src = root.path / ".runs" / REQ / "contracts"
    src.mkdir(parents=True)
    (src / "todos.openapi.yaml").write_text("openapi: 3.1.0\n")
    (src / "index.json").write_text(json.dumps({"todos.openapi.yaml": {"producer": "acme-api", "consumers": ["acme-web"]}}))
    root.run("adr.sh", "contracts", REQ)
    assert (root.path / "contracts" / "todos.openapi.yaml").exists()
    want = hashlib.sha256(b"openapi: 3.1.0\n").hexdigest()
    (root.path / "repos.json").write_text(json.dumps({"repos": [{"name": "acme-api"}, {"name": "acme-web"}]}))
    (root.path / "acme-api").mkdir()
    (root.path / "acme-web").mkdir()
    (root.path / "acme-api" / ".contracts.lock").write_text(json.dumps({"todos.openapi.yaml": want}))
    r = root.run("contract-check.sh")
    assert "ok   todos.openapi.yaml · acme-api" in r.stdout and "WARN todos.openapi.yaml · acme-web has not implemented" in r.stdout
    wt = root.path / "wt"
    wt.mkdir()
    (wt / ".contracts.lock").write_text(json.dumps({"todos.openapi.yaml": "old"}))
    r = root.run("contract-check.sh", "--repo", f"acme-web={wt}", check=False)
    assert r.returncode == 1 and "FAIL todos.openapi.yaml · acme-web implements an older version" in r.stdout
