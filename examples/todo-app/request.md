# To-do application

Requested 2026-10-18 16:51 UTC.

## In the user's words

Design me a to do application. The application will let users use to track their tasks. Tasks can categorized and organized. Tasks should be easily identifiable at a glance. Tasks should all have timers and reminders with it. Users should be able to retrieve tasks from any device, keep login very basic and minimal.

## Routing

Shape: a new product. The user asked for design only, so development is skipped.

- **product**: PRD slices and a ticket breakdown. Login, tasks, categories, timers and reminders all need scoping.
- **design**: tasks must be "identifiable at a glance", so the screens are the heart of this request.
- **architecture**: sync across devices, minimal auth, and a reminder delivery mechanism are real decisions.
- **data-model**: users, tasks, categories, timers and reminders all need a schema.
- **infra**: reminders need a scheduler or worker, and multi-device needs hosting. Starts once the C4 diagram is approved.
- **development**: skipped (design-only run).
- **retro**: at the end, so the factory learns from the first real run.
