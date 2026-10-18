-- Initial schema. Migrations only go forward (see conventions/postgres.md), so there is no Down.
-- Replace the notes table with your first real table; keep set_updated_at().

-- +goose Up
-- +goose StatementBegin
create function set_updated_at() returns trigger
language plpgsql as $$
begin
    new.updated_at = now();
    return new;
end;
$$;
-- +goose StatementEnd

create table notes (
    id         uuid        primary key default gen_random_uuid(),
    body       text        not null check (length(body) between 1 and 500),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index notes_created_at_idx on notes (created_at);

create trigger notes_set_updated_at
    before update on notes
    for each row execute function set_updated_at();
