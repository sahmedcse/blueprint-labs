import subprocess


def commit(root, path, lines, msg):
    (root.path / path).write_text("".join(f"line {i}\n" for i in range(lines)))
    subprocess.run(["git", "-C", str(root.path), "add", path], check=True)
    subprocess.run(["git", "-C", str(root.path), "commit", "-qm", msg], check=True)


def test_range_flags_bad_messages_and_oversized_commits(root):
    commit(root, "base.txt", 1, "chore: base")
    base = root.git("rev-parse", "HEAD").strip()
    commit(root, "a.txt", 10, "feat(cart): add totals")
    commit(root, "b.txt", 250, "feat: medium change")
    commit(root, "pnpm-lock.yaml", 5000, "chore(deps): lockfile")
    commit(root, "c.txt", 3, "updated stuff")
    commit(root, "d.txt", 450, "feat: too big")
    r = root.run("commit-check.sh", str(root.path), base, check=False)
    assert r.returncode == 1
    lines = r.stdout.splitlines()
    assert lines[0].startswith("ok ") and "WARN" in lines[1] and lines[2].startswith("ok ")
    assert "FAIL" in lines[3] and "not Conventional Commits" in r.stdout
    assert "450 changed lines (limit 400)" in r.stdout


def test_message_mode(root, tmp_path):
    good, bad = tmp_path / "good", tmp_path / "bad"
    good.write_text("fix(api)!: drop v0 route\n\nbody")
    bad.write_text("wip\n")
    assert root.run("commit-check.sh", "--message", str(good)).returncode == 0
    assert root.run("commit-check.sh", "--message", str(bad), check=False).returncode == 1
