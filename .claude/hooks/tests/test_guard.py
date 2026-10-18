import json
import os
import subprocess
import sys

import pytest

HOOK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "guard_paths.py")


@pytest.fixture
def root(tmp_path):
    (tmp_path / "repos.json").write_text(json.dumps({"repos": [{"name": "acme-web", "path": "acme-web"}]}))
    (tmp_path / "acme-web").mkdir()
    return tmp_path


def run(root, tool, **inp):
    r = subprocess.run([sys.executable, HOOK], input=json.dumps({"tool_name": tool, "tool_input": inp}),
                       capture_output=True, text=True, env={**os.environ, "CLAUDE_PROJECT_DIR": str(root)})
    return r.returncode


@pytest.mark.parametrize("path", ["acme-web/src/a.ts", "tickets/T-0001-x.md", "decisions/journal.md",
                                  "requests/REQ-0001-x/status.json"])
def test_blocks_protected_files(root, path):
    assert run(root, "Edit", file_path=str(root / path)) == 2


@pytest.mark.parametrize("path", [".worktrees/REQ-0001-x/T-0001/src/a.ts", ".runs/REQ-0001-x/design.json",
                                  "requests/REQ-0001-x/request.md", "principles/learnings/master.md"])
def test_allows_work_paths(root, path):
    assert run(root, "Write", file_path=str(root / path)) == 0


@pytest.mark.parametrize("cmd", ["echo x > acme-web/a.ts", "echo x >> {root}/acme-web/a.ts", "rm -rf acme-web/src",
                                 "sed -i '' s/a/b/ acme-web/x", "git -C acme-web commit -m x",
                                 "cat a | tee acme-web/b"])
def test_blocks_bash_writes(root, cmd):
    assert run(root, "Bash", command=cmd.format(root=root)) == 2


@pytest.mark.parametrize("cmd", ["cat acme-web/CLAUDE.md", "git -C acme-web log --oneline", "ls 2>/dev/null",
                                 "echo x > .worktrees/REQ-1/T-1/acme-web/a.ts", "git -C .worktrees/R/T commit -m x",
                                 "git -C acme-web fetch -q origin"])
def test_allows_reads_and_worktree_writes(root, cmd):
    assert run(root, "Bash", command=cmd) == 0


@pytest.mark.parametrize("cmd", ["git -C .worktrees/R/T commit --amend -m x", "git commit -m x --no-verify",
                                 "git -C .worktrees/R/T push --force origin b", "git push -f origin main",
                                 "git -C .worktrees/R/T push --force-with-lease"])
def test_blocks_history_rewrites(root, cmd):
    assert run(root, "Bash", command=cmd) == 2


def test_allows_normal_push(root):
    assert run(root, "Bash", command="git -C .worktrees/R/T push -u origin feature/t-0001-x") == 0
