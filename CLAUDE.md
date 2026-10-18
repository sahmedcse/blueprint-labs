# blueprint-labs control repo

This repo is the **control plane** for a project. It holds agents, loops, tickets, decisions and the
scripts that gate them. It holds **no product code**. Product repos (web, services, infra) are
separate git repos, checked out as sibling directories inside this one and gitignored here.
`repos.json` lists them. Every script reads that file, never a hardcoded repo name.

Start every piece of work with `/blueprint "<request>"`. Resume one with `/blueprint REQ-0003`.
See where things stand with `/blueprint-status`.

## How it fits together

| Path | What it is |
|---|---|
| `.claude/commands/blueprint.md` | The **master**. It routes a request to loops, fans out agents, waits on reviews, and routes feedback. |
| `.claude/loops/*.md` | The standard loops: product, design, architecture, data-model, infra, development, retro. |
| `.claude/agents/*.md` | Specialists. Each one owns its artifacts and gets its revise notes. |
| `principles/PRINCIPLES.md` | Rules every agent reads first. `principles/learnings/<agent>.md` holds lessons approved in retros. |
| `requests/REQ-*/` | One folder per request: `request.md` and `status.json` (generated, never hand-edited). |
| `tickets/T-*.md` | One file per ticket. Status changes **only** through `scripts/ticket.sh move`. |
| `decisions/` | ADRs and `journal.md`. Together they are the trail of directions taken. |
| `contracts/` | Cross-repo API contracts (OpenAPI). `scripts/contract-check.sh` enforces them. |
| `review/` | The local annotation system: a loopback server, the hub page, and the pin-notes layer. |
| `conventions/` | Binding stack rules for each kind of repo. |
| `skeletons/` | Baseline code for new product repos (`bin/add-repo`). |

## Scripts (the only way state changes)

| Script | Does |
|---|---|
| `scripts/request.sh new\|status\|list` | Opens requests and rebuilds their overall status (`--sync` closes merged tickets). |
| `scripts/ticket.sh new\|move\|list\|show\|ready-set\|validate\|breakdown` | Tickets and the PM's breakdown. Every move is logged, journaled and committed. |
| `review/review.sh register\|serve\|wait\|notes\|list` | Review pages: register an artifact, serve the hub, wait for decisions, read notes. |
| `scripts/worktree.sh`, `iter.sh`, `brief.sh`, `gate.sh`, `verify-gate.sh`, `merge-review.sh`, `pr-body.sh` | The per-ticket development loop. |
| `scripts/adr.sh`, `contract-check.sh` | File approved ADRs and contracts, and check repos against the contracts. |
| `scripts/learn.sh apply` | Apply an approved retro to `principles/`. |
| `scripts/commit-check.sh` | Small, Conventional Commits. The gate and CI run it. |
| `bin/new-project`, `add-repo`, `update-factory`, `sync-learnings`, `demo` | Project lifecycle. `bin/demo` lets you try the hub with sample data. |

`make test` runs every factory test, and `make commits` audits this repo's own history.

## The fixed stack (no alternatives without an ADR)

- **Web**: Next.js (App Router) + TypeScript strict + Tailwind + shadcn/ui. TanStack Query for
  server state, Zustand for client state, react-hook-form + zod for forms. pnpm.
- **Services**: Go (Chi, pgx, sqlc, goose) **or** Python (FastAPI, SQLAlchemy 2, Alembic, pydantic,
  uv). Each service records its choice in an ADR.
- **Data**: Postgres.
- **Infra**: Terraform only, on AWS.

## Rules that are not negotiable

- **Small, reviewable commits** in every repo, this one included. One logical change per commit,
  Conventional Commits, about 200 changed lines at most. `scripts/commit-check.sh` enforces this.
  Ticket moves, journal entries and learnings each get their own commit.
- **Scripts decide pass/fail**, not agents. An agent saying "tests pass" counts for nothing. Only
  the exit code of `scripts/gate.sh` does.
- **Merging is a human decision.** `gh pr merge` is denied to agents.
- **The review page is the conversation.** Design work is reviewed in the browser on the hub. The
  notes come back verbatim to the agent that owns the artifact.

## Command hygiene

Permission rules match commands as literally written. Run scripts from the repo root as
`scripts/<name>.sh` or `review/review.sh`. Use one command per Bash call: no `cd` first, no `&&`
chains. Use `git -C <path>` for product repos and worktrees.
