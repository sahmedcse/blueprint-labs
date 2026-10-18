"""The project trail: journal entries plus one small commit per event.

Used by review/review.py and scripts/ticket.py so every decision, ticket move and learning lands
in decisions/journal.md and in git history the same way.

    journal(root, kind, subject, text, link=None)  append one entry to decisions/journal.md
    commit(root, paths, message)                    commit exactly `paths`, retrying on index.lock
    locked(path)                                    mkdir-based lock (macOS has no flock(1))
"""
import contextlib
import datetime as _dt
import os
import subprocess
import time

JOURNAL = os.path.join("decisions", "journal.md")
HEADER = ("# Journal\n\nThe trail of this project: every request, review decision, ticket move and\n"
          "learning, newest last. Written by scripts, never by hand.\n\n")
TRAILER = "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"


def now():
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


@contextlib.contextmanager
def locked(path, timeout=30):
    lock = path + ".lock"
    deadline = time.time() + timeout
    while True:
        try:
            os.mkdir(lock)
            break
        except FileExistsError:
            if time.time() > deadline:
                raise TimeoutError(f"lock held: {lock}")
            time.sleep(0.1)
    try:
        yield
    finally:
        os.rmdir(lock)


def journal(root, kind, subject, text, link=None):
    """Append `- <when> · **<kind>** <subject> — <text> (<link>)` and return the journal path."""
    path = os.path.join(root, JOURNAL)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = " ".join((text or "").split())
    line = f"- {now()} · **{kind}** {subject} — {text}"
    if link:
        line += f" ({link})"
    with locked(path):
        new = not os.path.exists(path)
        with open(path, "a", encoding="utf-8") as f:
            if new:
                f.write(HEADER)
            f.write(line + "\n")
    return path


def commit(root, paths, message, retries=20):
    """Commit only `paths` (relative to root). Returns True if a commit was made.

    No-op outside a git repo or when nothing in `paths` changed, so scripts work in tests and in
    a fresh copy of the template before `git init`.
    """
    if subprocess.run(["git", "-C", root, "rev-parse", "--git-dir"], capture_output=True).returncode:
        return False
    paths = [os.path.relpath(p, root) if os.path.isabs(p) else p for p in paths]
    for attempt in range(retries):
        add = subprocess.run(["git", "-C", root, "add", "--", *paths], capture_output=True, text=True)
        if add.returncode == 0:
            staged = subprocess.run(["git", "-C", root, "diff", "--cached", "--quiet", "--", *paths])
            if staged.returncode == 0:
                return False
            done = subprocess.run(["git", "-C", root, "commit", "-q", "-m", message + TRAILER, "--", *paths],
                                  capture_output=True, text=True)
            if done.returncode == 0:
                return True
            err = done.stderr
        else:
            err = add.stderr
        if "index.lock" not in err:
            raise RuntimeError(f"git commit failed: {err.strip()}")
        time.sleep(0.2 * (attempt + 1))
    raise RuntimeError("git commit failed: index.lock held too long")
