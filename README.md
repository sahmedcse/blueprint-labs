# blueprint-labs

A software factory template for Claude Code. Copy it into a new project, then ask for work with
`/blueprint "<request>"`. A master agent turns the request into tickets and design artifacts that
you review in the browser, then builds them across separate product repos with small, reviewable PRs.

```
bin/new-project acme --web --api go --infra     # control repo + acme-web, acme-api, acme-infra
cd ~/Personal/acme && claude
/blueprint "users can sign up and keep a todo list"
```

See `CLAUDE.md` for how it works.
