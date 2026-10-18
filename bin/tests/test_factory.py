import json
import os
import shutil
import subprocess

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def sh(*cmd, cwd=None, check=True):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check:
        assert r.returncode == 0, r.stderr + r.stdout
    return r


def commit_all(path, msg):
    sh("git", "-C", str(path), "add", "-A")
    sh("git", "-C", str(path), "-c", "user.email=t@e", "-c", "user.name=t", "commit", "-qm", msg)


@pytest.fixture
def template(tmp_path):
    t = tmp_path / "blueprint-labs"
    shutil.copytree(REPO, t, ignore=shutil.ignore_patterns(".git", ".runs", ".worktrees", "tests", "__pycache__",
                                                          "skeletons", "node_modules"))
    sk = t / "skeletons" / "web"
    (sk / ".githooks").mkdir(parents=True)
    (sk / "package.json").write_text('{"name": "__NAME__"}\n')
    (sk / "README.md").write_text("# __NAME__ by __OWNER__\n")
    (sk / ".githooks" / "commit-msg").write_text("#!/bin/sh\nexit 0\n")
    sh("git", "init", "-q", "-b", "main", str(t))
    commit_all(t, "chore: template")
    return t


def subjects(path):
    return sh("git", "-C", str(path), "log", "--format=%s").stdout.splitlines()


def test_new_project_with_repo(template, tmp_path):
    out = sh(str(template / "bin" / "new-project"), "acme", "--dir", str(tmp_path), "--web", "--owner", "me").stdout
    proj = tmp_path / "acme"
    assert "control repo" in out and (proj / "CLAUDE.md").exists() and (proj / ".blueprint" / "factory.json").exists()
    web = proj / "acme-web"
    assert json.loads((web / "package.json").read_text())["name"] == "acme-web"
    assert (web / "README.md").read_text() == "# acme-web by me\n"
    assert sh("git", "-C", str(web), "config", "core.hooksPath").stdout.strip() == ".githooks"
    reg = json.loads((proj / "repos.json").read_text())
    assert reg["project"] == "acme" and reg["repos"][0] == {"name": "acme-web", "kind": "web", "path": "acme-web", "remote": None}
    assert "/acme-web/" in (proj / ".gitignore").read_text()
    assert subjects(proj) == ["chore(repos): add acme-web (web)", f"chore: start acme from blueprint-labs {subjects_sha(template)}"]
    assert sh("git", "-C", str(proj), "status", "--porcelain").stdout == ""


def subjects_sha(template):
    return sh("git", "-C", str(template), "rev-parse", "--short", "HEAD").stdout.strip()


def test_add_repo_refuses_in_template(template):
    r = sh(str(template / "bin" / "add-repo"), "x-web", "--kind", "web", check=False)
    assert r.returncode == 1 and "not in the template itself" in r.stderr


def test_update_and_sync_learnings(template, tmp_path):
    sh(str(template / "bin" / "new-project"), "acme", "--dir", str(tmp_path))
    proj = tmp_path / "acme"
    # The template improves: a principle changes and a lesson lands.
    (template / "principles" / "PRINCIPLES.md").write_text((template / "principles" / "PRINCIPLES.md").read_text() + "\n12. New rule.\n")
    lf = template / "principles" / "learnings" / "architect.md"
    lf.write_text(lf.read_text() + "- Template lesson.\n  source: elsewhere\n")
    commit_all(template, "feat: improve")
    # The project learned something of its own meanwhile.
    pl = proj / "principles" / "learnings" / "ux-designer.md"
    pl.write_text(pl.read_text() + "- In acme, show empty states large.\n  source: REQ-0001 notes\n")
    commit_all(proj, "learn(ux-designer): empty states")

    sh(str(proj / "bin" / "update-factory"))
    assert "12. New rule." in (proj / "principles" / "PRINCIPLES.md").read_text()
    assert "Template lesson." in (proj / "principles" / "learnings" / "architect.md").read_text()
    assert "show empty states large" in pl.read_text()
    s = subjects(proj)
    assert any(x.startswith("chore(factory): update principles") for x in s)
    assert any(x.startswith("chore(factory): merge template learnings") for x in s)

    out = sh(str(proj / "bin" / "sync-learnings")).stdout
    branch = [l for l in out.splitlines() if l.startswith("branch ")][0].split()[1]
    shared = sh("git", "-C", str(template), "show", f"{branch}:principles/learnings/ux-designer.md").stdout
    assert "In <project>, show empty states large." in shared
    assert "Template lesson" not in sh("git", "-C", str(template), "diff", f"main..{branch}").stdout
