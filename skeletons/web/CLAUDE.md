# __NAME__

The web app for this project. It is a product repo of a blueprint-labs control repo, checked out
inside it as a sibling of `conventions/`, `tickets/` and `contracts/`. Work arrives as tickets
from the control repo. Change only what your ticket asks.

**Binding rules**: `../conventions/web.md` in the control repo. If this file and that one
disagree, that one wins. Also read `AGENTS.md` here (Next.js version notes; `next dev` keeps it
current, so commit it when it changes).

## Stack

Next.js (App Router), React, TypeScript `strict`, Tailwind v4, shadcn/ui, lucide-react, pnpm.
TanStack Query, Zustand, react-hook-form + zod. Vitest + Testing Library, Playwright.

## Layout

| Path | What goes there |
|---|---|
| `src/app/` | Routes. Server components by default; `"use client"` only where needed. `providers.tsx` mounts the QueryClient. |
| `src/components/ui/` | shadcn primitives. Generated with `pnpm dlx shadcn@latest add <name>`. Don't hand-edit. |
| `src/components/` | Shared components. |
| `src/features/<f>/` | Feature folders: `components/`, hooks, `api.ts`. `features/health` and `features/waitlist` are examples. |
| `src/lib/api-client.ts` | The **only** place `fetch` is called. Base URL from `NEXT_PUBLIC_API_URL`. |
| `src/lib/query-keys.ts` | Every TanStack Query key. |
| `src/stores/<feature>.ts` | Zustand stores, one per feature. |
| `src/types/api.ts` | Generated from the control repo's `contracts/` OpenAPI. Never hand-written. |
| `e2e/` | Playwright specs, one happy path per screen. |

## State, in brief

- **Server data** goes in TanStack Query only. Never copy it into Zustand or `useState`.
- **Shared client UI state** goes in a small, serializable Zustand store.
- **Forms** use react-hook-form with a zod schema as the single source of validation and types.
- **Local state** that nothing else reads uses `useState`.
- **Bookmarkable state** (filters, tabs, pagination) lives in search params.
- Use theme tokens through Tailwind (`bg-primary`, `text-muted-foreground`). No raw hex.

## The gate

```sh
pnpm install
make gate          # lint, typecheck, test, build, in that order
```

The exit code of `make gate` is the verdict, not anyone's summary. Never skip a test, disable a
lint rule or add `@ts-ignore` to get green. E2E is separate: `pnpm exec playwright install
chromium` once, then `pnpm test:e2e`.

## Commits

- Small and single-purpose: one logical change, about 200 changed lines at most. A behavior and
  its test go in the same commit. Lockfile bumps and generated shadcn files get their own commit.
- Conventional Commits (`feat(scope): subject`). Run `make hooks` once so `.githooks/commit-msg`
  enforces it.
- Never amend, squash, force-push or use `--no-verify`. Merging is a human decision.
