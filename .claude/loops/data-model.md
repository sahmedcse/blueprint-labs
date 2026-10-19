# Data-model loop

Follows [the lead pattern](lead-pattern.md). **Lead:** data-modeler. **Details:**
`data-model/erd-<context>` (one per bounded context) and `data-model/migration-plan`.
**Summary:** `data-model/summary`.

**Starts when** `product/overview` is approved. **Inputs:** the approved overview and PRDs,
`design.json` (`data_needs`), and the architect's entity and field names if architecture runs in
parallel (see architecture.md).

Specific to the data model:
- The summary states the contexts, the constraints that enforce product rules (caps, uniqueness,
  one-per-task), how time-based work is scheduled, and the migration order, each with its pick
  and why.
- `data-model.json` is the handoff to the backend developer. The lead keeps it consistent with
  the details.
- Migration-only tickets (`owner_agent: data-modeler`) are built in the development loop, in
  implementation mode.
