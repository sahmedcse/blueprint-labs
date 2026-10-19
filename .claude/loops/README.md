# Loops

A loop is a standard procedure the master (`/blueprint`) runs. Every proposal loop (product,
design, architecture, data-model, infra) follows [the lead pattern](lead-pattern.md): a lead
writes an opinionated summary, detail writers run in parallel, and the user approves the summary.
They open a detail page only when they want depth. Each loop:

1. **Produces** artifacts with one specialist agent.
2. **Registers** each artifact: `review/review.sh register <REQ> <key> --owner <agent> --title "<t>"`.
3. **Reviews** them on the hub. `review.sh wait` returns per artifact, so many loops review at once.
4. **Revises.** The notes go verbatim to the same agent (SendMessage). It rewrites, and the
   master re-registers.
5. **Approves**, which unblocks the loops that depend on it and files the result into the trail.
   A card registered with `--parent` is a detail page: approving the parent approves it too,
   unless the user revised it separately.

| Loop | Owner | Artifacts (keys) | Starts when | Done when |
|---|---|---|---|---|
| [product](product.md) | product-manager (lead) + prd-writer per slice | `product/overview` with `product/<slice>` details, then `product/breakdown` | request routed | breakdown approved, tickets imported |
| [design](design.md) | ux-designer (lead and details) | `design/summary` + `design/<screen>`, `design/flow` | `product/overview` approved | all design approved |
| [architecture](architecture.md) | architect (lead and details) | `architecture/summary` + `c4-containers`, `seq-*`, `adr-*` | `product/overview` approved | all approved, ADRs filed |
| [data-model](data-model.md) | data-modeler (lead and details) | `data-model/summary` + `erd-*`, `migration-plan` | `product/overview` approved | all approved |
| [infra](infra.md) | infra-engineer (lead and details) | `infra/summary` + `topology`, `plan` | `architecture/c4-containers` approved | all approved |
| [development](development.md) | developers + reviewers | PRs, one per ticket | breakdown approved **and** the design loops a ticket depends on | every ticket in_review or done |
| [retro](retro.md) | retro | `retro/learnings` | development done (or the request closes) | learnings applied |

Loop states recorded with `scripts/request.sh status <REQ> --loop <name>=<state>`:
`pending → running → review → approved | skipped`, and `development` ends as `done`.
