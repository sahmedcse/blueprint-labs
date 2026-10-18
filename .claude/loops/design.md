# Design loop

**Owner:** ux-designer. **Goal:** every user-visible change approved as a mockup before anyone
builds it.

1. `scripts/request.sh status <REQ> --phase design --loop design=running`
2. Launch `ux-designer` with the REQ, the approved PRD pages (`requests/<REQ>/artifacts/product/`)
   and `.runs/<REQ>/breakdown.json`.
3. If `.runs/<REQ>/design.json` has `"ui_required": false`, set `--loop design=skipped` and journal
   nothing more. Otherwise register each `design/<screen>` (and `design/flow` if present), then set
   `--loop design=review`.
4. Revise → notes to the same designer, then re-register. Approved → the screen is filed under
   `requests/<REQ>/artifacts/design/` automatically.
5. When every design artifact is approved: `--loop design=approved`. Tickets whose `artifacts`
   list a design key can't start until that key is approved.
