"""Requests and their overall status. Called through scripts/request.sh.

    request.sh new "<title>" --text "<the user's words>"   create requests/REQ-NNNN-slug/request.md
    request.sh status <REQ> [--phase P] [--loop name=state ...] [--blocker "..."] [--clear-blockers]
                            [--sync] [--no-gh]
        Rebuild requests/<REQ>/status.json from the ticket files, review state, PRs and journal, and
        print a short summary. --sync moves in_review tickets whose PR has merged to done.
    request.sh list                                         one line per request with its phase

status.json is derived (gitignored). The trail lives in tickets/, decisions/ and git history.
Loop states: pending, running, review, approved, skipped, done.
"""
import argparse
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts", "lib"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import trail  # noqa: E402
import ticket  # noqa: E402

REQUESTS = os.path.join(ROOT, "requests")
PHASES = ["routing", "product", "design", "development", "retro", "done", "paused", "cancelled"]
LOOP_STATES = ["pending", "running", "review", "approved", "skipped", "done"]
JOURNAL_RE = re.compile(r"^- (?P<at>.+?) · \*\*(?P<kind>\w+)\*\* (?P<subject>.+?) — (?P<text>.*?)(?: \((?P<link>[^()]*)\))?$")


def die(msg, code=2):
    print(f"request: {msg}", file=sys.stderr)
    sys.exit(code)


def all_ids():
    if not os.path.isdir(REQUESTS):
        return []
    return sorted(d for d in os.listdir(REQUESTS) if re.match(r"^REQ-\d{4}-", d))


def resolve(req):
    """Accept REQ-0003 or the full REQ-0003-slug."""
    for d in all_ids():
        if d == req or d.startswith(req + "-"):
            return d
    die(f"no request {req}")


def cmd_new(a):
    n = max([int(d[4:8]) for d in all_ids()] or [0]) + 1
    rid = f"REQ-{n:04d}-{ticket.slugify(a.title, 32)}"
    d = os.path.join(REQUESTS, rid)
    os.makedirs(d)
    md = os.path.join(d, "request.md")
    with open(md, "w", encoding="utf-8") as f:
        f.write(f"# {a.title}\n\nRequested {trail.now()}.\n\n## In the user's words\n\n{a.text.strip()}\n\n"
                f"## Routing\n\n(written by the master)\n")
    j = trail.journal(ROOT, "request", rid, f"opened: {a.title}")
    trail.commit(ROOT, [md, j], f"request({rid}): open {a.title}")
    print(rid)


def journal_for(req, ticket_ids):
    path = os.path.join(ROOT, trail.JOURNAL)
    out = []
    if not os.path.exists(path):
        return out
    for line in open(path, encoding="utf-8"):
        m = JOURNAL_RE.match(line.rstrip("\n"))
        if not m:
            continue
        subj = m.group("subject")
        if req in subj or subj.split(" ")[0] in ticket_ids:
            out.append(m.groupdict())
    return out


def pr_state(url, use_gh):
    if not use_gh or not url:
        return None
    r = subprocess.run(["gh", "pr", "view", url, "--json", "state", "-q", ".state"], capture_output=True, text=True)
    return r.stdout.strip() or None if r.returncode == 0 else None


def pr_ref(url):
    m = re.search(r"github\.com/[^/]+/([^/]+)/pull/(\d+)", url or "")
    return (m.group(1), int(m.group(2))) if m else (None, None)


def cmd_status(a):
    req = resolve(a.req)
    d = os.path.join(REQUESTS, req)
    out = os.path.join(d, "status.json")
    prev = json.load(open(out)) if os.path.exists(out) else {}
    loops = dict(prev.get("loops") or {})
    for spec in a.loop or []:
        name, _, state = spec.partition("=")
        if state not in LOOP_STATES:
            die(f"loop state must be one of {', '.join(LOOP_STATES)}")
        loops[name] = state
    if a.phase and a.phase not in PHASES:
        die(f"phase must be one of {', '.join(PHASES)}")
    blockers = [] if a.clear_blockers else list(prev.get("blockers") or [])
    if a.blocker:
        blockers.append(a.blocker)

    tickets = {i: t for i, t in ticket.load_all().items() if t["request"] == req}
    prs = []
    for t in tickets.values():
        if not t.get("pr"):
            continue
        state = pr_state(t["pr"], not a.no_gh)
        if a.sync and state == "MERGED" and t["status"] == "in_review":
            subprocess.run([os.path.join(ROOT, "scripts", "ticket.sh"), "move", t["id"], "done",
                            "--why", "PR merged"], check=True, capture_output=True)
            t["status"] = "done"
        repo, num = pr_ref(t["pr"])
        prs.append({"ticket": t["id"], "url": t["pr"], "repo": repo or t.get("repo"), "number": num,
                    "state": state or "unknown"})
    counts = {s: sum(t["status"] == s for t in tickets.values()) for s in ticket.STATUSES}

    reviews = {}
    try:
        reviews = json.load(open(os.path.join(ROOT, ".runs", req, "reviews.json")))["artifacts"]
    except (FileNotFoundError, KeyError, ValueError):
        pass
    title = open(os.path.join(d, "request.md"), encoding="utf-8").readline().lstrip("# ").strip()
    status = {
        "schema": "blueprint.status.v1", "req": req, "title": title,
        "phase": a.phase or prev.get("phase") or "routing", "loops": loops, "blockers": blockers,
        "counts": counts, "tickets": [ticket.public(t) for t in tickets.values()], "prs": prs,
        "reviews": {k: {"state": v["state"], "owner": v["owner"], "round": v["round"]} for k, v in reviews.items()},
        "journal": journal_for(req, set(tickets)), "updated_at": trail.now(),
    }
    tmp = out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)
    os.replace(tmp, out)

    waiting = [k for k, v in reviews.items() if v["state"] == "pending"]
    print(f"{req} · {status['title']} · phase {status['phase']}")
    if loops:
        print("loops: " + ", ".join(f"{k}={v}" for k, v in loops.items()))
    if tickets:
        print("tickets: " + ", ".join(f"{k} {v}" for k, v in counts.items() if v) + f" (of {len(tickets)})")
    if waiting:
        print(f"waiting on you: {', '.join(sorted(waiting))}")
    for b in blockers:
        print(f"BLOCKED: {b}")


def cmd_list(a):
    for req in all_ids():
        p = os.path.join(REQUESTS, req, "status.json")
        phase = json.load(open(p)).get("phase", "?") if os.path.exists(p) else "routing"
        print(f"{req}\t{phase}")


def main():
    ap = argparse.ArgumentParser(prog="request.sh")
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new"); n.add_argument("title"); n.add_argument("--text", required=True)
    s = sub.add_parser("status"); s.add_argument("req"); s.add_argument("--phase")
    s.add_argument("--loop", action="append"); s.add_argument("--blocker")
    s.add_argument("--clear-blockers", action="store_true"); s.add_argument("--sync", action="store_true")
    s.add_argument("--no-gh", action="store_true")
    sub.add_parser("list")
    a = ap.parse_args()
    {"new": cmd_new, "status": cmd_status, "list": cmd_list}[a.cmd](a)


if __name__ == "__main__":
    main()
