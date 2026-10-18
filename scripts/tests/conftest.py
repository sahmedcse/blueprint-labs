import json
import os
import shutil
import subprocess

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Root:
    """A throwaway control repo with this repo's scripts copied in."""

    def __init__(self, path):
        self.path = path

    def run(self, script, *args, check=True):
        r = subprocess.run([str(self.path / "scripts" / script), *args], capture_output=True, text=True,
                           env={**os.environ, "BPL_NO_NOTIFY": "1"})
        if check:
            assert r.returncode == 0, r.stderr + r.stdout
        return r

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.path), *args], capture_output=True, text=True).stdout

    def subjects(self):
        return self.git("log", "--format=%s").splitlines()


@pytest.fixture
def root(tmp_path):
    shutil.copytree(os.path.join(REPO, "scripts"), tmp_path / "scripts",
                    ignore=shutil.ignore_patterns("tests", "__pycache__"))
    (tmp_path / "repos.json").write_text(json.dumps({"repos": [{"name": "acme-api"}, {"name": "acme-web"}]}))
    subprocess.run(["git", "init", "-q", "-b", "main", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.email", "t@e.com"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "t"], check=True)
    return Root(tmp_path)
