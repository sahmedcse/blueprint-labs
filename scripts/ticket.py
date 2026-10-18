"""Tickets: one markdown file per ticket in tickets/, with status changes only through this script.
Called through scripts/ticket.sh.

    ticket.sh new --request REQ --title T --repo R --owner AGENT [--type feature] [--estimate M]
                  [--epic E] [--depends T-0001,T-0002] [--status backlog|ready]
    ticket.sh list [--status S] [--request REQ] [--repo R] [--json]
    ticket.sh show T-0001
    ticket.sh validate
    ticket.sh move T-0001 <status> --why "<reason>" [--pr URL] [--branch B]
    ticket.sh ready-set [--request REQ] [--json]   tickets that are ready with every dependency done
    ticket.sh breakdown render <REQ>   .runs/<REQ>/breakdown.json → artifacts/product/breakdown.html
    ticket.sh breakdown import <REQ>   create the approved breakdown's tickets in one commit

Moves follow MOVES below. Each move logs to the ticket, the journal and one commit. When a ticket
reaches done, backlog tickets whose dependencies are now all done are promoted to ready in the
same commit.

Exit codes: 0 ok, 1 refused (an illegal move or an invalid ticket set), 2 bad arguments.
"""
import argparse
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts", "lib"))
import trail  # noqa: E402

TICKETS = os.path.join(ROOT, "tickets")
STATUSES = ["backlog", "ready", "in_progress", "in_review", "blocked", "done", "dropped"]
TYPES = ["feature", "data", "infra", "design", "spike", "chore", "bug"]
ESTIMATES = ["S", "M", "L"]
FIELDS = ["id", "title", "request", "epic", "type", "repo", "owner_agent", "depends_on", "estimate",
          "status", "branch", "pr", "artifacts", "created", "updated"]
LISTS = {"depends_on", "artifacts"}
MOVES = {
    "backlog": {"ready", "blocked", "dropped"},
    "ready": {"in_progress", "backlog", "blocked", "dropped"},
    "in_progress": {"in_review", "ready", "blocked"},
    "in_review": {"done", "in_progress", "blocked"},
    "blocked": {"backlog", "ready", "in_progress", "dropped"},
    "done": set(),
    "dropped": set(),
}
ID_RE = re.compile(r"^T-\d{4}$")


def die(msg, code=2):
    print(f"ticket: {msg}", file=sys.stderr)
    sys.exit(code)


def slugify(s, n=40):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")[:n].strip("-") or "ticket"


# ---- file format: a small, strict frontmatter subset (no YAML dependency) ----------------------

def parse(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise ValueError(f"{path}: missing frontmatter")
    meta = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        k, v = k.strip(), v.strip()
        if k in LISTS:
            meta[k] = [x.strip() for x in v.strip("[]").split(",") if x.strip()]
        else:
            meta[k] = json.loads(v) if v.startswith('"') else (v or None)
    meta["_body"] = m.group(2)
    meta["_path"] = path
    return meta


def dump(t):
    lines = ["---"]
    for k in FIELDS:
        v = t.get(k)
        if k in LISTS:
            lines.append(f"{k}: [{', '.join(v or [])}]")
        elif k == "title":
            lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
        else:
            lines.append(f"{k}: {v if v is not None else ''}".rstrip())
    lines.append("---")
    return "\n".join(lines) + "\n" + t["_body"]


def write(t):
    with open(t["_path"], "w", encoding="utf-8") as f:
        f.write(dump(t))


def load_all():
    if not os.path.isdir(TICKETS):
        return {}
    out = {}
    for name in sorted(os.listdir(TICKETS)):
        if re.match(r"^T-\d{4}-.*\.md$", name):
            t = parse(os.path.join(TICKETS, name))
            out[t["id"]] = t
    return out


def get(tickets, tid):
    if tid not in tickets:
        die(f"no ticket {tid}")
    return tickets[tid]


def next_id(tickets):
    n = max([int(i[2:]) for i in tickets] or [0])
    return f"T-{n + 1:04d}"


def repo_names():
    try:
        return {r["name"] for r in json.load(open(os.path.join(ROOT, "repos.json")))["repos"]}
    except (FileNotFoundError, KeyError, ValueError):
        return set()


def body(story="", acceptance=(), created_note="created"):
    ac = "\n".join(f"- [ ] {a}" for a in acceptance) or "- [ ] (to be written)"
    return (f"\n## Story\n\n{story or '(to be written)'}\n\n## Acceptance criteria\n\n{ac}\n\n"
            f"## Notes\n\n## Log\n\n- {trail.now()} · {created_note}\n")


def create(tickets, *, request, title, repo, owner, type_="feature", estimate="M", epic=None,
           depends=(), status="backlog", story="", acceptance=(), artifacts=(), note="created"):
    tid = next_id(tickets)
    t = {"id": tid, "title": title, "request": request, "epic": epic, "type": type_, "repo": repo,
         "owner_agent": owner, "depends_on": list(depends), "estimate": estimate, "status": status,
         "branch": None, "pr": None, "artifacts": list(artifacts), "created": trail.now()[:10],
         "updated": trail.now()[:10],
         "_path": os.path.join(TICKETS, f"{tid}-{slugify(title)}.md"),
         "_body": body(story, acceptance, f"{note} ({status})")}
    tickets[tid] = t
    return t


def problems(tickets):
    out, repos = [], repo_names()
    for tid, t in tickets.items():
        if not ID_RE.match(tid or ""):
            out.append(f"{t['_path']}: bad id {tid!r}")
        if t.get("status") not in STATUSES:
            out.append(f"{tid}: bad status {t.get('status')!r}")
        if t.get("type") not in TYPES:
            out.append(f"{tid}: bad type {t.get('type')!r}")
        if t.get("estimate") not in ESTIMATES:
            out.append(f"{tid}: bad estimate {t.get('estimate')!r}")
        if not t.get("title") or not t.get("request") or not t.get("owner_agent"):
            out.append(f"{tid}: title, request and owner_agent are required")
        if repos and t.get("repo") not in repos and t.get("type") not in ("design", "spike"):
            out.append(f"{tid}: repo {t.get('repo')!r} is not in repos.json")
        for d in t.get("depends_on") or []:
            if d not in tickets:
                out.append(f"{tid}: depends on unknown {d}")
    # cycles
    seen, stack = set(), set()

    def visit(tid):
        if tid in stack:
            out.append(f"dependency cycle through {tid}")
            return
        if tid in seen or tid not in tickets:
            return
        stack.add(tid)
        for d in tickets[tid].get("depends_on") or []:
            visit(d)
        stack.discard(tid)
        seen.add(tid)

    for tid in tickets:
        visit(tid)
    return out


def public(t):
    return {k: t.get(k) for k in FIELDS}


# ---- commands ----------------------------------------------------------------------------------

def cmd_new(a):
    tickets = load_all()
    if a.status not in ("backlog", "ready"):
        die("new tickets start as backlog or ready")
    deps = [d for d in (a.depends or "").split(",") if d]
    t = create(tickets, request=a.request, title=a.title, repo=a.repo, owner=a.owner, type_=a.type,
               estimate=a.estimate, epic=a.epic, depends=deps, status=a.status)
    errs = problems(tickets)
    if errs:
        die("; ".join(errs), 1)
    os.makedirs(TICKETS, exist_ok=True)
    write(t)
    j = trail.journal(ROOT, "ticket", t["id"], f"created ({t['status']}): {t['title']}")
    trail.commit(ROOT, [t["_path"], j], f"ticket({t['id']}): create {t['title']}")
    print(t["id"])


def cmd_list(a):
    rows = [t for t in load_all().values()
            if (not a.status or t["status"] == a.status) and (not a.request or t["request"] == a.request)
            and (not a.repo or t["repo"] == a.repo)]
    if a.json:
        print(json.dumps([public(t) for t in rows], indent=2))
        return
    for t in rows:
        deps = f" after {','.join(t['depends_on'])}" if t["depends_on"] else ""
        print(f"{t['id']}\t{t['status']}\t{t['repo'] or '-'}\t{t['owner_agent']}\t{t['title']}{deps}")


def cmd_show(a):
    print(dump(get(load_all(), a.id)))


def cmd_validate(a):
    errs = problems(load_all())
    for e in errs:
        print(e)
    sys.exit(1 if errs else 0)


def log(t, line):
    t["_body"] = t["_body"].rstrip("\n") + f"\n- {trail.now()} · {line}\n"
    t["updated"] = trail.now()[:10]


def deps_done(tickets, t):
    return all(tickets.get(d, {}).get("status") == "done" for d in t.get("depends_on") or [])


def cmd_move(a):
    tickets = load_all()
    t = get(tickets, a.id)
    old, new = t["status"], a.status
    if new not in MOVES[old]:
        allowed = ", ".join(sorted(MOVES[old])) or "none (final)"
        die(f"{a.id} cannot move {old} → {new}. From {old} it can go to: {allowed}", 1)
    if new == "in_progress" and not deps_done(tickets, t):
        waiting = [d for d in t["depends_on"] if tickets[d]["status"] != "done"]
        die(f"{a.id} is waiting on {', '.join(waiting)}", 1)
    if new == "in_review" and not (a.pr or t.get("pr")):
        die(f"{a.id} needs --pr to go to in_review", 1)
    if not a.why.strip():
        die("--why is required: it becomes the trail")
    if a.pr:
        t["pr"] = a.pr
    if a.branch:
        t["branch"] = a.branch
    t["status"] = new
    log(t, f"{old} → {new}: {a.why}" + (f" ({a.pr})" if a.pr else ""))
    changed = [t]
    if new == "done":
        for o in tickets.values():
            if o["status"] == "backlog" and a.id in (o.get("depends_on") or []) and deps_done(tickets, o):
                o["status"] = "ready"
                log(o, f"backlog → ready: all dependencies done (last was {a.id})")
                changed.append(o)
    for c in changed:
        write(c)
    promoted = [c["id"] for c in changed[1:]]
    text = f"{old} → {new}: {a.why}" + (f"; promoted {', '.join(promoted)} to ready" if promoted else "")
    j = trail.journal(ROOT, "ticket", a.id, text, link=a.pr or t.get("pr"))
    msg = f"ticket({a.id}): {old} → {new} — {a.why}"
    trail.commit(ROOT, [c["_path"] for c in changed] + [j], msg[:100])
    print(f"{a.id} {old} → {new}" + (f" (promoted {', '.join(promoted)})" if promoted else ""))


def cmd_ready_set(a):
    tickets = load_all()
    rows = [t for t in tickets.values() if t["status"] == "ready" and deps_done(tickets, t)
            and (not a.request or t["request"] == a.request)]
    if a.json:
        print(json.dumps([public(t) for t in rows], indent=2))
    else:
        for t in rows:
            print(f"{t['id']}\t{t['repo'] or '-'}\t{t['owner_agent']}\t{t['title']}")


# ---- the PM's breakdown: drafted as JSON, reviewed as a page, imported once approved -------------

def breakdown_paths(req):
    run = os.path.join(ROOT, ".runs", req)
    return os.path.join(run, "breakdown.json"), os.path.join(run, "artifacts", "product", "breakdown.html")


def load_breakdown(req):
    src, _ = breakdown_paths(req)
    try:
        b = json.load(open(src, encoding="utf-8"))
    except FileNotFoundError:
        die(f"no breakdown at {os.path.relpath(src, ROOT)}")
    except ValueError as e:
        die(f"breakdown.json is not valid JSON: {e}", 1)
    errs, repos = [], repo_names()
    epics = {e.get("key") for e in b.get("epics", [])}
    refs = [t.get("ref") for t in b.get("tickets", [])]
    if not refs:
        errs.append("no tickets")
    if len(refs) != len(set(refs)):
        errs.append("ticket refs must be unique")
    for t in b.get("tickets", []):
        r = t.get("ref")
        if not t.get("title") or not t.get("owner_agent"):
            errs.append(f"{r}: title and owner_agent are required")
        if t.get("epic") not in epics:
            errs.append(f"{r}: unknown epic {t.get('epic')!r}")
        if t.get("type", "feature") not in TYPES or t.get("estimate", "M") not in ESTIMATES:
            errs.append(f"{r}: bad type or estimate")
        if repos and t.get("repo") not in repos and t.get("type") not in ("design", "spike"):
            errs.append(f"{r}: repo {t.get('repo')!r} is not in repos.json")
        if not t.get("acceptance"):
            errs.append(f"{r}: needs acceptance criteria")
        for d in t.get("depends_on", []):
            if d not in refs:
                errs.append(f"{r}: depends on unknown ref {d!r}")
    if errs:
        die("breakdown invalid: " + "; ".join(errs), 1)
    return b


def render_breakdown(b):
    e = html.escape
    tickets = b["tickets"]
    lines = ["graph LR"]
    for t in tickets:
        lines.append(f'  {t["ref"]}["{t["title"].replace(chr(34), "")}"]')
        lines += [f"  {d} --> {t['ref']}" for d in t.get("depends_on", [])]
    sections = []
    for ep in b["epics"]:
        cards = "".join(
            f'<div class="card"><div class="kicker">{e(t["ref"])} · {e(t.get("estimate", "M"))} · {e(t.get("type", "feature"))}</div>'
            f'<h3>{e(t["title"])}</h3><div><span class="tag">{e(t.get("repo") or "—")}</span>'
            f'<span class="tag">{e(t["owner_agent"])}</span></div>'
            f'<ul>{"".join(f"<li>{e(x)}</li>" for x in t["acceptance"])}</ul>'
            + (f'<div class="muted">after {e(", ".join(t["depends_on"]))}</div>' if t.get("depends_on") else "")
            + "</div>" for t in tickets if t.get("epic") == ep["key"])
        sections.append(f'<h2>{e(ep["title"])}</h2><p class="muted">{e(ep.get("goal", ""))}</p><div class="grid">{cards}</div>')
    big = [t["ref"] for t in tickets if t.get("estimate") == "L"]
    unsure = "".join(f"<li>{e(q)}</li>" for q in b.get("open_questions", []))
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ticket breakdown</title><link rel="stylesheet" href="/_review/templates/base.css"></head>
<body><div class="page">
<div class="kicker">product · {e(b["req"])} · owner product-manager</div>
<h1>Ticket breakdown</h1>
<p class="lede">{e(b.get("summary", ""))}</p>
<div class="decision"><b>Decision to approve</b>{len(tickets)} tickets in {len(b["epics"])} epics. Approving creates them; tickets with no dependencies start as ready.</div>
{"<p class=warn>Large tickets: " + e(", ".join(big)) + ". Consider splitting them.</p>" if big else ""}
<div class="diagram"><pre class="mermaid">
{e(chr(10).join(lines))}
</pre></div>
{"".join(sections)}
{f'<div class="unsure"><b>Unsure about</b><ul>{unsure}</ul></div>' if unsure else ""}
</div>
<script src="/_review/vendor/mermaid.min.js"></script>
<script>mermaid.initialize({{startOnLoad:true,theme:matchMedia('(prefers-color-scheme: dark)').matches?'dark':'neutral'}});</script>
</body></html>
"""


def cmd_breakdown(a):
    b = load_breakdown(a.req)
    if b.get("req") != a.req:
        die(f"breakdown.json says req {b.get('req')!r}, expected {a.req}", 1)
    src, page = breakdown_paths(a.req)
    if a.action == "render":
        os.makedirs(os.path.dirname(page), exist_ok=True)
        open(page, "w", encoding="utf-8").write(render_breakdown(b))
        print(os.path.relpath(page, ROOT))
        return
    tickets = load_all()
    if any(t["request"] == a.req for t in tickets.values()):
        die(f"{a.req} already has tickets; add more with `ticket.sh new`", 1)
    ref_to_id, created = {}, []
    for t in b["tickets"]:  # refs may point forward, so allocate ids first
        ref_to_id[t["ref"]] = f"T-{int(next_id(tickets)[2:]) + len(ref_to_id):04d}"
    epic_titles = {ep["key"]: ep["title"] for ep in b["epics"]}
    for t in b["tickets"]:
        deps = [ref_to_id[d] for d in t.get("depends_on", [])]
        c = create(tickets, request=a.req, title=t["title"], repo=t.get("repo"), owner=t["owner_agent"],
                   type_=t.get("type", "feature"), estimate=t.get("estimate", "M"),
                   epic=slugify(epic_titles[t["epic"]], 30), depends=deps,
                   status="backlog" if deps else "ready", story=t.get("story", ""),
                   acceptance=t["acceptance"], artifacts=t.get("artifacts", []),
                   note="created from approved breakdown")
        assert c["id"] == ref_to_id[t["ref"]]
        created.append(c)
    errs = problems(tickets)
    if errs:
        die("; ".join(errs), 1)
    os.makedirs(TICKETS, exist_ok=True)
    for c in created:
        write(c)
    kept = os.path.join(ROOT, "requests", a.req, "breakdown.json")
    os.makedirs(os.path.dirname(kept), exist_ok=True)
    with open(kept, "w", encoding="utf-8") as f:
        json.dump({**b, "ids": ref_to_id}, f, indent=2)
    ready = sum(c["status"] == "ready" for c in created)
    j = trail.journal(ROOT, "ticket", a.req, f"created {len(created)} tickets from the approved breakdown "
                      f"({created[0]['id']}–{created[-1]['id']}, {ready} ready)")
    trail.commit(ROOT, [c["_path"] for c in created] + [kept, j],
                 f"ticket({a.req}): create {len(created)} tickets from approved breakdown")
    for c in created:
        print(f"{c['id']}\t{c['status']}\t{c['title']}")


COMMANDS = {"breakdown": cmd_breakdown, "move": cmd_move, "ready-set": cmd_ready_set, "new": cmd_new, "list": cmd_list, "show": cmd_show, "validate": cmd_validate}


def parser():
    ap = argparse.ArgumentParser(prog="ticket.sh")
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new")
    n.add_argument("--request", required=True); n.add_argument("--title", required=True)
    n.add_argument("--repo"); n.add_argument("--owner", required=True)
    n.add_argument("--type", default="feature", choices=TYPES)
    n.add_argument("--estimate", default="M", choices=ESTIMATES)
    n.add_argument("--epic"); n.add_argument("--depends"); n.add_argument("--status", default="backlog")
    ls = sub.add_parser("list")
    ls.add_argument("--status", choices=STATUSES); ls.add_argument("--request"); ls.add_argument("--repo")
    ls.add_argument("--json", action="store_true")
    sub.add_parser("show").add_argument("id")
    sub.add_parser("validate")
    m = sub.add_parser("move")
    m.add_argument("id"); m.add_argument("status", choices=STATUSES)
    m.add_argument("--why", required=True); m.add_argument("--pr"); m.add_argument("--branch")
    r = sub.add_parser("ready-set")
    r.add_argument("--request"); r.add_argument("--json", action="store_true")
    b = sub.add_parser("breakdown")
    b.add_argument("action", choices=["render", "import"]); b.add_argument("req")
    return ap, sub


def main():
    ap, _ = parser()
    a = ap.parse_args()
    COMMANDS[a.cmd](a)


if __name__ == "__main__":
    main()
