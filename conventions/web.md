# Web conventions (Next.js)

**Stack**: Next.js (App Router), React, TypeScript `strict`, Tailwind, shadcn/ui, lucide icons, pnpm.

## State: one tool per kind of state
| Kind | Tool | Rule |
|---|---|---|
| Server data (anything fetched) | **TanStack Query** | Never copy server data into Zustand or `useState`. Query keys come from `src/lib/query-keys.ts`. |
| Client UI state shared across components | **Zustand** | One store per feature in `src/stores/<feature>.ts`. Keep it small and serializable. |
| Form state | **react-hook-form + zod** | The zod schema is the single source for validation and types. |
| Local component state | `useState` | Fine when nothing else reads it. |
| URL state (filters, tabs, pagination) | search params | Anything a user would bookmark lives in the URL. |

## Layout
```
src/app/            routes (server components by default; "use client" only where needed)
src/components/ui/  shadcn primitives (generated; don't hand-edit)
src/components/     shared components
src/features/<f>/   feature folders: components, hooks, api.ts
src/lib/            api-client.ts (the only place fetch is called), query-keys.ts, utils
src/stores/         Zustand stores
src/types/api.ts    generated from contracts/ OpenAPI. Never hand-written.
```

## Rules
- All HTTP goes through `src/lib/api-client.ts`. Its types are generated from the contract.
- Use design tokens through Tailwind theme variables. No raw hex in components.
- Tests: vitest + Testing Library for units, Playwright for one happy path per screen.
- Gate: `pnpm lint && pnpm typecheck && pnpm test && pnpm build`.
