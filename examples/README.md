# Examples

Real runs of the factory, kept so you can see what a request turns into. Each folder is one
project. It holds the request, the routing, every artifact you reviewed (with screenshots), each
review round's notes, the tickets, the decisions and the trail, so you can follow how the design
got where it did.

| Example | Request | Scope |
|---|---|---|
| [todo-app](todo-app/) | A to-do app: categorized tasks that are identifiable at a glance, timers and reminders, sync across devices, minimal login | Design only |

## How an example is made
1. `bin/new-project <name>` creates a throwaway control repo under `.runs/examples/` (gitignored).
2. The master runs `/blueprint` there. Agents produce artifacts, and you review them on the hub.
3. The results are copied here, a loop at a time, each as its own small PR.

## Layout of an example
```
<name>/
  README.md            the story of the run: request, routing, decisions, what changed per review round
  request.md           the request in the user's words, plus the master's routing
  screenshots/         a PNG of every approved artifact, so it reads on GitHub without the hub
  artifacts/           the approved artifacts as HTML (they render with the hub: bin/demo-style serve)
  reviews/             each review round's notes, exactly as the user wrote them
  tickets/             the tickets the breakdown produced
  decisions/           ADRs and journal.md (the trail)
  contracts/           API contracts the architect produced
  retro.md             what the factory learned from this run
```
