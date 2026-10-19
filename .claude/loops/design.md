# Design loop

Follows [the lead pattern](lead-pattern.md). **Lead:** ux-designer. **Details:** `design/<screen>`
(one screen each) and `design/flow`. **Summary:** `design/summary`.

**Starts when** `product/overview` is approved. **Inputs:** the approved overview and PRDs
(`requests/<REQ>/artifacts/product/`) and the decisions in the journal.

Specific to design:
- **Triage first.** If the lead writes `.runs/<REQ>/design.json` with `"ui_required": false`, set
  `--loop design=skipped`. There's no summary and no review.
- The summary leads with what makes the product recognizable (for the todo app, "at a
  glance"). Its choices are design choices: density, color, what each row shows, navigation.
  It embeds one small key visual (for example a single row), not whole screens.
- `design.json` (screens, routes, new and reused components, data needs) is the handoff to the
  architect and the frontend developer. The lead keeps it consistent with the details.
- Tickets whose `artifacts` list a design key can't start until that key is approved.
