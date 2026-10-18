"""Handoffs in the development loop: the developer's brief, the merged review and the PR body.

    brief.sh <REQ> <T> <iteration>        the prompt for the ticket's owner agent
    merge-review.sh <REQ> <T> <iteration> merge the reviewers into review.iter<N>.json
    pr-body.sh <REQ> <T>                  the pull request description (markdown)

merge-review policy (mechanical, so no model decides it):
- the spec review is mandatory. Every finding is blocking and must name criterion 1-6.
- high-severity security findings and escalated quality findings are blocking and go first.
- at most CAP (5) blocking findings survive. The rest are demoted to advisory.
- a missing quality or security review is a visible advisory placeholder, never a failure.
Exit 1 when the spec review is missing or invalid: re-run it. Never treat that as approval.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts", "lib"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import repos  # noqa: E402
import ticket  # noqa: E402

CAP = int(os.environ.get("REVIEW_BLOCKING_CAP", "5"))
CONVENTIONS = {"web": ["web.md"], "go": ["go.md", "postgres.md"], "python": ["python.md", "postgres.md"],
               "terraform": ["terraform.md"]}


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return None


def tdir(req, tid):
    return repos.ticket_dir(ROOT, req, tid)


def get_ticket(tid):
    t = ticket.load_all().get(tid)
    if not t:
        sys.exit(f"no ticket {tid}")
    return t


# ---- merge-review ------------------------------------------------------------------------------

def merge_review(req, tid, it):
    d = tdir(req, tid)
    spec = load(os.path.join(d, f"review.iter{it}.spec.json"))
    if not spec or spec.get("schema") != "blueprint.review.spec.v1" or not isinstance(spec.get("findings"), list):
        print(f"merge-review: spec review missing or invalid for {tid} iter {it}", file=sys.stderr)
        return 1
    if any(f.get("criterion") not in (1, 2, 3, 4, 5, 6) for f in spec["findings"]):
        print("merge-review: every spec finding must name criterion 1-6", file=sys.stderr)
        return 1
    qual = load(os.path.join(d, f"review.iter{it}.quality.json"))
    sec_path = os.path.join(d, f"review.iter{it}.security.json")
    sec = load(sec_path)
    first, blocking, advisory = [], [], []
    for f in (sec or {}).get("findings", []):
        (first if f.get("severity") == "high" else advisory).append({**f, "source": "security"})
    for f in (qual or {}).get("findings", []):
        (first if f.get("escalate") else advisory).append({**f, "source": "quality"})
    blocking = first + [{**f, "source": "spec"} for f in spec["findings"]]
    if qual is None:
        advisory.append({"source": "quality", "problem": "quality review missing or unparseable"})
    if os.path.exists(sec_path) and sec is None:
        advisory.append({"source": "security", "problem": "security review unparseable"})
    keep, demoted = blocking[:CAP], blocking[CAP:]
    findings = ([{**f, "severity": "blocking"} for f in keep] +
                [{**f, "severity": "advisory", "demoted": True} for f in demoted] +
                [{**f, "severity": "advisory"} for f in advisory])
    for i, f in enumerate(findings, 1):
        f["id"] = f"R{it}.{i}"
    merged = {"schema": "blueprint.review.v1", "ticket": tid, "iteration": it,
              "verdict": "changes_requested" if keep else "approved", "findings": findings}
    with open(os.path.join(d, f"review.iter{it}.json"), "w") as f:
        json.dump(merged, f, indent=2)
    print(f"{tid} iter {it}: {len(keep)} blocking, {len(findings) - len(keep)} advisory")
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["merge-review"] and len(a) == 4:
        sys.exit(merge_review(a[1], a[2], int(a[3])))
    else:
        sys.exit("usage: brief.sh <REQ> <T> <N> | merge-review.sh <REQ> <T> <N> | pr-body.sh <REQ> <T>")
