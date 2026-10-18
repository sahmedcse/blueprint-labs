# Postgres conventions

- One database per service. Services never read another service's tables; they go through its API.
- Table names are snake_case plurals. Primary keys are `id uuid default gen_random_uuid()`.
- Every table has `created_at timestamptz not null default now()` and `updated_at`.
- Money is `numeric(19,4)` or integer minor units, never float. Time is always `timestamptz`.
- Foreign keys are always declared. Index every foreign key and every column used in a WHERE.
- Migrations only go forward and each one is small. Destructive changes take two steps
  (stop using the column, then drop it in a later release).
- Migration tools: **goose** for Go services, **Alembic** for Python services.
- Tests run against an ephemeral, port-randomized container (see `scripts/gate.sh`), never a
  developer database.
