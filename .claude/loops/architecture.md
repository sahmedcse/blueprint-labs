# Architecture loop

Follows [the lead pattern](lead-pattern.md). **Lead:** architect. **Details:**
`architecture/c4-containers`, `seq-<flow>`, `adr-<slug>`. **Summary:** `architecture/summary`.

**Starts when** `product/overview` is approved. **Inputs:** the approved overview and PRDs,
`design.json` if present, the data model if it exists yet, `repos.json` and `decisions/`.

Specific to architecture:
- The lead's summary states the repos, the language per service, the merge order, and each
  decision with the option it picked. Each ADR is a detail. The contract
  (`.runs/<REQ>/contracts/*.yaml` plus `index.json`) is linked from the summary.
- **Give data-model the same naming brief.** When data-model runs in parallel, the architect lead's
  plan names the core entities and fields first, and the master passes that list to the
  data-model lead. This stops the two from inventing different names.
- On approval of `architecture/adr-<slug>` (directly, or via the summary):
  `scripts/adr.sh file <REQ> <slug>`.
- When the whole loop is approved: `scripts/adr.sh contracts <REQ>`, then
  `--loop architecture=approved`.
- A **new repo** in an approved ADR → `bin/add-repo <name> --kind <go|python|web|terraform>`
  before development.
- If the architecture shows the breakdown is wrong, send the finding to the product lead as a
  revise of `product/breakdown`, before the import if possible.
