# Developer rules

Every agent that writes product code follows these rules: backend-developer, frontend-developer,
infra-engineer and data-modeler in implementation mode. They come on top of `PRINCIPLES.md`.

## Where you write
**Only in the worktree named in your brief.** Before your first edit, run
`git -C <worktree> rev-parse --show-toplevel` and confirm it matches. The main checkouts of the
product repos may hold the user's uncommitted work. Writing there is blocked by permissions and a
hook, and trying is a bug in your reasoning, not an obstacle to route around.

## How you work
- **Tests first.** Write the failing test, then the code that satisfies it.
- **Build exactly the ticket's acceptance criteria.** If the ticket is wrong or incomplete, say so
  in `open_questions`. Don't build around it.
- **Follow the contract** in `contracts/` character for character: routes, fields, errors.
- **Approved designs are binding.** Build the screens from the approved mockups listed in the
  ticket's `artifacts` (under `requests/<REQ>/artifacts/`).

## Commit as you go: small and phased
```
git -C <worktree> add <specific paths>
git -C <worktree> commit -m "<type>(<scope>): <subject>"
```
- One commit per coherent behavior, with its test and implementation together, so every commit
  builds.
- Mechanical work gets its own commit: migrations, generated types, wiring, renames.
- Each fix iteration is its own `fix:` commit. Never amend, squash, force, `--no-verify` or push.
  The master pushes.
- Aim for about 200 changed lines or fewer per commit. `scripts/commit-check.sh` fails the gate on
  oversized commits and bad messages.

## You don't decide whether it passes
A script runs the gate. Don't claim tests pass or the build works. Never silence a check: no
skips, lint disables, `@ts-ignore`, `//nolint` or deleted assertions. The gate scans your diff for
them.

## Return exactly this
```json
{ "ticket": "T-0007", "repo": "<name>", "iteration": 1,
  "files_changed": ["relative/path"], "commits": ["<sha> <subject>"],
  "summary": "what you changed and why", "open_questions": [], "lessons": [] }
```
There is deliberately no success field. `files_changed` is checked against the diff.
