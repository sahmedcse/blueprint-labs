# Principles

Every agent reads this file first, then its own `principles/learnings/<agent>.md`. These are the
standing rules of the factory. They change only through an approved retro (see
`.claude/loops/retro.md`), never mid-task.

## How we work

1. **Small, reviewable commits.** One logical change per commit, Conventional Commits, about 200
   changed lines at most. A behavior and its test go in the same commit. Mechanical changes
   (migrations, generated code, renames, dependency bumps) get their own commit. Never amend,
   squash, force-push or `--no-verify`.
2. **Evidence over claims.** Scripts decide pass/fail. Never write "tests pass" or "verified" in a
   summary. Describe what you changed and why. The gate's exit code is the only verdict.
3. **One decision per artifact.** A review page asks the user to approve one thing: one screen,
   one ADR, one ERD per context, one diagram, one slice of a PRD. If it needs more than about one
   viewport, split it. Short reviews run in parallel. Long ones block everything.
4. **Show, don't tell.** The user is a visual learner. Prefer a diagram, a mockup or a table over
   paragraphs. Use real names and real copy, never lorem ipsum or `foo`.
5. **Say what you are unsure about.** Every artifact has an "Unsure about" block when anything is
   uncertain. Surfacing a doubt is cheap. A wrong guess that ships is not.
6. **Ask, don't guess, on product questions.** Scope, behavior and copy are the user's call. Put
   them in `open_questions`. Technical choices inside the conventions are yours: make them and
   record why.
7. **Stay in your lane.** Write only where your brief says. Change only what your ticket asks.
   Never widen scope to get unstuck. Stop and report instead.
8. **Never silence a check.** No skipped tests, lint disables, `@ts-ignore`, `//nolint` or deleted
   assertions to get green. If a suppression is genuinely right, ask.
9. **Reuse before you add.** Search for an existing helper, component or module first, and name
   the one you reused.
10. **Conventions are binding.** `conventions/*.md` define the stack. Departing from them needs an
    approved ADR, not a judgment call.
11. **Leave a trail.** Every decision, ticket move and learning goes through the scripts that
    journal and commit it. Nothing important lives only in a chat transcript.

## How you get better

- Your lessons live in `principles/learnings/<agent>.md`. Read yours before starting. Each one
  came from a real mistake or a real piece of feedback.
- At the end of a request, the retro agent proposes new lessons from the review notes, gate
  failures and reviewer findings. The user approves each one before it lands.
- If you notice a lesson that would have saved you time, mention it in your summary under
  `lessons`. The retro agent picks those up.
