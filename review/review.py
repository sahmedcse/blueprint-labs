"""Review gates for one request: you annotate artifacts in the browser, and the agent that owns
each one gets your notes back. Called through review/review.sh.

    review.sh register <REQ> <key> --owner <agent> --title "<title>"
        Register or re-register .runs/<REQ>/artifacts/<key>.html: inject the annotation layer
        and record its revision. Run it again after every revision. It prints the rev.
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
            "updated_at": trail.now(),
        })
        if not entry["owner"]:
            die("--owner is required the first time an artifact is registered")
        reviews["artifacts"][a.key] = entry
        save_json(p["reviews"], reviews)

    cfg = {"req": a.req, "artifact": a.key, "rev": rev, "title": entry["title"],
           "owner": entry["owner"], "round": entry["round"]}
    block = ("<!-- bpl:begin -->\n<script>window.BPL = %s;</script>\n"
             '<script src="/_review/annotate.js"></script>\n<!-- bpl:end -->\n') % json.dumps(cfg)
    with open(page, "w", encoding="utf-8") as f:
        f.write(html.replace("</body>", block + "</body>"))

    for w in size_warnings(html):
        print(f"WARN: {a.key} is large: {w}. Split it so each page is one decision.", file=sys.stderr)
    if was_revise:
        notify("Revision ready", f"{entry['title']} (round {entry['round']})")
    print(rev)


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


def cmd_list(a):
    reviews = load_json(paths(a.req)["reviews"], {"artifacts": {}})
    for key, e in sorted(reviews["artifacts"].items()):
        print(f"{key}\t{e['owner']}\t{e['state']}\tround {e['round']}\t{e['title']}")


def cmd_serve(a):
    os.execv(sys.executable, [sys.executable, os.path.join(ROOT, "review", "server.py"), ROOT, a.req])


def main():
    ap = argparse.ArgumentParser(prog="review.sh")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("register"); r.add_argument("req"); r.add_argument("key")
    r.add_argument("--owner"); r.add_argument("--title")
    n = sub.add_parser("notes"); n.add_argument("req"); n.add_argument("key")
    sub.add_parser("list").add_argument("req")
    sub.add_parser("serve").add_argument("req")
    a = ap.parse_args()
    if not re.match(r"^REQ-\d{4}(-[a-z0-9-]+)?$", a.req):
        die(f"bad request id {a.req!r}: expected REQ-0001-slug")
    {"register": cmd_register, "notes": cmd_notes,
     "list": cmd_list, "serve": cmd_serve}[a.cmd](a)


if __name__ == "__main__":
    main()
