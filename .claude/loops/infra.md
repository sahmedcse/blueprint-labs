# Infra loop

**Owner:** infra-engineer. **Goal:** an approved topology and Terraform plan, with the human steps
spelled out.

1. Starts when `architecture/c4-containers` is approved, or immediately for an infra-only request.
   `scripts/request.sh status <REQ> --loop infra=running`
2. Launch `infra-engineer` in **design mode** with the REQ, the approved C4 page and `repos.json`.
3. Register `infra/topology` and `infra/plan`, then set `--loop infra=review`.
4. Revise → notes to the same agent. When both are approved: `--loop infra=approved`, and add any
   `human_steps` it returned to the request as blockers until done
   (`request.sh status <REQ> --blocker "..."`).
5. Terraform tickets are built in the development loop (`owner_agent: infra-engineer`).
   **Nobody runs `terraform apply`.**
