# Data-model loop

**Owner:** data-modeler. **Goal:** approved ERDs and a migration plan before any migration is
written.

1. `scripts/request.sh status <REQ> --loop data-model=running`
2. Launch `data-modeler` in **design mode** with the REQ, the approved overview and PRD pages, the breakdown,
   `design.json` (`data_needs`) and the architect's artifacts if they exist yet.
3. Register `data-model/erd-<context>` (one per bounded context) and `data-model/migration-plan`,
   then set `--loop data-model=review`.
4. Revise → notes to the same agent. When all are approved: `--loop data-model=approved`.
5. Migration-only tickets (`owner_agent: data-modeler`) are built in the development loop, with the
   data-modeler in implementation mode.
