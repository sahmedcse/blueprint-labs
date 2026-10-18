# Product loop

**Owners:** product-manager (lead) and prd-writer (one per slice). **Goal:** a product direction
the user approves from one page, then a ticket breakdown built on that approved direction.

The loop has two stages. The breakdown is never drafted before the direction is approved.

## Stage A: direction
1. `scripts/request.sh status <REQ> --phase product --loop product=running`
2. Launch `product-manager` in **plan mode** with the REQ id and `requests/<REQ>/request.md`. It
   writes `artifacts/product/overview.html` and `prd-plan.json`.
3. Validate: `jq -e '.slices | length > 0' .runs/<REQ>/prd-plan.json`. Register the overview:
   `review/review.sh register <REQ> product/overview --owner product-manager --title "Product overview"`
4. **Fan out the slices.** Launch one `prd-writer` per entry in `prd-plan.json`, **all in a
   single message**, each with the REQ and its slice key. Register each one as a detail of the
   overview as it returns:
   `review/review.sh register <REQ> product/<slice> --owner prd-writer --title "PRD: <title>" --parent product/overview`
   Record each writer's agent id under its slice key in `.runs/<REQ>/agents.json`, so a revise
   reaches the right writer.
5. `scripts/request.sh status <REQ> --loop product=review`. The user reads the overview. They
   open a PRD only when they want the detail.
6. On decisions:
   - revise on `product/overview` → notes to the lead PM. If it says a slice must change, send
     that part to the slice's writer, then re-register what changed.
   - revise on a `product/<slice>` → notes to that slice's writer only. Re-register it.
   - **approve on `product/overview`**: `review.sh wait` also approves every slice still pending
     (`also_approved=` in its output). Revised slices still need their own approval. Go to
     stage B once the overview and all slices are approved.
7. Questions the lead PM raised that change scope → one AskUserQuestion, batched. The answers
   go back to the lead as revise notes.

## Stage B: breakdown (only after stage A is approved)
1. Launch `product-manager` in **breakdown mode**. It reads the approved pages and every review
   note, and writes `.runs/<REQ>/breakdown.json`.
2. `scripts/ticket.sh breakdown render <REQ>`. A non-zero exit means it's invalid: send the
   stderr back once.
3. `review/review.sh register <REQ> product/breakdown --owner product-manager --title "Ticket breakdown"`
4. Revise → notes to the lead PM, then re-render and re-register.
5. Approve → `scripts/ticket.sh breakdown import <REQ>`, then
   `scripts/request.sh status <REQ> --loop product=approved`.

Design, architecture and data-model start when stage A is approved. They don't wait for the
breakdown, so they run while you review it.
