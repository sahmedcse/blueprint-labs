# Infra loop

Follows [the lead pattern](lead-pattern.md). **Lead:** infra-engineer. **Details:**
`infra/topology`, `infra/plan`, plus one page per decision that needs its own (for example
`infra/hosting`). **Summary:** `infra/summary`.

**Starts when** `architecture/c4-containers` is approved, or immediately for an infra-only
request. **Inputs:** the approved C4 and ADRs, `plan.json` and `repos.json`.

Specific to infra:
- The summary picks the hosting runtime, the networking, the data stores, email and secrets,
  each with its cost implication, and lists the **human steps** (accounts, domains, OAuth
  clients, the first apply).
- When approved: `--loop infra=approved`, and every human step becomes a blocker until it's done:
  `scripts/request.sh status <REQ> --blocker "..."`.
- Terraform tickets are built in the development loop. **Nobody runs `terraform apply`.**
