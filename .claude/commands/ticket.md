---
description: Work one ticket by hand through the development loop (build, gate, review, PR) outside a full /blueprint run.
argument-hint: T-0007
---

Run `.claude/loops/development.md` for exactly one ticket: `$ARGUMENTS`.

1. `scripts/ticket.sh show $ARGUMENTS`. It must be `ready` (or `in_progress` from an earlier
   attempt), with every dependency `done`. If it isn't, report why and stop.
2. Its REQ is the `request` field. Follow steps 1–6 of the development loop for this ticket
   alone, and nothing else.
3. Report the PR URL, or the reason the ticket is blocked.
