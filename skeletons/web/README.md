# __NAME__

Next.js web app (App Router, TypeScript, Tailwind v4, shadcn/ui).

## Setup

```sh
pnpm install
cp .env.example .env.local   # set NEXT_PUBLIC_API_URL
make hooks                   # enable the Conventional Commits hook
pnpm dev                     # http://localhost:3000
```

## Scripts

| Command | What it does |
|---|---|
| `pnpm dev` | Dev server. |
| `pnpm build` | Production build. |
| `pnpm lint` | ESLint. |
| `pnpm typecheck` | `tsc --noEmit`. |
| `pnpm test` | Vitest unit tests. |
| `pnpm test:e2e` | Playwright. Run `pnpm exec playwright install chromium` once first. |
| `make gate` | Lint, typecheck, test and build, in that order. CI runs this. |

Conventions and the state rules live in [CLAUDE.md](./CLAUDE.md).
