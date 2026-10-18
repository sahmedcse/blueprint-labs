import json

REQ = "REQ-0001-todo"
HEAD = "# Learnings: ux-designer\n\nintro\n\n"


def setup(root, proposals):
    (root.path / "principles" / "learnings").mkdir(parents=True)
    (root.path / "principles" / "learnings" / "ux-designer.md").write_text(
        HEAD + "- Old lesson.\n  source: REQ-0000\n")
    (root.path / "principles" / "learnings" / "architect.md").write_text("# Learnings: architect\n\n")
    run = root.path / ".runs" / REQ
    run.mkdir(parents=True)
    (run / "retro.json").write_text(json.dumps({"req": REQ, "proposals": proposals}))


def p(id, file, action, text=None, replaces=None):
    return {"id": id, "file": f"principles/learnings/{file}.md", "action": action, "text": text,
            "replaces": replaces, "source": f"{REQ} evidence"}


def test_apply_add_replace_remove_with_commit_per_file(root):
    setup(root, [p("L1", "ux-designer", "replace", "Show the empty state large.", "Old lesson."),
                 p("L2", "ux-designer", "add", "Use real copy."),
                 p("L3", "architect", "add", "Draw only touched containers."),
                 p("L4", "architect", "add", "Rejected one.")])
    root.run("learn.sh", "apply", REQ, "--skip", "L4")
    ux = (root.path / "principles" / "learnings" / "ux-designer.md").read_text()
    assert "Old lesson" not in ux and ux.count("source:") == 2
    assert "- Show the empty state large.\n  source: REQ-0001-todo evidence\n- Use real copy." in ux
    arch = (root.path / "principles" / "learnings" / "architect.md").read_text()
    assert "Rejected one" not in arch and "Draw only touched containers." in arch
    subjects = sorted(root.subjects())
    assert subjects == ["learn(architect): Draw only touched containers",
                        "learn(ux-designer): Show the empty state large (+1 more)"]


def test_remove(root):
    setup(root, [p("L1", "ux-designer", "remove", replaces="Old lesson.")])
    root.run("learn.sh", "apply", REQ)
    assert (root.path / "principles" / "learnings" / "ux-designer.md").read_text() == HEAD


def test_invalid_proposal_writes_nothing(root):
    setup(root, [p("L1", "architect", "add", "fine"), p("L2", "ux-designer", "replace", "x", "missing")])
    r = root.run("learn.sh", "apply", REQ, check=False)
    assert r.returncode == 1 and "no bullet matching" in r.stderr
    assert "fine" not in (root.path / "principles" / "learnings" / "architect.md").read_text()


def test_refuses_files_outside_principles(root):
    setup(root, [{"id": "L1", "file": "scripts/gate.sh", "action": "add", "text": "x", "source": "s"}])
    assert root.run("learn.sh", "apply", REQ, check=False).returncode == 1
