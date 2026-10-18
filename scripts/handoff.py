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


# ---- brief -------------------------------------------------------------------------------------

def brief(req, tid, it):
    t, s = get_ticket(tid), repos.load_state(ROOT, req, tid)
    if not s:
        sys.exit(f"{tid} has no worktree; run worktree.sh create first")
    owner = t["owner_agent"]
    plan = load(os.path.join(ROOT, ".runs", req, "plan.json")) or {}
    contracts = sorted(f for f in os.listdir(os.path.join(ROOT, "contracts")) if f.endswith((".yaml", ".yml", ".json"))) \
        if os.path.isdir(os.path.join(ROOT, "contracts")) else []
    out = [f"You are the {owner}. Implement ticket {tid} ({t['title']}), iteration {it} of {s['max_iterations']}.", "",
           "## Read first",
           "- principles/PRINCIPLES.md and principles/DEVELOPER.md (binding)",
           f"- principles/learnings/{owner}.md",
           *[f"- conventions/{c}" for c in CONVENTIONS.get(s["kind"], [])],
           f"- the repo's CLAUDE.md in your worktree", "",
           "## Where you work",
           f"- worktree: {s['worktree']}",
           f"- branch: {s['branch']} (based on {s['base']})",
           f"- repo: {s['repo']} (kind {s['kind']})", "",
           "## The ticket (your spec)", "", open(t["_path"], encoding="utf-8").read().strip(), ""]
    if plan.get("tickets", {}).get(tid):
        out += ["## Architect's notes", "", plan["tickets"][tid], ""]
    if contracts:
        out += ["## Contracts (build against these exactly)", *[f"- contracts/{c}" for c in contracts], ""]
    if t.get("artifacts"):
        out += ["## Approved designs (binding)",
                *[f"- requests/{req}/artifacts/{k}.html" for k in t["artifacts"]], ""]
    if it > 1:
        prev = it - 1
        gate = load(os.path.join(tdir(req, tid), f"gate.iter{prev}.json"))
        if gate and gate["status"] == "fail":
            log = open(os.path.join(ROOT, gate["log"]), encoding="utf-8").read().splitlines()[-60:]
            out += [f"## The gate failed last iteration at `{gate['first_failed_step']}`. Log tail:", "```",
                    *log, "```", ""]
        review = load(os.path.join(tdir(req, tid), f"review.iter{prev}.json"))
        if review:
            blocking = [f for f in review["findings"] if f["severity"] == "blocking"]
            if blocking:
                out += ["## Blocking review findings to fix (verbatim)",
                        *[f"- [{f['id']}] {f.get('file', '')}:{f.get('line', '')}: {f['problem']} Fix: "
                          f"{f.get('fix') or f.get('suggestion', '')}" for f in blocking], ""]
        out += ["Fix only what is listed above, in new `fix:` commits. Don't rewrite history.", ""]
    out += ["Return the JSON shape from principles/DEVELOPER.md."]
    print("\n".join(out))


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


# ---- pr-body -----------------------------------------------------------------------------------

def pr_body(req, tid):
    t, s = get_ticket(tid), repos.load_state(ROOT, req, tid)
    body = open(t["_path"], encoding="utf-8").read().split("---", 2)[2]
    section = lambda name: body.split(f"## {name}", 1)[1].split("\n## ", 1)[0].strip() if f"## {name}" in body else ""
    gates = sorted((s or {}).get("gates", {}).items(), key=lambda kv: int(kv[0]))
    last = gates[-1] if gates else None
    review = load(os.path.join(tdir(req, tid), f"review.iter{last[0]}.json")) if last else None
    commits = repos.git(s["worktree"], "log", "--reverse", "--format=- %h %s", f"{s['base']}..HEAD").stdout.strip() if s else ""
    out = [f"**{tid}** · {t['title']} · request `{req}`", "", "## Story", "", section("Story"), "",
           "## Acceptance criteria", "", section("Acceptance criteria"), ""]
    if t.get("artifacts"):
        out += ["## Approved designs", "", *[f"- `requests/{req}/artifacts/{k}.html` in the control repo"
                                              for k in t["artifacts"]], ""]
    if t.get("depends_on"):
        out += [f"Depends on: {', '.join(t['depends_on'])}. Merge those first.", ""]
    out += ["## Verification", ""]
    if last:
        out.append(f"Gate passed at iteration {last[0]} (`.runs/{req}/tickets/{tid}/gate.iter{last[0]}.json`).")
    adv = [f for f in (review or {}).get("findings", []) if f["severity"] == "advisory"]
    if adv:
        out += ["", "### Advisory review findings", *[f"- ({f['source']}) {f.get('file', '')} {f['problem']}" for f in adv]]
    out += ["", "## Commits", "", commits or "(none)", "",
            "Merging is a human decision. Agents can't merge.", "",
            "🤖 Generated with [Claude Code](https://claude.com/claude-code)"]
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["brief"] and len(a) == 4:
        brief(a[1], a[2], int(a[3]))
    elif a[:1] == ["merge-review"] and len(a) == 4:
        sys.exit(merge_review(a[1], a[2], int(a[3])))
    elif a[:1] == ["pr-body"] and len(a) == 3:
        sys.exit(pr_body(a[1], a[2]))
    else:
        sys.exit("usage: brief.sh <REQ> <T> <N> | merge-review.sh <REQ> <T> <N> | pr-body.sh <REQ> <T>")
