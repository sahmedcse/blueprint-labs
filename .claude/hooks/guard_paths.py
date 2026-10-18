"""PreToolUse guard for Edit, Write, NotebookEdit and Bash. Exit 2 blocks the call (stderr goes to
the model), and exit 0 allows it.

1. Product repos' main checkouts (from repos.json) are read-only. They may hold the user's
   uncommitted work. Agents write in .worktrees/ instead. Edit/Write deny rules can't see shell
   redirects, so Bash commands are checked too.
2. History is never rewritten: --amend, --no-verify and force pushes are blocked in any form
   (including `git -C <path> ...`, which the settings deny rules can't match).
3. The trail is written by scripts only: tickets/, decisions/journal.md and requests/*/status.json
   are blocked for Edit/Write. Use scripts/ticket.sh, scripts/request.sh and friends.
"""
import json
import os
import re
import sys

ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def block(why, hint):
    print(f"BLOCKED: {why}\n{hint}", file=sys.stderr)
    sys.exit(2)


def main_checkouts():
    try:
        rs = json.load(open(os.path.join(ROOT, "repos.json"))).get("repos", [])
    except (FileNotFoundError, ValueError):
        return []
    return [os.path.realpath(os.path.join(ROOT, r.get("path") or r["name"])) for r in rs]


def inside(path, base):
    return path == base or path.startswith(base + os.sep)


def check_file(path):
    p = os.path.realpath(os.path.join(ROOT, path) if not os.path.isabs(path) else path)
    for repo in main_checkouts():
        if inside(p, repo):
            block(f"{path} is in a product repo's main checkout",
                  "Main checkouts are read-only to agents. Write in your ticket's worktree under .worktrees/.")
    rel = os.path.relpath(p, ROOT)
    if rel.startswith("tickets" + os.sep) or rel == os.path.join("decisions", "journal.md") or \
            re.match(r"^requests/[^/]+/status\.json$", rel):
        block(f"{rel} is part of the trail",
              "Change it through the scripts: scripts/ticket.sh move|new, scripts/request.sh status.")


def check_bash(cmd):
    if re.search(r"\bgit\b[^;&|]*\s(commit\b[^;&|]*--amend|[^;&|]*--no-verify|push\b[^;&|]*(\s-f\b|--force))", cmd):
        block("rewriting history or skipping hooks", "Make a new commit instead. Small commits are the rule.")
    for repo in main_checkouts():
        rel = re.escape(os.path.relpath(repo, ROOT))
        main = rf"(?:{re.escape(repo)}|(?<![\w./-]){rel})/"
        rules = [
            (rf">>?\s*['\"]?{main}", "shell redirect into a main checkout"),
            (rf"\btee(\s+-\S+)*\s+[^|;&]*{main}", "tee into a main checkout"),
            (rf"(^|[;&|\s])(rm|mv|cp|touch|truncate|dd|ln|install|patch|rmdir|chmod|chown)(\s+-\S+)*\s+[^;&|]*{main}",
             "filesystem mutation inside a main checkout"),
            (rf"git\s+-C\s+['\"]?(?:{re.escape(repo)}|{rel})/?['\"]?\s+(add|commit|checkout|switch|reset|clean|stash|apply|rm|mv|restore|merge|rebase|pull|push)\b",
             "mutating git command against a main checkout"),
        ]
        if re.search(r"\bsed\s+(-\S*\s+)*-i", cmd) and re.search(main, cmd):
            block("in-place sed on a main checkout", "Write in your ticket's worktree under .worktrees/.")
        for pat, why in rules:
            if re.search(pat, cmd):
                block(why, "Main checkouts hold the user's work. Write in your ticket's worktree under .worktrees/.")


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return
    tool, inp = data.get("tool_name"), data.get("tool_input") or {}
    if tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        path = inp.get("file_path") or inp.get("notebook_path")
        if path:
            check_file(path)
    elif tool == "Bash" and inp.get("command"):
        check_bash(inp["command"])


if __name__ == "__main__":
    main()
