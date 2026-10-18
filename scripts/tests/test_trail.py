import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import trail  # noqa: E402


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=True).stdout


def init(root):
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "t@example.com")
    git(root, "config", "user.name", "t")


def test_journal_appends_with_header(tmp_path):
    trail.journal(str(tmp_path), "review", "REQ-0001 design/a", "approved\n rev x")
    trail.journal(str(tmp_path), "ticket", "T-0001", "ready → in_progress", link="PR #3")
    text = (tmp_path / "decisions" / "journal.md").read_text()
    assert text.startswith("# Journal")
    lines = [l for l in text.splitlines() if l.startswith("- ")]
    assert len(lines) == 2
    assert "**review** REQ-0001 design/a — approved rev x" in lines[0]
    assert lines[1].endswith("(PR #3)")


def test_commit_only_named_paths(tmp_path):
    init(tmp_path)
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("b")
    assert trail.commit(str(tmp_path), ["a.txt"], "chore: add a")
    log = git(tmp_path, "log", "--format=%B")
    assert "chore: add a" in log and "Co-Authored-By" in log
    assert "b.txt" in git(tmp_path, "status", "--porcelain")
    assert trail.commit(str(tmp_path), ["a.txt"], "chore: nothing") is False


def test_commit_noop_outside_git(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    assert trail.commit(str(tmp_path), ["a.txt"], "x") is False
