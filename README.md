# blueprint-labs

A software factory template for Claude Code. You describe what you want. A master agent turns it
into small tickets and **visual design pages you annotate in the browser**, then builds the
approved tickets as small, reviewable PRs across separate product repos. Every decision is kept in
a trail you can read later, and the agents learn from your feedback through approved retros.

```
bin/demo                                           # try the review hub with sample data, no agents
bin/new-project acme --web --api go --infra        # control repo + acme-web, acme-api, acme-infra
cd ~/Personal/acme && claude
/blueprint "people can sign up and keep a todo list"
/blueprint-status
```

## The loop
1. **Terminal**: `/blueprint` opens a request and routes it through the standard loops: product →
   design ∥ architecture ∥ data-model → infra → development → retro.
2. **Browser**: the hub (one local page per request) shows every artifact as a card, plus the
   ticket board and the timeline. Open a card, pin notes, press **Send notes** or **Approve**.
3. **Terminal**: the master picks up each decision as it happens. It sends your notes verbatim to
   the agent that owns that page while you review the next one. Reviews are small and run in
   parallel.

## What's in here
- `.claude/commands/blueprint.md`: the master. `.claude/loops/`: the standard loops.
  `.claude/agents/`: the PM, UX designer, architect, data modeler, infra engineer, backend and
  frontend developers, three reviewers, and the retro agent.
- `principles/`: rules every agent reads, plus per-agent learnings that grow through retros.
- `review/`: the loopback review server, the hub, the pin-notes layer and the artifact templates.
- `scripts/`: tickets, requests, gates, reviews and contracts. Scripts, not models, decide
  pass/fail.
- `skeletons/`: baseline web (Next.js + TanStack Query + Zustand), Go, Python (FastAPI) and
  Terraform repos.
- `conventions/`: the binding stack rules.

See `CLAUDE.md` for the details.
