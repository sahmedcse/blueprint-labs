"""Apply an approved retro. Called through scripts/learn.sh.

    learn.sh apply <REQ> [--skip L2,L5]

Reads .runs/<REQ>/retro.json (proposals the user approved on the hub; --skip drops any they
rejected in their notes) and edits principles/ files. Each file gets one commit:
`learn(<agent>): <first proposal text>`, and each change is journaled.

Exit codes: 0 applied, 1 a proposal is invalid (nothing is written), 2 bad arguments.
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts", "lib"))
import trail  # noqa: E402


def die(msg, code=2):
    print(f"learn: {msg}", file=sys.stderr)
    sys.exit(code)


def bullet(p):
    return f"- {p['text'].strip()}\n  source: {p['source'].strip()}\n"


def apply_one(text, p):
    if p["action"] == "add":
        return text.rstrip("\n") + "\n" + bullet(p)
    old = (p.get("replaces") or "").strip()
    if not old:
        raise ValueError(f"{p['id']}: {p['action']} needs `replaces`")
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.strip() == f"- {old}" or line.strip() == old:
            end = i + 1
            while end < len(lines) and lines[end].startswith("  source:"):
                end += 1
            new = [bullet(p)] if p["action"] == "replace" else []
            return "".join(lines[:i] + new + lines[end:])
    raise ValueError(f"{p['id']}: no bullet matching {old!r} in {p['file']}")


def cmd_apply(a):
    src = os.path.join(ROOT, ".runs", a.req, "retro.json")
    try:
        retro = json.load(open(src, encoding="utf-8"))
    except FileNotFoundError:
        die(f"no retro at {os.path.relpath(src, ROOT)}")
    skip = set(filter(None, (a.skip or "").split(",")))
    by_file = {}
    for p in retro.get("proposals", []):
        if p.get("id") in skip:
            continue
        f = os.path.normpath(p.get("file", ""))
        if not f.startswith("principles" + os.sep) or not f.endswith(".md") or ".." in f.split(os.sep):
            die(f"{p.get('id')}: may only edit principles/*.md, not {f!r}", 1)
        if p.get("action") not in ("add", "replace", "remove") or not p.get("source"):
            die(f"{p.get('id')}: needs a valid action and a source", 1)
        if p["action"] != "remove" and not (p.get("text") or "").strip():
            die(f"{p.get('id')}: needs text", 1)
        by_file.setdefault(f, []).append(p)

    staged = {}
    for f, props in by_file.items():
        path = os.path.join(ROOT, f)
        if not os.path.exists(path):
            die(f"{f} does not exist", 1)
        text = open(path, encoding="utf-8").read()
        for p in props:
            try:
                text = apply_one(text, p)
            except ValueError as e:
                die(str(e), 1)
        staged[path] = (text, props)

    for path, (text, props) in staged.items():  # all valid; now write and commit per file
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        scope = os.path.splitext(os.path.basename(path))[0].lower()
        for p in props:
            j = trail.journal(ROOT, "learn", scope, f"{p['action']}: {p.get('text') or p.get('replaces')}",
                              link=p["source"])
        first = (props[0].get("text") or props[0].get("replaces") or "").strip().rstrip(".")
        more = f" (+{len(props) - 1} more)" if len(props) > 1 else ""
        trail.commit(ROOT, [path, j], f"learn({scope}): {first[:70]}{more}")
        print(f"{os.path.relpath(path, ROOT)}: {len(props)} change(s)")
    if not staged:
        print("nothing to apply")


def main():
    ap = argparse.ArgumentParser(prog="learn.sh")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("apply"); s.add_argument("req"); s.add_argument("--skip")
    a = ap.parse_args()
    cmd_apply(a)


if __name__ == "__main__":
    main()
