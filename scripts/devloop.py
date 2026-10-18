"""The development loop's mechanics, one subcommand per script wrapper:

    worktree.sh create  <REQ> <T>      a worktree + branch for one ticket, from the repo's main
    worktree.sh cleanup <REQ> <T>      remove it (refuses when dirty)
    worktree.sh doctor                 prune stale worktrees in every product repo
    iter.sh next <REQ> <T>             advance the ticket's iteration (exit 1 when the budget is spent)
    iter.sh undo <REQ> <T>             roll back one iteration after an infra error

State lives in .runs/<REQ>/tickets/<T>/state.json. Product repos' main checkouts are never
modified. The only operations on them are `git fetch` and `git worktree add/remove`.
"""
import argparse
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts", "lib"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import repos  # noqa: E402
import ticket  # noqa: E402

MAX_ITERATIONS = int(os.environ.get("BLUEPRINT_MAX_ITERATIONS", "3"))
PREFIX = {"bug": "fix", "chore": "chore", "spike": "chore", "infra": "infra"}


def die(msg, code=1):
    print(f"{os.environ.get('BPL_PROG', 'devloop')}: {msg}", file=sys.stderr)
    sys.exit(code)


def load_ticket(tid):
    t = ticket.load_all().get(tid)
    if not t:
        die(f"no ticket {tid}", 2)
    return t


def worktree_path(req, tid):
    return os.path.join(ROOT, ".worktrees", req, tid)


def cmd_create(a):
    t = load_ticket(a.ticket)
    try:
        repo = repos.get(ROOT, t["repo"])
    except KeyError:
        die(f"{a.ticket}: repo {t['repo']!r} is not in repos.json")
    path = repo["abspath"]
    if not os.path.isdir(os.path.join(path, ".git")):
        die(f"{path} is not a git repository")
    branch = f"{PREFIX.get(t['type'], 'feature')}/{a.ticket.lower()}-{ticket.slugify(t['title'], 32)}"
    wt = worktree_path(a.req, a.ticket)
    if os.path.exists(wt):
        die(f"worktree already exists: {os.path.relpath(wt, ROOT)}")
    repos.git(path, "worktree", "prune")
    if repos.git(path, "remote", check=False).stdout.strip():
        r = repos.git(path, "fetch", "-q", "origin", "+refs/heads/main:refs/remotes/origin/main", check=False)
        if r.returncode:
            die(f"fetch failed in {t['repo']}: {r.stderr.strip()}", 2)
    if repos.git(path, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}", check=False).returncode == 0:
        die(f"{t['repo']} already has branch {branch}")
    base = repos.base_ref(path)
    os.makedirs(os.path.dirname(wt), exist_ok=True)
    repos.git(path, "worktree", "add", "-q", "-b", branch, wt, base)
    repos.save_state(ROOT, a.req, a.ticket, {
        "ticket": a.ticket, "repo": t["repo"], "kind": repo["kind"], "repo_path": path,
        "worktree": wt, "branch": branch, "base": base, "iteration": 0,
        "max_iterations": MAX_ITERATIONS, "gates": {}})
    print(branch)


def cmd_cleanup(a):
    s = repos.load_state(ROOT, a.req, a.ticket)
    if not s or not os.path.exists(s["worktree"]):
        print(f"nothing to clean for {a.ticket}")
        return
    r = repos.git(s["repo_path"], "worktree", "remove", s["worktree"], check=False)
    if r.returncode:
        die(f"KEPT {s['worktree']}: {r.stderr.strip()} (inspect it, then remove it by hand)")
    repos.git(s["repo_path"], "worktree", "prune")
    print(f"removed {os.path.relpath(s['worktree'], ROOT)}")


def cmd_doctor(a):
    for r in repos.load(ROOT).get("repos", []):
        path = os.path.join(ROOT, r.get("path") or r["name"])
        if not os.path.isdir(path):
            print(f"== {r['name']}: MISSING at {path}")
            continue
        repos.git(path, "worktree", "prune")
        print(f"== {r['name']}")
        print(repos.git(path, "worktree", "list").stdout.rstrip())
    if shutil.which("docker"):
        out = os.popen("docker ps --filter name=bplgate- --format '{{.Names}}' 2>/dev/null").read().strip()
        print("== orphaned gate databases\n" + (out or "(none)"))


def cmd_iter(a):
    s = repos.load_state(ROOT, a.req, a.ticket) or die(f"{a.ticket} has no worktree yet", 2)
    if a.action == "next":
        if s["iteration"] >= s["max_iterations"]:
            die(f"{a.ticket} used all {s['max_iterations']} iterations")
        s["iteration"] += 1
    else:
        s["iteration"] = max(0, s["iteration"] - 1)
    repos.save_state(ROOT, a.req, a.ticket, s)
    print(s["iteration"])


def main():
    ap = argparse.ArgumentParser(prog=os.environ.get("BPL_PROG", "devloop"))
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("create", "cleanup"):
        p = sub.add_parser(name); p.add_argument("req"); p.add_argument("ticket")
    sub.add_parser("doctor")
    it = sub.add_parser("iter"); it.add_argument("action", choices=["next", "undo"])
    it.add_argument("req"); it.add_argument("ticket")
    a = ap.parse_args()
    {"create": cmd_create, "cleanup": cmd_cleanup, "doctor": cmd_doctor, "iter": cmd_iter}[a.cmd](a)


if __name__ == "__main__":
    main()
