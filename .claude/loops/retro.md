# Retro loop

**Owner:** retro. **Goal:** the factory learns from this request, with the user approving every
lesson.

Run it when development is done, when the request is cancelled or paused for good, or early for
any ticket that took 2 or more revise rounds or 2 or more gate failures.

1. `scripts/request.sh status <REQ> --phase retro --loop retro=running`
2. Launch `retro` with the REQ and every `lessons` entry the agents returned during the run (keep
   them in `.runs/<REQ>/lessons.jsonl` as they arrive).
3. Register `retro/learnings`, then set `--loop retro=review`.
4. Revise → notes to the retro agent, which drops or rewords exactly those rows.
5. Approve → `scripts/learn.sh apply <REQ>`, which makes one commit per learnings file. Then
   `--loop retro=done --phase done`.
6. Tell the user they can share approved learnings with the template: `bin/sync-learnings`.
