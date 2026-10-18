# Loops

A loop is a standard procedure the master (`/blueprint`) runs. Each loop:

1. **Produces** artifacts with one specialist agent.
2. **Registers** each artifact: `review/review.sh register <REQ> <key> --owner <agent> --title "<t>"`.
3. **Reviews** them on the hub. `review.sh wait` returns per artifact, so many loops review at once.
4. **Revises.** The notes go verbatim to the same agent (SendMessage). It rewrites, and the
   master re-registers.
5. **Approves**, which unblocks the loops that depend on it and files the result into the trail.

| Loop | Owner | Artifacts (keys) | Starts when | Done when |
|---|---|---|---|---|
| [product](product.md) | product-manager | `product/<slice>`, `product/breakdown` | request routed | breakdown approved, tickets imported |
| [design](design.md) | ux-designer | `design/<screen>`, `design/flow` | all `product/<slice>` approved | all design approved |
| [architecture](architecture.md) | architect | `architecture/c4-containers`, `seq-*`, `adr-*` | all `product/<slice>` approved | all approved, ADRs filed |
| [data-model](data-model.md) | data-modeler | `data-model/erd-*`, `migration-plan` | all `product/<slice>` approved | all approved |
| [infra](infra.md) | infra-engineer | `infra/topology`, `infra/plan` | `architecture/c4-containers` approved | all approved |
| [development](development.md) | developers + reviewers | PRs, one per ticket | breakdown approved **and** the design loops a ticket depends on | every ticket in_review or done |
| [retro](retro.md) | retro | `retro/learnings` | development done (or the request closes) | learnings applied |

Loop states recorded with `scripts/request.sh status <REQ> --loop <name>=<state>`:
`pending → running → review → approved | skipped`, and `development` ends as `done`.
