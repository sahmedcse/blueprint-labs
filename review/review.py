"""Review gates for one request: you annotate artifacts in the browser, and the agent that owns
each one gets your notes back. Called through review/review.sh.

    review.sh register <REQ> <key> --owner <agent> --title "<title>" [--parent <key>]
        Register or re-register .runs/<REQ>/artifacts/<key>.html: inject the annotation layer
        and record its revision. Run it again after every revision. It prints the rev.
        --parent makes it a detail page of another artifact (a PRD under the product overview).
        Approving the parent approves its pending details. A detail can still be revised alone.
    review.sh withdraw <REQ> <key> --why "<reason>"   take a card off the hub (it no longer applies)
    review.sh serve <REQ>        start the loopback server (run in the background)
    review.sh wait <REQ>         block until ANY pending artifact is decided (run under Monitor)
    review.sh notes <REQ> <key>  print that artifact's notes verbatim, for its owning agent
    review.sh list <REQ>         one line per artifact: key, owner, state, round

wait prints exactly one line, then exits:
    DECISION artifact=<key> owner=<agent> decision=<approve|revise> rev=<rev> round=<n> notes=<n>   exit 0
    IDLE: no artifacts pending review                                                               exit 3
    SERVER DOWN: <why>                                                                              exit 1
It may print STALE: lines first, which mean a tab on an older revision decided. That decision is
set aside and the wait continues.

Each decision goes into the trail: a journal entry, the notes copied to
requests/<REQ>/reviews/<key>/round-<n>.json, and (on approve) the clean artifact copied to
requests/<REQ>/artifacts/<key>.html, committed together as one small commit.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts", "lib"))
import trail  # noqa: E402

KEY_RE = re.compile(r"^[a-z0-9][a-z0-9-]*(/[a-z0-9][a-z0-9-]*)*$")
LAYER_RE = re.compile(r"<!-- bpl:begin -->.*?<!-- bpl:end -->\n?", re.S)
MAX_HEADINGS, MAX_TEXT = 6, 8000  # rough proxy for "one decision, about one viewport tall"


def paths(req):
    run = os.path.join(ROOT, ".runs", req)
    return {
        "run": run,
        "artifacts": os.path.join(run, "artifacts"),
        "notes": os.path.join(run, "notes"),
        "reviews": os.path.join(run, "reviews.json"),
        "url": os.path.join(run, "review.url"),
        "archive": os.path.join(ROOT, "requests", req),
    }


def die(msg, code=2):
    print(f"review: {msg}", file=sys.stderr)
    sys.exit(code)


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def strip_layer(html):
    return LAYER_RE.sub("", html)


def notify(title, text):
    if sys.platform == "darwin" and not os.environ.get("BPL_NO_NOTIFY"):
        script = f'display notification {json.dumps(text)} with title {json.dumps(title)}'
        subprocess.run(["osascript", "-e", script], capture_output=True)


def size_warnings(html):
    body = re.sub(r"<(script|style)\b.*?</\1>", "", html, flags=re.S | re.I)
    headings = len(re.findall(r"<h2\b", body, re.I))
    text = len(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)))
    warns = []
    if headings > MAX_HEADINGS:
        warns.append(f"{headings} <h2> sections (limit {MAX_HEADINGS})")
    if text > MAX_TEXT:
        warns.append(f"{text} chars of text (limit {MAX_TEXT})")
    return warns


# ---- commands ----------------------------------------------------------------------------------

def cmd_register(a):
    p = paths(a.req)
    if not KEY_RE.match(a.key):
        die(f"bad key {a.key!r}: use lowercase words and dashes, e.g. design/checkout")
    page = os.path.join(p["artifacts"], a.key + ".html")
    if not os.path.isfile(page):
        die(f"no artifact at {os.path.relpath(page, ROOT)}")
    html = strip_layer(open(page, encoding="utf-8").read())
    if html.count("</body>") != 1:
        die(f"{a.key}.html must contain exactly one </body>")
    rev = hashlib.sha256(html.encode()).hexdigest()[:10]

    with trail.locked(p["reviews"]):
        reviews = load_json(p["reviews"], {"schema": "blueprint.reviews.v1", "req": a.req, "artifacts": {}})
        cur = reviews["artifacts"].get(a.key)
        if cur and cur["rev"] == rev and cur["state"] != "revise":
            print(rev)  # unchanged; keep its state
            return
        if cur:
            # Set the last round's notes aside so they can't decide the new round.
            old = os.path.join(p["notes"], a.key + ".json")
            if os.path.exists(old):
                os.replace(old, os.path.join(p["notes"], f"{a.key}.round-{cur['round']}.json"))
        was_revise = bool(cur and cur["state"] == "revise")
        entry = cur or {"round": 0, "history": []}
        entry.update({
            "file": f"artifacts/{a.key}.html", "title": a.title or (cur or {}).get("title") or a.key,
            "owner": a.owner or (cur or {}).get("owner"), "loop": a.key.split("/")[0],
            "rev": rev, "state": "pending", "round": entry["round"] + 1,
            "parent": a.parent or (cur or {}).get("parent"),
            "updated_at": trail.now(),
        })
        if not entry["owner"]:
            die("--owner is required the first time an artifact is registered")
        reviews["artifacts"][a.key] = entry
        save_json(p["reviews"], reviews)

    cfg = {"req": a.req, "artifact": a.key, "rev": rev, "title": entry["title"],
           "owner": entry["owner"], "round": entry["round"], "parent": entry.get("parent")}
    block = ("<!-- bpl:begin -->\n<script>window.BPL = %s;</script>\n"
             '<script src="/_review/annotate.js"></script>\n<!-- bpl:end -->\n') % json.dumps(cfg)
    with open(page, "w", encoding="utf-8") as f:
        f.write(html.replace("</body>", block + "</body>"))

    for w in size_warnings(html):
        print(f"WARN: {a.key} is large: {w}. Split it so each page is one decision.", file=sys.stderr)
    if was_revise:
        notify("Revision ready", f"{entry['title']} (round {entry['round']})")
    print(rev)


def server_up(p):
    try:
        url = open(p["url"]).read().strip()
    except FileNotFoundError:
        return False, "no review.url. Did serve start?"
    try:
        urllib.request.urlopen(url + "__reviews", timeout=2).read()
        return True, url
    except OSError as e:
        return False, f"{url} not responding ({e})"


def record(a, p, key, entry, note):
    """Write the trail for one decision: journal, notes copy, archived artifact, one commit."""
    decision, rnd = note["decision"], entry["round"]
    touched = []
    kept = os.path.join(p["archive"], "reviews", key, f"round-{rnd}.json")
    save_json(kept, {**note, "owner": entry["owner"], "round": rnd, "title": entry["title"]})
    touched.append(kept)
    if decision == "approve":
        src = os.path.join(p["artifacts"], key + ".html")
        dst = os.path.join(p["archive"], "artifacts", key + ".html")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w", encoding="utf-8") as f:
            f.write(strip_layer(open(src, encoding="utf-8").read()))
        touched.append(dst)
    texts = [n.get("text", "").strip() for n in note["notes"] if n.get("text", "").strip()]
    summary = "; ".join(f"{i + 1}) {t[:120]}" for i, t in enumerate(texts))
    verb = "approved" if decision == "approve" else f"revise ({len(texts)} notes)"
    if note.get("via"):
        verb = f"approved with {note['via']}"
    text = f"{verb}, round {rnd}" + (f": {summary}" if summary else "")
    touched.append(trail.journal(ROOT, "review", f"{a.req} {key}", text))
    trail.commit(ROOT, touched, f"review({a.req}): {key} {verb}, round {rnd}")


def cmd_wait(a):
    p = paths(a.req)
    ok, why = server_up(p)
    if not ok:
        print(f"SERVER DOWN: {why}")
        sys.exit(1)
    checks = 0
    while True:
        with trail.locked(p["reviews"]):
            reviews = load_json(p["reviews"], {"artifacts": {}})
            pending = {k: e for k, e in reviews["artifacts"].items() if e["state"] == "pending"}
            if not pending:
                print("IDLE: no artifacts pending review")
                sys.exit(3)
            for key, entry in sorted(pending.items()):
                nf = os.path.join(p["notes"], key + ".json")
                note = load_json(nf, None)
                if not note or note.get("done") is not True:
                    continue
                if note.get("rev") != entry["rev"]:
                    os.replace(nf, os.path.join(p["notes"], f"{key}.stale-{note.get('rev')}.json"))
                    print(f"STALE: {key} decision from old rev {note.get('rev')} set aside; "
                          f"current rev is {entry['rev']}", flush=True)
                    continue
                decision = note.get("decision")
                if decision not in ("approve", "revise"):
                    continue
                entry["state"] = "approved" if decision == "approve" else "revise"
                entry["history"].append({"rev": entry["rev"], "round": entry["round"],
                                         "decision": decision, "notes": len(note["notes"]),
                                         "at": trail.now()})
                cascaded = []
                if decision == "approve":
                    for ck, ce in sorted(reviews["artifacts"].items()):
                        if ce.get("parent") == key and ce["state"] == "pending":
                            ce["state"] = "approved"
                            ce["history"].append({"rev": ce["rev"], "round": ce["round"], "decision": "approve",
                                                  "via": key, "notes": 0, "at": trail.now()})
                            cascaded.append((ck, ce))
                save_json(p["reviews"], reviews)
                record(a, p, key, entry, note)
                for ck, ce in cascaded:
                    record(a, p, ck, ce, {"decision": "approve", "notes": [], "rev": ce["rev"], "via": key})
                print(f"DECISION artifact={key} owner={entry['owner']} decision={decision} "
                      f"rev={entry['rev']} round={entry['round']} notes={len(note['notes'])}"
                      + (f" also_approved={','.join(k for k, _ in cascaded)}" if cascaded else ""))
                sys.exit(0)
        time.sleep(a.interval)
        checks += 1
        if checks % 10 == 0:
            ok, why = server_up(p)
            if not ok:
                print(f"SERVER DOWN: {why}")
                sys.exit(1)


def cmd_notes(a):
    p = paths(a.req)
    reviews = load_json(p["reviews"], {"artifacts": {}})
    entry = reviews["artifacts"].get(a.key) or die(f"{a.key} is not registered")
    note = load_json(os.path.join(p["notes"], a.key + ".json"), {"notes": []})
    print(f"Review notes for {a.key} ({entry['title']}), round {entry['round']}, rev {entry['rev']}.")
    print("They are quoted exactly as the user wrote them. Each note is pinned to an element of the page.")
    print()
    for i, n in enumerate(note.get("notes", []), 1):
        target = f' on "{n["target"]}"' if n.get("target") else ""
        print(f"{i}. [{n.get('label', 'page')}]{target}: {n.get('text', '').strip() or '(no text)'}")
    if not note.get("notes"):
        print("(no notes)")


def cmd_withdraw(a):
    p = paths(a.req)
    with trail.locked(p["reviews"]):
        reviews = load_json(p["reviews"], {"artifacts": {}})
        entry = reviews["artifacts"].get(a.key) or die(f"{a.key} is not registered")
        entry["state"] = "withdrawn"
        entry["history"].append({"rev": entry["rev"], "round": entry["round"], "decision": "withdraw",
                                 "why": a.why, "at": trail.now()})
        save_json(p["reviews"], reviews)
    j = trail.journal(ROOT, "review", f"{a.req} {a.key}", f"withdrawn: {a.why}")
    trail.commit(ROOT, [j], f"review({a.req}): withdraw {a.key}")
    print(f"{a.key} withdrawn")


def cmd_list(a):
    reviews = load_json(paths(a.req)["reviews"], {"artifacts": {}})
    for key, e in sorted(reviews["artifacts"].items()):
        parent = f"\tunder {e['parent']}" if e.get("parent") else ""
        print(f"{key}\t{e['owner']}\t{e['state']}\tround {e['round']}\t{e['title']}{parent}")


def cmd_serve(a):
    os.execv(sys.executable, [sys.executable, os.path.join(ROOT, "review", "server.py"), ROOT, a.req])


def main():
    ap = argparse.ArgumentParser(prog="review.sh")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("register"); r.add_argument("req"); r.add_argument("key")
    r.add_argument("--owner"); r.add_argument("--title"); r.add_argument("--parent")
    wd = sub.add_parser("withdraw"); wd.add_argument("req"); wd.add_argument("key"); wd.add_argument("--why", required=True)
    w = sub.add_parser("wait"); w.add_argument("req"); w.add_argument("--interval", type=float, default=1.0)
    n = sub.add_parser("notes"); n.add_argument("req"); n.add_argument("key")
    sub.add_parser("list").add_argument("req")
    sub.add_parser("serve").add_argument("req")
    a = ap.parse_args()
    if not re.match(r"^REQ-\d{4}(-[a-z0-9-]+)?$", a.req):
        die(f"bad request id {a.req!r}: expected REQ-0001-slug")
    {"register": cmd_register, "wait": cmd_wait, "notes": cmd_notes, "withdraw": cmd_withdraw,
     "list": cmd_list, "serve": cmd_serve}[a.cmd](a)


if __name__ == "__main__":
    main()
