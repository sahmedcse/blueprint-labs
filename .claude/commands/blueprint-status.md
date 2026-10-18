---
description: Overall status of one request, or of all requests: phase, loops, tickets, reviews waiting on you, PRs and blockers.
argument-hint: "[REQ-0003]"
---

Show status for `$ARGUMENTS`. If it's empty, show all requests.

- With no argument: run `scripts/request.sh list`, then `scripts/request.sh status <REQ> --sync`
  for each request that isn't `done` or `cancelled`.
- With a REQ: run `scripts/request.sh status <REQ> --sync`, `review/review.sh list <REQ>` and
  `scripts/ticket.sh list --request <REQ>`.

`--sync` moves tickets whose PRs have merged to `done`, which promotes their dependents.

Reply in a compact form with at most about 15 lines per request: phase, loop states, a ticket
count per status, what's **waiting on the user** (reviews pending, PRs to merge, blockers), and
the hub URL from `.runs/<REQ>/review.url` if the server is up. Change nothing else.
