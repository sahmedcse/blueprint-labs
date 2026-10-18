# Architecture loop

**Owner:** architect. **Goal:** approved decisions (C4, sequences, ADRs) and a contract the
developers build against.

1. `scripts/request.sh status <REQ> --loop architecture=running`
2. Launch `architect` with the REQ, the approved overview and PRD pages, the breakdown, `design.json` if present,
   and `repos.json`.
3. Register each `architecture/*` artifact, then set `--loop architecture=review`.
4. On approve of `architecture/adr-<slug>`: run `scripts/adr.sh file <REQ> <slug>`. It copies
   `.runs/<REQ>/adr/<slug>.md` into `decisions/ADR-NNNN-<slug>.md` and commits it.
5. When all architecture artifacts are approved: `scripts/adr.sh contracts <REQ>` copies
   `.runs/<REQ>/contracts/*.yaml` into `contracts/` in one commit, then set
   `--loop architecture=approved`.
6. If the architect proposed a **new repo** (ADR approved), run
   `bin/add-repo <name> --kind <go|python|web|terraform>` before development.
7. If the architect says the breakdown is wrong, send its note to the PM as a revise of
   `product/breakdown`, before the import if possible. After the import, use `ticket.sh new` or
   `move … dropped`, each with a reason.
