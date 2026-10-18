"""The product-repo registry (repos.json) and per-ticket run state.

repos.json:
  { "schema": "blueprint.repos.v1", "project": "acme", "github_owner": "you",
    "repos": [ { "name": "acme-api", "kind": "go", "path": "acme-api",
                 "remote": "git@github.com:you/acme-api.git" } ] }

kind is one of web, go, python, terraform. path is relative to the control repo.
"""
import json
import os
import subprocess

KINDS = ("web", "go", "python", "terraform")


def load(root):
    try:
        with open(os.path.join(root, "repos.json"), encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"repos": []}


def get(root, name):
    for r in load(root).get("repos", []):
        if r["name"] == name:
            return {**r, "abspath": os.path.join(root, r.get("path") or r["name"])}
    raise KeyError(name)


def git(path, *args, check=True):
    r = subprocess.run(["git", "-C", path, *args], capture_output=True, text=True)
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(args)} in {path}: {r.stderr.strip()}")
    return r


def base_ref(path):
    """origin/main when the repo has a remote main, else local main."""
    if git(path, "rev-parse", "--verify", "-q", "refs/remotes/origin/main", check=False).returncode == 0:
        return "origin/main"
    return "main"


def ticket_dir(root, req, tid):
    return os.path.join(root, ".runs", req, "tickets", tid)


def load_state(root, req, tid):
    try:
        with open(os.path.join(ticket_dir(root, req, tid), "state.json"), encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def save_state(root, req, tid, state):
    d = ticket_dir(root, req, tid)
    os.makedirs(d, exist_ok=True)
    tmp = os.path.join(d, ".state.json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, os.path.join(d, "state.json"))
