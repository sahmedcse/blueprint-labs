# The lead pattern

Every proposal loop runs this way: product, design, architecture, data-model and infra. The
per-loop docs only add what's specific to that loop. Leads follow `principles/LEADS.md`.

| Loop | Lead | Detail writers | Detail keys |
|---|---|---|---|
| product | product-manager | prd-writer | `product/<slice>` (the breakdown comes later, see product.md) |
| design | ux-designer | ux-designer (detail mode) | `design/<screen>`, `design/flow` |
| architecture | architect | architect (detail mode) | `architecture/c4-*`, `seq-*`, `adr-*` |
| data-model | data-modeler | data-modeler (detail mode) | `data-model/erd-*`, `migration-plan` |
| infra | infra-engineer | infra-engineer (detail mode) | `infra/topology`, `infra/plan`, ... |

Every lead's summary key is `<loop>/summary`, except product's, which is `product/overview`.

## Steps
1. **Plan.** Launch the lead in **lead mode** with the REQ, the approved inputs from earlier loops,
   and the decisions in `decisions/journal.md`. It writes `.runs/<REQ>/plans/<loop>.json` and,
   if it can, a first `artifacts/<loop>/summary.html`.
2. **Fan out.** Launch one writer per entry in the plan, **all in a single message**, each in
   **detail mode** with its brief. Record each agent id in `.runs/<REQ>/agents.json` under its
   detail key.
3. **Summarize.** When the details are back, send the lead their return summaries and open
   questions. It finishes `summary.html`, folding detail questions into its choices or its
   Unsure block.
4. **Register.** The summary first:
   `review/review.sh register <REQ> <loop>/summary --owner <lead> --title "<Loop>: summary"`.
   Then each detail as a child:
   `review/review.sh register <REQ> <loop>/<name> --owner <writer> --title "..." --parent <loop>/summary`.
   Then `scripts/request.sh status <REQ> --loop <loop>=review`.
5. **Route decisions.**
   - revise on the summary → to the lead. If it names a detail, send that part to the
     detail's writer too.
   - revise on a detail → to its writer, then tell the lead what changed.
   - approve on the summary → `review.sh wait` also approves pending details
     (`also_approved=`). The loop is approved once every detail is approved.
6. **Questions** that only the user can answer go into one batched AskUserQuestion, never one per
   agent. The answers are journaled as decisions and sent to the lead and to any affected
   writer.

Details can still be opened, annotated and revised one by one. The pattern only means the user
doesn't **have** to.
