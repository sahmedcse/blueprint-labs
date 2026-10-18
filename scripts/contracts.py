"""Contracts and ADRs: filing approved decisions, and checking that repos build against the
current contract.

    adr.sh file <REQ> <slug>      .runs/<REQ>/adr/<slug>.md → decisions/ADR-NNNN-<slug>.md (one commit)
    adr.sh contracts <REQ>        .runs/<REQ>/contracts/* → contracts/ (one commit)
    contract-check.sh [--repo NAME=PATH]...

contracts/index.json says who is party to each contract:
    { "todos.openapi.yaml": { "producer": "acme-api", "consumers": ["acme-web"] } }
Each party records the contract version it implements in `.contracts.lock` at its root:
    { "todos.openapi.yaml": "<sha256 of the contract file>" }
Developers update that lock in the same commit as the code that implements a contract change.

contract-check compares every party's lock with the current contract. For each --repo given
(the ticket's worktree), a mismatch fails (exit 1). For other repos it prints WARN lines, which
are pending work for other tickets, not failures.
"""
import glob
import hashlib
import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts", "lib"))
import repos  # noqa: E402
import trail  # noqa: E402

CONTRACTS = os.path.join(ROOT, "contracts")


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def adr_file(req, slug):
    src = os.path.join(ROOT, ".runs", req, "adr", f"{slug}.md")
    if not os.path.exists(src):
        sys.exit(f"adr: no {os.path.relpath(src, ROOT)}")
    d = os.path.join(ROOT, "decisions")
    os.makedirs(d, exist_ok=True)
    for existing in glob.glob(os.path.join(d, f"ADR-*-{slug}.md")):
        sys.exit(f"adr: already filed as {os.path.basename(existing)}")
    n = max([int(m.group(1)) for f in os.listdir(d) if (m := re.match(r"ADR-(\d{4})-", f))] or [0]) + 1
    dst = os.path.join(d, f"ADR-{n:04d}-{slug}.md")
    text = open(src, encoding="utf-8").read()
    with open(dst, "w", encoding="utf-8") as f:
        f.write(f"<!-- status: accepted · request: {req} · filed: {trail.now()} -->\n{text}")
    title = (text.splitlines() or [slug])[0].lstrip("# ").strip() or slug
    j = trail.journal(ROOT, "decision", f"ADR-{n:04d}", f"accepted: {title}", link=req)
    trail.commit(ROOT, [dst, j], f"docs(adr): ADR-{n:04d} {title}"[:100])
    print(os.path.relpath(dst, ROOT))


def adr_contracts(req):
    src = os.path.join(ROOT, ".runs", req, "contracts")
    files = sorted(glob.glob(os.path.join(src, "*")))
    if not files:
        print("no contracts to file")
        return
    os.makedirs(CONTRACTS, exist_ok=True)
    out = []
    for f in files:
        dst = os.path.join(CONTRACTS, os.path.basename(f))
        if os.path.basename(f) == "index.json" and os.path.exists(dst):
            merged = {**json.load(open(dst)), **json.load(open(f))}  # new parties win
            with open(dst, "w") as fh:
                json.dump(merged, fh, indent=2)
        else:
            shutil.copyfile(f, dst)
        out.append(dst)
    names = ", ".join(os.path.basename(f) for f in out)
    j = trail.journal(ROOT, "decision", req, f"contracts approved: {names}")
    trail.commit(ROOT, out + [j], f"feat(contracts): approve {names} for {req}"[:100])
    print(names)


def check(overrides):
    index_path = os.path.join(CONTRACTS, "index.json")
    if not os.path.exists(index_path):
        print("contract-check: no contracts/index.json, nothing to check")
        return 0
    index = json.load(open(index_path))
    failed = 0
    for name, parties in sorted(index.items()):
        path = os.path.join(CONTRACTS, name)
        if not os.path.exists(path):
            print(f"FAIL {name}: listed in index.json but missing")
            failed += 1
            continue
        want = sha(path)
        for repo in [parties.get("producer"), *parties.get("consumers", [])]:
            if not repo:
                continue
            strict = repo in overrides
            try:
                where = overrides.get(repo) or repos.get(ROOT, repo)["abspath"]
            except KeyError:
                print(f"FAIL {name}: party {repo} is not in repos.json")
                failed += 1
                continue
            lock = os.path.join(where, ".contracts.lock")
            have = (json.load(open(lock)) if os.path.exists(lock) else {}).get(name)
            if have == want:
                print(f"ok   {name} · {repo}")
                continue
            why = "has not implemented it yet" if have is None else "implements an older version"
            print(f"{'FAIL' if strict else 'WARN'} {name} · {repo} {why}")
            failed += strict
    return 1 if failed else 0


def main(a):
    if a[:1] == ["file"] and len(a) == 3:
        return adr_file(a[1], a[2])
    if a[:1] == ["contracts"] and len(a) == 2:
        return adr_contracts(a[1])
    if a[:1] == ["check"]:
        overrides, rest = {}, a[1:]
        while rest:
            if rest[0] != "--repo" or len(rest) < 2 or "=" not in rest[1]:
                sys.exit("usage: contract-check.sh [--repo NAME=PATH]...")
            k, v = rest[1].split("=", 1)
            overrides[k] = os.path.abspath(v)
            rest = rest[2:]
        sys.exit(check(overrides))
    sys.exit("usage: adr.sh file <REQ> <slug> | adr.sh contracts <REQ> | contract-check.sh [--repo NAME=PATH]...")


if __name__ == "__main__":
    main(sys.argv[1:])
