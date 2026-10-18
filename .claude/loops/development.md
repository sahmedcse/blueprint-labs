# Development loop

**Owners:** the ticket's `owner_agent` builds it, then spec-reviewer, quality-reviewer and (when
needed) security-reviewer review it. **Goal:** one small PR per ticket, gated by scripts, with
the ticket's status tracking it the whole way.

Ported from Profitify's `/feature` steps 5–9, but per **ticket** instead of per repo.
Shorthand: `$T` = ticket id, `$WT` = `.worktrees/<REQ>/$T`.

## 1. Pick the next wave
```
scripts/ticket.sh ready-set --request <REQ> --json
```
A ticket can start only when every key in its `artifacts` list is approved (`review/review.sh list
<REQ>`). Take up to **3** at once (`BLUEPRINT_PARALLEL` overrides this), preferring different
repos so gates don't queue behind each other.

For each one:
```
scripts/worktree.sh create <REQ> $T
scripts/ticket.sh move $T in_progress --why "worktree created" --branch <branch printed above>
```

## 2. Build, in parallel
For each ticket in the wave:
```
scripts/iter.sh next <REQ> $T
```
A non-zero exit means the iteration budget (3) is spent. Move the ticket to `blocked` with that
reason, and don't retry it.

Then `scripts/brief.sh <REQ> $T <iter>` prints the prompt. Launch every ticket's `owner_agent` with
its brief **in a single message** so they run concurrently. Append each agent's `lessons` to
`.runs/<REQ>/lessons.jsonl`.

## 3. Gate, one at a time
```
scripts/gate.sh <REQ> $T <iter>
```
Run gates **serially**. They contend for CPU and Docker. Exit codes:
- **0** passed.
- **1** failed. The iteration is used up. The next brief includes the log tail.
- **2** infra error (Docker down, port race). Run `scripts/iter.sh undo <REQ> $T` and retry once.

## 4. Review, in parallel
Only for tickets whose gate passed. Launch these reviewers in one message:
- `spec-reviewer` → `.runs/<REQ>/tickets/$T/review.iter<N>.spec.json`
- `quality-reviewer` → `.runs/<REQ>/tickets/$T/review.iter<N>.quality.json`
- `security-reviewer` → `…security.json`, when the ticket is `type: infra`, its repo is
  `terraform`, or its diff touches auth, user input, SQL or dependencies (`git -C $WT diff
  --stat origin/main`).

Then `scripts/merge-review.sh <REQ> $T <iter>`. It writes `review.iter<N>.json`, capping blocking
findings at 5 and promoting escalations and high-severity security findings. A non-zero exit
means the spec review was missing or unparseable: re-run that reviewer once, and **never** treat
it as approval.

## 5. Route
```
jq '[.findings[]|select(.severity=="blocking")]|length' .runs/<REQ>/tickets/$T/review.iter<N>.json
```
Greater than 0 → back to step 2 for that ticket (the brief carries the findings). Zero → step 6.

## 6. Open the PR
1. `scripts/verify-gate.sh <REQ> $T` fails if the tree changed after its gate passed. If so,
   re-gate.
2. `scripts/contract-check.sh` checks every repo against `contracts/`. If it reports a mismatch in
   a repo outside this ticket, **stop and ask the user**.
3. Run `git -C $WT status --porcelain`. Commit anything left with a conventional message. Don't
   squash or amend.
4. `git -C $WT push -u origin <branch>`
5. `scripts/pr-body.sh <REQ> $T > .runs/<REQ>/tickets/$T/pr.md`
6. `gh pr create --repo <owner/repo> --base main --head <branch> --title "$T: <title>" --body-file .runs/<REQ>/tickets/$T/pr.md --assignee @me`
7. `scripts/ticket.sh move $T in_review --why "PR opened" --pr <url>`

PRs open ready for review. **`gh pr merge` is denied to you.** Merging is the user's decision.

## 7. Next wave, then wait for merges
Go back to step 1 while `ready-set` has startable tickets. Dependents of an in-review ticket wait
until it merges. When nothing is startable but tickets remain, tell the user which PRs to merge,
in dependency order. `scripts/request.sh status <REQ> --sync` moves merged tickets to `done`,
which promotes their dependents. Then continue the loop. After a ticket is done, run
`scripts/worktree.sh cleanup <REQ> $T`.

The loop is `done` when every ticket of the request is `done` or `dropped`, or is `blocked` with a
reason the user has seen.
