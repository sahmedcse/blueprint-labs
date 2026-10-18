# Product loop

**Owner:** product-manager. **Goal:** a short PRD the user can see, and a ticket breakdown they
approve.

1. `scripts/request.sh status <REQ> --phase product --loop product=running`
2. Launch `product-manager` with the REQ id, `requests/<REQ>/request.md`, and the paths it writes
   (`.runs/<REQ>/artifacts/product/`, `.runs/<REQ>/breakdown.json`).
3. When it returns:
   - `scripts/ticket.sh breakdown render <REQ>`. A non-zero exit means the breakdown is invalid.
     Send the stderr back to the PM once.
   - Register every PRD page and the breakdown:
     `review/review.sh register <REQ> product/<slice> --owner product-manager --title "<t>"`
     `review/review.sh register <REQ> product/breakdown --owner product-manager --title "Ticket breakdown"`
   - `scripts/request.sh status <REQ> --loop product=review`
4. On review decisions:
   - revise on a PRD page or the breakdown → notes to the PM. After it rewrites, re-render the
     breakdown if it changed, then re-register.
   - **all `product/<slice>` approved** → start design, architecture and data-model in parallel
     (whichever the routing picked). Don't wait for the breakdown.
   - **`product/breakdown` approved** → `scripts/ticket.sh breakdown import <REQ>`, then
     `scripts/request.sh status <REQ> --loop product=approved`.
5. Open questions the PM raised that change scope → one AskUserQuestion, then send the answers
   back to the PM as a revise.
