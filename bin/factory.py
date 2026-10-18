"""Project lifecycle for blueprint-labs. Called through the bin/ wrappers.

    bin/new-project <name> [--dir ~/Personal] [--owner GH_OWNER] [--web] [--api go|python] [--infra] [--github]
        A new control repo at <dir>/<name>, copied from this template's HEAD, plus the product
        repos asked for: <name>-web, <name>-api and <name>-infra.
    bin/add-repo <name> --kind web|go|python|terraform [--owner GH_OWNER] [--github]
        (run inside a control repo) scaffold a product repo from skeletons/<kind> and register it.
    bin/update-factory
        Pull the template's latest factory files (scripts, agents, loops, review, principles) into
        this project, with one commit per area. Learnings are merged, never overwritten.
    bin/sync-learnings
        Offer this project's approved learnings back to the template, on a branch in the template
        repo (and as a PR when it has a GitHub remote).

`--github` creates private GitHub repos with `gh` and pushes. It's off by default because it
publishes.
"""
import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "scripts", "lib"))
import trail  # noqa: E402

# What a project takes from the template. requests/, tickets/, decisions/ and repos.json are its own.
FACTORY_AREAS = [(".claude", "agents, loops, commands, hooks and settings"), ("scripts", "scripts"),
                 ("review", "review system"), ("conventions", "conventions"), ("skeletons", "skeletons"),
                 ("bin", "project tools"), ("principles/PRINCIPLES.md", "principles"),
                 ("principles/DEVELOPER.md", "developer rules")]
TEXT_EXT = {".md", ".json", ".yaml", ".yml", ".toml", ".go", ".mod", ".py", ".ts", ".tsx", ".js", ".mjs",
            ".css", ".html", ".tf", ".hcl", ".example", ".sql", ".txt", ".cfg", ".ini", ".lock", ".sh", ".env", ""}


def die(msg, code=1):
    print(f"factory: {msg}", file=sys.stderr)
    sys.exit(code)


def run(cmd, cwd=None, check=True):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and r.returncode:
        die(f"{' '.join(cmd)} failed: {r.stderr.strip() or r.stdout.strip()}")
    return r


def git_commit(path, msg, paths=("-A",)):
    run(["git", "-C", path, "add", *paths])
    if run(["git", "-C", path, "diff", "--cached", "--quiet"], check=False).returncode:
        run(["git", "-C", path, "commit", "-q", "-m", msg + trail.TRAILER])
        return True
    return False


def export_head(src, dst):
    """Copy a repo's committed HEAD (no untracked or ignored files) into dst."""
    os.makedirs(dst, exist_ok=True)
    archive = subprocess.Popen(["git", "-C", src, "archive", "HEAD"], stdout=subprocess.PIPE)
    subprocess.run(["tar", "-x", "-C", dst], stdin=archive.stdout, check=True)
    if archive.wait():
        die(f"git archive failed in {src}")
    return run(["git", "-C", src, "rev-parse", "--short", "HEAD"]).stdout.strip()


# ---- new-project -------------------------------------------------------------------------------

def new_project(a):
    if not re.match(r"^[a-z][a-z0-9-]{1,30}$", a.name):
        die("project name: lowercase letters, digits and dashes", 2)
    target = os.path.join(os.path.expanduser(a.dir), a.name)
    if os.path.exists(target):
        die(f"{target} already exists")
    sha = export_head(HERE, target)
    for d in ("requests", "tickets"):
        for f in os.listdir(os.path.join(target, d)):
            if f != ".gitkeep":
                os.remove(os.path.join(target, d, f))
    json.dump({"schema": "blueprint.repos.v1", "project": a.name, "github_owner": a.owner, "repos": []},
              open(os.path.join(target, "repos.json"), "w"), indent=2)
    os.makedirs(os.path.join(target, ".blueprint"), exist_ok=True)
    json.dump({"template": HERE, "template_commit": sha, "created": trail.now()},
              open(os.path.join(target, ".blueprint", "factory.json"), "w"), indent=2)
    with open(os.path.join(target, "README.md"), "w") as f:
        f.write(f"# {a.name}\n\nControl repo for {a.name}, made from blueprint-labs ({sha}). Start work with\n"
                f'`/blueprint "<request>"` in Claude Code. See CLAUDE.md.\n')
    run(["git", "init", "-q", "-b", "main", target])
    git_commit(target, f"chore: start {a.name} from blueprint-labs {sha}")
    print(f"control repo  {target}")
    wanted = ([("web", f"{a.name}-web")] if a.web else []) + ([(a.api, f"{a.name}-api")] if a.api else []) + \
             ([("terraform", f"{a.name}-infra")] if a.infra else [])
    for kind, name in wanted:
        cmd = [os.path.join(target, "bin", "add-repo"), name, "--kind", kind] + \
              (["--owner", a.owner] if a.owner else []) + (["--github"] if a.github else [])
        r = subprocess.run(cmd, cwd=target)
        if r.returncode:
            die(f"add-repo {name} failed")
    print(f"\nnext: cd {target} && claude, then /blueprint \"<what you want>\"")


# ---- add-repo ----------------------------------------------------------------------------------

def substitute(root, mapping):
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        for name in filenames + dirnames:
            p = os.path.join(dirpath, name)
            if os.path.isfile(p) and not os.path.islink(p) and os.path.splitext(name)[1] in TEXT_EXT:
                try:
                    text = open(p, encoding="utf-8").read()
                except UnicodeDecodeError:
                    continue
                new = text
                for k, v in mapping.items():
                    new = new.replace(k, v)
                if new != text:
                    open(p, "w", encoding="utf-8").write(new)
            renamed = name
            for k, v in mapping.items():
                renamed = renamed.replace(k, v)
            if renamed != name:
                os.rename(p, os.path.join(dirpath, renamed))


def add_repo(a):
    root = HERE
    if not os.path.exists(os.path.join(root, ".blueprint", "factory.json")):
        die("run add-repo inside a project made by bin/new-project, not in the template itself")
    if not re.match(r"^[a-z][a-z0-9-]{1,40}$", a.name):
        die("repo name: lowercase letters, digits and dashes", 2)
    src = os.path.join(root, "skeletons", a.kind)
    if not os.path.isdir(src):
        die(f"no skeleton for kind {a.kind!r} at skeletons/{a.kind}")
    registry_path = os.path.join(root, "repos.json")
    registry = json.load(open(registry_path))
    if any(r["name"] == a.name for r in registry["repos"]):
        die(f"{a.name} is already registered")
    dst = os.path.join(root, a.name)
    if os.path.exists(dst):
        die(f"{dst} already exists")
    owner = a.owner or registry.get("github_owner") or "your-github-user"
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("node_modules", ".next", ".venv", ".terraform",
                                                            "__pycache__", ".pytest_cache", ".mypy_cache"))
    substitute(dst, {"__NAME__": a.name, "__PKG__": a.name.replace("-", "_"), "__OWNER__": owner})
    run(["git", "init", "-q", "-b", "main", dst])
    if os.path.isdir(os.path.join(dst, ".githooks")):
        run(["git", "-C", dst, "config", "core.hooksPath", ".githooks"])
    git_commit(dst, f"chore: scaffold {a.name} from the blueprint-labs {a.kind} skeleton")
    remote = None
    if a.github:
        r = run(["gh", "repo", "create", f"{owner}/{a.name}", "--private", "--source", dst, "--push"], check=False)
        if r.returncode:
            print(f"warning: gh repo create failed: {r.stderr.strip()}. The repo stays local.", file=sys.stderr)
        else:
            remote = f"git@github.com:{owner}/{a.name}.git"
    registry["repos"].append({"name": a.name, "kind": a.kind, "path": a.name, "remote": remote})
    json.dump(registry, open(registry_path, "w"), indent=2)
    open(registry_path, "a").write("\n")
    gi = os.path.join(root, ".gitignore")
    with open(gi, "a") as f:
        f.write(f"/{a.name}/\n")
    j = trail.journal(root, "repo", a.name, f"added ({a.kind})" + (f", remote {remote}" if remote else ", local only"))
    trail.commit(root, [registry_path, gi, j], f"chore(repos): add {a.name} ({a.kind})")
    print(f"product repo  {dst}  ({a.kind}{', ' + remote if remote else ', local only'})")


# ---- learnings: update-factory and sync-learnings ----------------------------------------------

def bullets(text):
    """Learning bullets: '- lesson' plus its indented 'source:' line, keyed by the lesson text."""
    out, lines, i = {}, text.splitlines(keepends=True), 0
    while i < len(lines):
        if lines[i].startswith("- "):
            j = i + 1
            while j < len(lines) and lines[j].startswith("  "):
                j += 1
            out[lines[i][2:].strip()] = "".join(lines[i:j])
            i = j
        else:
            i += 1
    return out


def merge_learnings(ours_dir, theirs_dir, strip=None):
    """Append bullets from theirs that ours lacks. Returns {file: added_count}."""
    added = {}
    if not os.path.isdir(theirs_dir):
        return added
    os.makedirs(ours_dir, exist_ok=True)
    for name in sorted(os.listdir(theirs_dir)):
        if not name.endswith(".md"):
            continue
        theirs = open(os.path.join(theirs_dir, name), encoding="utf-8").read()
        ours_path = os.path.join(ours_dir, name)
        ours = open(ours_path, encoding="utf-8").read() if os.path.exists(ours_path) else theirs.split("\n- ", 1)[0]
        have = bullets(ours)
        new = [b for k, b in bullets(theirs).items() if k not in have]
        if strip:
            new = [re.sub(rf"\b{re.escape(strip)}\b", "<project>", b) for b in new]
        if new:
            open(ours_path, "w", encoding="utf-8").write(ours.rstrip("\n") + "\n" + "".join(new))
            added[name] = len(new)
    return added


def factory_info():
    p = os.path.join(HERE, ".blueprint", "factory.json")
    if not os.path.exists(p):
        die("this isn't a project made by bin/new-project (no .blueprint/factory.json)")
    info = json.load(open(p))
    if not os.path.isdir(os.path.join(info["template"], ".git")):
        die(f"template repo not found at {info['template']}")
    return p, info


def update_factory(a):
    info_path, info = factory_info()
    if run(["git", "-C", HERE, "status", "--porcelain"]).stdout.strip():
        die("commit or stash your changes first")
    with tempfile.TemporaryDirectory() as tmp:
        sha = export_head(info["template"], tmp)
        for area, label in FACTORY_AREAS:
            src, dst = os.path.join(tmp, area), os.path.join(HERE, area)
            if os.path.isdir(src):
                shutil.rmtree(dst, ignore_errors=True)
                shutil.copytree(src, dst)
            elif os.path.isfile(src):
                shutil.copyfile(src, dst)
            if git_commit(HERE, f"chore(factory): update {label} from blueprint-labs {sha}", [area]):
                print(f"updated {area}")
        added = merge_learnings(os.path.join(HERE, "principles", "learnings"), os.path.join(tmp, "principles", "learnings"))
        if git_commit(HERE, f"chore(factory): merge template learnings from blueprint-labs {sha}", ["principles/learnings"]):
            print(f"merged learnings: {added}")
    info["template_commit"], info["updated"] = sha, trail.now()
    json.dump(info, open(info_path, "w"), indent=2)
    git_commit(HERE, f"chore(factory): record blueprint-labs {sha}", [".blueprint/factory.json"])


def sync_learnings(a):
    _, info = factory_info()
    tpl = info["template"]
    project = json.load(open(os.path.join(HERE, "repos.json"))).get("project") or os.path.basename(HERE)
    branch = f"learnings/{project}-{datetime.date.today():%Y%m%d}"
    wt = os.path.join(tempfile.mkdtemp(), "tpl")
    base = "main" if run(["git", "-C", tpl, "rev-parse", "--verify", "-q", "main"], check=False).returncode == 0 else "HEAD"
    run(["git", "-C", tpl, "worktree", "add", "-q", "-b", branch, wt, base])
    try:
        added = merge_learnings(os.path.join(wt, "principles", "learnings"), os.path.join(HERE, "principles", "learnings"),
                                strip=project)
        if not added:
            print("nothing new to share")
            run(["git", "-C", tpl, "worktree", "remove", wt])
            run(["git", "-C", tpl, "branch", "-D", branch])
            return
        for name, n in added.items():
            git_commit(wt, f"learn({name[:-3]}): {n} lesson(s) from {project}", [f"principles/learnings/{name}"])
        print(f"branch {branch} in {tpl}: {added}")
        if run(["git", "-C", tpl, "remote"], check=False).stdout.strip():
            run(["git", "-C", wt, "push", "-u", "origin", branch])
            pr = run(["gh", "pr", "create", "--head", branch, "--title", f"Learnings from {project}",
                      "--body", "Approved retro learnings from a project, with project names stripped.\n\n"
                                "🤖 Generated with [Claude Code](https://claude.com/claude-code)"], cwd=wt, check=False)
            print(pr.stdout.strip() or pr.stderr.strip())
        else:
            print(f"review it with: git -C {tpl} log main..{branch}, then merge it there")
    finally:
        if os.path.exists(wt):
            run(["git", "-C", tpl, "worktree", "remove", "--force", wt], check=False)


def main():
    prog = os.environ.get("BPL_PROG", "factory")
    ap = argparse.ArgumentParser(prog=prog)
    if prog == "new-project":
        ap.add_argument("name"); ap.add_argument("--dir", default="~/Personal"); ap.add_argument("--owner")
        ap.add_argument("--web", action="store_true"); ap.add_argument("--api", choices=["go", "python"])
        ap.add_argument("--infra", action="store_true"); ap.add_argument("--github", action="store_true")
        new_project(ap.parse_args())
    elif prog == "add-repo":
        ap.add_argument("name"); ap.add_argument("--kind", required=True, choices=["web", "go", "python", "terraform"])
        ap.add_argument("--owner"); ap.add_argument("--github", action="store_true")
        add_repo(ap.parse_args())
    elif prog == "update-factory":
        update_factory(ap.parse_args())
    elif prog == "sync-learnings":
        sync_learnings(ap.parse_args())
    else:
        die("run through bin/new-project, bin/add-repo, bin/update-factory or bin/sync-learnings", 2)


if __name__ == "__main__":
    main()
