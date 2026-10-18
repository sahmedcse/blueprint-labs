import json

REQ = "REQ-0001-todo"


def new(root, title, *extra, check=True):
    return root.run("ticket.sh", "new", "--request", REQ, "--title", title, "--repo", "acme-api",
                    "--owner", "backend-developer", *extra, check=check)


def listed(root, *args):
    return {t["id"]: t for t in json.loads(root.run("ticket.sh", "list", "--json", *args).stdout)}


def test_new_assigns_ids_and_commits(root):
    assert new(root, "Create todos table").stdout.strip() == "T-0001"
    assert new(root, "Todo CRUD API", "--depends", "T-0001").stdout.strip() == "T-0002"
    t = listed(root)
    assert t["T-0002"]["depends_on"] == ["T-0001"] and t["T-0002"]["status"] == "backlog"
    assert (root.path / "tickets" / "T-0002-todo-crud-api.md").exists()
    assert root.subjects() == ["ticket(T-0002): create Todo CRUD API", "ticket(T-0001): create Create todos table"]
    assert "created (backlog): Todo CRUD API" in (root.path / "decisions" / "journal.md").read_text()


def test_title_with_colon_and_quotes_round_trips(root):
    new(root, 'Auth: "magic link" sign-in')
    assert listed(root)["T-0001"]["title"] == 'Auth: "magic link" sign-in'


def test_new_rejects_unknown_repo_and_dependency(root):
    r = root.run("ticket.sh", "new", "--request", REQ, "--title", "x", "--repo", "nope",
                 "--owner", "backend-developer", check=False)
    assert r.returncode == 1 and "not in repos.json" in r.stderr
    assert new(root, "y", "--depends", "T-0009", check=False).returncode == 1
    assert not (root.path / "tickets").exists() or not list((root.path / "tickets").glob("T-*.md"))


def test_list_filters(root):
    new(root, "a")
    new(root, "b", "--status", "ready")
    assert list(listed(root, "--status", "ready")) == ["T-0002"]
    assert "T-0001\tbacklog\tacme-api" in root.run("ticket.sh", "list").stdout


def test_validate_flags_cycles(root):
    new(root, "a")
    new(root, "b", "--depends", "T-0001")
    assert root.run("ticket.sh", "validate").returncode == 0
    p = next((root.path / "tickets").glob("T-0001-*.md"))
    p.write_text(p.read_text().replace("depends_on: []", "depends_on: [T-0002]"))
    r = root.run("ticket.sh", "validate", check=False)
    assert r.returncode == 1 and "cycle" in r.stdout
