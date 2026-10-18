"""The verification gate for one ticket. This script, not any model, decides whether a change passes.

    gate.sh <REQ> <T> <iteration>     run the gate in the ticket's worktree
    verify-gate.sh <REQ> <T>          exit 1 if the tree changed since its last passing gate

Exit codes (gate): 0 pass, 1 fail (uses up the iteration), 2 infra error (Docker down and the
like; roll the iteration back with `iter.sh undo` and retry once).

Steps: universal checks (no new suppressions, no gutted tests, nothing uncommitted, commit-check),
then for go/python an ephemeral Postgres (DATABASE_URL), `make migrate` when the repo has that
target, then `make gate`. Writes .runs/<REQ>/tickets/<T>/gate.iter<N>.{json,log}.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts", "lib"))
import repos  # noqa: E402

SUPPRESSIONS = re.compile(r"t\.Skip\(|\bit\.skip\(|describe\.skip\(|test\.skip\(|eslint-disable|@ts-ignore|"
                          r"@ts-expect-error|//\s*nolint|--no-verify|pytest\.mark\.skip|# type: ignore|# noqa|"
                          r"tflint-ignore")
TEST_FILES = ["*_test.go", "*.test.ts", "*.test.tsx", "*.spec.ts", "*.spec.tsx", "test_*.py", "*_test.py",
              "tests/*", "e2e/*"]


class Infra(Exception):
    pass


def sh(cmd, cwd, log, env=None, timeout=1800):
    log.write(f"$ {' '.join(cmd)}\n")
    log.flush()
    r = subprocess.run(cmd, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, env=env, timeout=timeout)
    return r.returncode


def tree_sha(wt, base):
    parts = [repos.git(wt, "rev-parse", "HEAD").stdout, repos.git(wt, "diff", base).stdout,
             repos.git(wt, "status", "--porcelain").stdout]
    return hashlib.sha256("\0".join(parts).encode()).hexdigest()


def check_suppressions(wt, base, log):
    diff = repos.git(wt, "diff", base, "--unified=0").stdout
    added = [l for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
    # The one allowed skip: an integration test skipping when DATABASE_URL is unset, on that line.
    bad = [l for l in added if SUPPRESSIONS.search(l) and "DATABASE_URL" not in l]
    if bad:
        log.write("NEW SUPPRESSIONS: fix the code, not the check:\n" + "\n".join(bad) + "\n")
    return 1 if bad else 0


def check_test_gutting(wt, base, log):
    stat = repos.git(wt, "diff", base, "--numstat", "--", *TEST_FILES).stdout
    ins = sum(int(p[0]) for p in (l.split("\t") for l in stat.splitlines()) if p[0] != "-")
    dels = sum(int(p[1]) for p in (l.split("\t") for l in stat.splitlines()) if p[1] != "-")
    if dels > ins:
        log.write(f"TEST FILES NET-DELETED {dels - ins} LINES (+{ins}/-{dels}). Tests were removed, not added.\n")
        return 1
    return 0


def check_committed(wt, log):
    dirty = repos.git(wt, "status", "--porcelain").stdout.strip()
    if dirty:
        log.write("UNCOMMITTED CHANGES. Commit your work in small commits:\n" + dirty + "\n")
        return 1
    return 0


def start_db(name, log):
    if not shutil.which("docker"):
        raise Infra("docker is not installed")
    r = subprocess.run(["docker", "run", "-d", "--rm", "--name", name, "-P", "-e", "POSTGRES_PASSWORD=gate",
                        "-e", "POSTGRES_USER=gate", "-e", "POSTGRES_DB=gate", "postgres:16"],
                       capture_output=True, text=True)
    if r.returncode:
        raise Infra(f"could not start postgres: {r.stderr.strip()}")
    port = subprocess.run(["docker", "port", name, "5432/tcp"], capture_output=True, text=True).stdout
    m = re.search(r":(\d+)\s*$", port.splitlines()[0] if port else "")
    if not m:
        raise Infra(f"no port for {name}: {port!r}")
    for _ in range(60):
        ok = subprocess.run(["docker", "exec", name, "pg_isready", "-U", "gate", "-d", "gate"], capture_output=True)
        if ok.returncode == 0:
            time.sleep(1)  # the server restarts once after init; give it a beat
            log.write(f"ephemeral postgres {name} on port {m.group(1)}\n")
            return f"postgresql://gate:gate@127.0.0.1:{m.group(1)}/gate"
        time.sleep(1)
    raise Infra("postgres did not become ready in 60s")


def has_target(wt, target):
    try:
        return re.search(rf"^{target}:", open(os.path.join(wt, "Makefile")).read(), re.M) is not None
    except FileNotFoundError:
        return False


def cmd_gate(req, tid, iteration):
    state = repos.load_state(ROOT, req, tid)
    if not state:
        print(f"gate.sh: {tid} has no worktree", file=sys.stderr)
        return 2
    wt, base = state["worktree"], state["base"]
    out = repos.ticket_dir(ROOT, req, tid)
    log_path, json_path = os.path.join(out, f"gate.iter{iteration}.log"), os.path.join(out, f"gate.iter{iteration}.json")
    steps, status, db = [], "pass", None
    with open(log_path, "w") as log:
        def step(name, fn):
            nonlocal status
            if status != "pass":
                steps.append({"name": name, "result": "skipped"})
                return
            log.write(f"\n::: {name}\n")
            t0 = time.time()
            try:
                rc = fn()
            except Infra as e:
                log.write(f"INFRA ERROR: {e}\n")
                status = "infra"
                steps.append({"name": name, "result": "infra"})
                return
            steps.append({"name": name, "result": "pass" if rc == 0 else "fail", "seconds": round(time.time() - t0)})
            if rc:
                status = "fail"

        env = dict(os.environ)
        step("no-new-suppressions", lambda: check_suppressions(wt, base, log))
        step("no-test-gutting", lambda: check_test_gutting(wt, base, log))
        step("all-committed", lambda: check_committed(wt, log))
        step("commit-check", lambda: sh([os.path.join(ROOT, "scripts", "commit-check.sh"), wt, base], wt, log))
        try:
            if state["kind"] in ("go", "python") and status == "pass":
                db = f"bplgate-{tid.lower()}-{iteration}-{os.getpid()}"

                def db_step():
                    env["DATABASE_URL"] = start_db(db, log)
                    return 0
                step("ephemeral-postgres", db_step)
                if has_target(wt, "migrate"):
                    step("make migrate", lambda: sh(["make", "migrate"], wt, log, env))
            if state["kind"] == "web" and os.path.exists(os.path.join(wt, "pnpm-lock.yaml")):
                step("pnpm install", lambda: sh(["pnpm", "install", "--frozen-lockfile", "--prefer-offline"], wt, log, env))
            step("make gate", lambda: sh(["make", "gate"], wt, log, env))
        finally:
            if db:
                subprocess.run(["docker", "rm", "-f", db], capture_output=True)
    sha = tree_sha(wt, base)
    result = {"schema": "blueprint.gate.v1", "ticket": tid, "iteration": iteration, "status": status,
              "first_failed_step": next((s["name"] for s in steps if s["result"] in ("fail", "infra")), None),
              "tree_sha": sha, "log": os.path.relpath(log_path, ROOT), "steps": steps}
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2)
    state["gates"][str(iteration)] = {"status": status, "tree_sha": sha}
    repos.save_state(ROOT, req, tid, state)
    print(f"GATE {status.upper()} {tid} iter {iteration}" + (f" at {result['first_failed_step']}" if status != "pass" else ""))
    return {"pass": 0, "fail": 1, "infra": 2}[status]


def cmd_verify(req, tid):
    state = repos.load_state(ROOT, req, tid) or {}
    passed = [v for k, v in sorted(state.get("gates", {}).items(), key=lambda kv: int(kv[0])) if v["status"] == "pass"]
    if not passed:
        print(f"verify-gate: {tid} has no passing gate")
        return 1
    if passed[-1]["tree_sha"] != tree_sha(state["worktree"], state["base"]):
        print(f"verify-gate: {tid} changed after its gate passed; re-run the gate")
        return 1
    print(f"verify-gate: {tid} matches its passing gate")
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["verify"] and len(a) == 3:
        sys.exit(cmd_verify(a[1], a[2]))
    if len(a) == 3 and a[2].isdigit():
        sys.exit(cmd_gate(a[0], a[1], int(a[2])))
    print("usage: gate.sh <REQ> <T> <iteration> | verify-gate.sh <REQ> <T>", file=sys.stderr)
    sys.exit(2)
