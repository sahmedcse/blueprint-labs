"""Enforce small, reviewable commits. Called through scripts/commit-check.sh.

    commit-check.sh <repo-path> <base-ref>     check every commit in base..HEAD
    commit-check.sh --message <file>           check one message (commit-msg hook)

A commit fails when its first line isn't Conventional Commits, or when it changes more than
FAIL_LINES lines once lockfiles, vendored and generated files are excluded. More than WARN_LINES
prints a warning. Exit 0 ok, 1 a commit failed, 2 bad arguments.
"""
import fnmatch
import os
import re
import subprocess
import sys

WARN_LINES = int(os.environ.get("BLUEPRINT_COMMIT_WARN", "200"))
FAIL_LINES = int(os.environ.get("BLUEPRINT_COMMIT_FAIL", "400"))
SUBJECT_RE = re.compile(r"^(feat|fix|chore|docs|refactor|test|perf|build|ci|style|revert)(\([a-z0-9._/-]+\))?!?: \S")
ALLOWED_RE = re.compile(r"^(Merge |Revert \")")
EXEMPT = ["pnpm-lock.yaml", "package-lock.json", "yarn.lock", "go.sum", "uv.lock", "poetry.lock",
          "*.min.js", "*/vendor/*", "vendor/*", "*.gen.*", "*_gen.go", "*.sql.go", "*/components/ui/*",
          "src/types/api.ts", ".terraform.lock.hcl", "*/.terraform.lock.hcl"]


def exempt(path):
    name = os.path.basename(path)
    return any(fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(name, pat) for pat in EXEMPT)


def check_subject(subject):
    if ALLOWED_RE.match(subject) or SUBJECT_RE.match(subject):
        return None
    return f"not Conventional Commits: {subject!r} (expected e.g. 'feat(cart): add totals')"


def check_range(repo, base):
    revs = subprocess.run(["git", "-C", repo, "rev-list", "--reverse", "--no-merges", f"{base}..HEAD"],
                          capture_output=True, text=True)
    if revs.returncode:
        print(f"commit-check: bad range {base}..HEAD: {revs.stderr.strip()}", file=sys.stderr)
        return 2
    failed = 0
    for sha in revs.stdout.split():
        subject = subprocess.run(["git", "-C", repo, "log", "-1", "--format=%s", sha],
                                 capture_output=True, text=True).stdout.strip()
        stat = subprocess.run(["git", "-C", repo, "show", "--numstat", "--format=", sha],
                              capture_output=True, text=True).stdout
        size = 0
        for line in stat.splitlines():
            parts = line.split("\t")
            if len(parts) == 3 and parts[0] != "-" and not exempt(parts[2]):
                size += int(parts[0]) + int(parts[1])
        problems = [p for p in [check_subject(subject)] if p]
        if size > FAIL_LINES:
            problems.append(f"{size} changed lines (limit {FAIL_LINES}); split it into smaller commits")
        tag = "FAIL" if problems else ("WARN" if size > WARN_LINES else "ok  ")
        print(f"{tag} {sha[:8]} {size:5d} {subject}")
        for p in problems:
            print(f"     - {p}")
        failed += bool(problems)
    return 1 if failed else 0


def main(argv):
    if len(argv) == 2 and argv[0] == "--message":
        first = open(argv[1], encoding="utf-8").readline().strip()
        problem = check_subject(first)
        if problem:
            print(f"commit-check: {problem}", file=sys.stderr)
            return 1
        return 0
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    return check_range(*argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
