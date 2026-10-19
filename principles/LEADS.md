# Leads

Every proposal loop (product, design, architecture, data model, infra) is run by a **lead**. The
user reads leads' summaries, not every artifact. They go into a detail page only when they want
depth. This file is how a lead works. It comes on top of `PRINCIPLES.md`.

## The summary is the product
- **One page per loop**: `artifacts/<loop>/summary.html`, built from `review/templates/summary.html`.
  The user approves the loop by approving this page.
- **Lead with your recommendation**, in one sentence the user could repeat to someone else.
- **Be opinionated.** For each of the 2–5 choices that matter, show 2–3 real options, their pros
  and cons, **your pick**, and one line on why. "It depends" is not a recommendation. If you
  genuinely can't choose, say what would decide it.
- **Already decided** goes in its own block, one line each, with no alternatives. Never
  re-litigate a decision the user made or an approved earlier loop made.
- **Details are links, not content.** Each detail page gets a card with one line on what it
  decides. Don't repeat the detail on the summary.
- **Risks**: the 2–3 things you'd watch, with the one you'd watch most first.
- It must pass the size check (`review.sh register` warns over 8,000 characters). If it doesn't
  fit, you're explaining instead of deciding.

## You plan the details; others write them
Subagents can't start subagents, so the master runs your detail writers in parallel from your
plan, `.runs/<REQ>/plans/<loop>.json`:
```json
{ "schema": "blueprint.lead-plan.v1", "req": "<REQ>", "loop": "<loop>", "lead": "<agent>",
  "details": [ { "key": "<loop>/<name>", "title": "...", "agent": "<agent that writes it>",
    "brief": "3-6 sentences: what this page decides, the decided choices that apply, what to leave out" } ] }
```
- Each detail is one decision and doesn't overlap any other. Say which detail owns anything
  shared between two.
- Write the summary **after** the details exist when you can (the master re-runs you to finish
  it). Otherwise write it from the plan and refresh it when the details land.
- When details already exist (a revision, or a loop converted mid-run), plan only what's
  missing or wrong, and summarize what's there.

## Revisions
- Notes on the summary come to you. If a note is really about one detail, say which. The master
  sends it to that detail's writer.
- Notes on a detail go straight to its writer. You're told so you can refresh the summary if
  the decision changed.
